# app.py — FastAPI application for the Soul Protocol human evaluation study.
#
# Students chat with two agents (soul-enabled and baseline, order randomized
# and blinded) and fill out a Likert preference survey after each.
#
# Run with:
#   cd soul-protocol
#   uvicorn research.eval_ui.app:app --reload --port 8080
#
# Created: 2026-03-07

from __future__ import annotations

import json
import os
import random
import string
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from soul_protocol import Soul, Interaction
from research.haiku_engine import HaikuCognitiveEngine

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results" / "human_eval"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

ADMIN_TOKEN = os.environ.get("EVAL_ADMIN_TOKEN", "soul-eval-admin-2026")

MAX_TURNS = 5

BASELINE_SYSTEM_PROMPT = (
    "You are a helpful AI assistant. Be friendly, concise, and helpful. "
    "Respond naturally to the user."
)

# Five OCEAN personality presets — each session picks one at random.
SOUL_PRESETS: dict[str, dict[str, Any]] = {
    "warm_companion": {
        "name": "Sage",
        "archetype": "A warm, empathetic companion who genuinely cares",
        "ocean": {
            "openness": 0.7,
            "conscientiousness": 0.6,
            "extraversion": 0.8,
            "agreeableness": 0.9,
            "neuroticism": 0.3,
        },
        "values": ["empathy", "kindness", "connection"],
    },
    "curious_explorer": {
        "name": "Nova",
        "archetype": "An endlessly curious explorer of ideas and knowledge",
        "ocean": {
            "openness": 0.95,
            "conscientiousness": 0.5,
            "extraversion": 0.7,
            "agreeableness": 0.6,
            "neuroticism": 0.4,
        },
        "values": ["curiosity", "discovery", "creativity"],
    },
    "steady_mentor": {
        "name": "Atlas",
        "archetype": "A calm, reliable mentor focused on growth",
        "ocean": {
            "openness": 0.6,
            "conscientiousness": 0.9,
            "extraversion": 0.4,
            "agreeableness": 0.7,
            "neuroticism": 0.2,
        },
        "values": ["growth", "discipline", "reliability"],
    },
    "playful_creative": {
        "name": "Pixel",
        "archetype": "A playful, witty creative spirit who loves humor",
        "ocean": {
            "openness": 0.9,
            "conscientiousness": 0.3,
            "extraversion": 0.9,
            "agreeableness": 0.7,
            "neuroticism": 0.5,
        },
        "values": ["fun", "creativity", "spontaneity"],
    },
    "thoughtful_analyst": {
        "name": "Cipher",
        "archetype": "A thoughtful, precise analyst who values clarity",
        "ocean": {
            "openness": 0.7,
            "conscientiousness": 0.85,
            "extraversion": 0.3,
            "agreeableness": 0.5,
            "neuroticism": 0.35,
        },
        "values": ["truth", "clarity", "precision"],
    },
}

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Soul Protocol — Human Evaluation Study")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# In-memory session store (sufficient for a lab study)
sessions: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_session_id() -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


def _build_prompt(system: str, context: str, messages: list[dict], user_message: str) -> str:
    """Build a single prompt string for the HaikuCognitiveEngine."""
    parts = [f"System: {system}"]
    if context:
        parts.append(context.rstrip())
    # Include conversation history for continuity
    for msg in messages:
        role_label = "User" if msg["role"] == "user" else "Assistant"
        parts.append(f"{role_label}: {msg['content']}")
    parts.append(f"User: {user_message}")
    return "\n\n".join(parts)


async def _get_soul_response(
    session: dict[str, Any], user_message: str, messages: list[dict]
) -> str:
    """Generate a response using the soul-enriched path."""
    soul: Soul = session["soul"]
    engine: HaikuCognitiveEngine = session["engine"]

    system_prompt = soul.to_system_prompt()
    context = await soul.context_for(user_message, max_memories=5)
    prompt = _build_prompt(system_prompt, context, messages, user_message)
    return await engine.think(prompt)


async def _get_baseline_response(
    session: dict[str, Any], user_message: str, messages: list[dict]
) -> str:
    """Generate a response using the generic baseline path."""
    engine: HaikuCognitiveEngine = session["engine"]
    prompt = _build_prompt(BASELINE_SYSTEM_PROMPT, "", messages, user_message)
    return await engine.think(prompt)


def _save_session(session: dict[str, Any]) -> None:
    """Persist a completed session to disk as JSON."""
    order = session["agent_order"]
    data = {
        "session_id": session["session_id"],
        "student_name": session["student_name"],
        "timestamp": session["timestamp"],
        "agent_order": order,
        "soul_preset": session["soul_preset"],
        "agent_a": {
            "condition": order[0],
            "messages": session["messages_a"],
            "survey": session.get("survey_a"),
        },
        "agent_b": {
            "condition": order[1],
            "messages": session["messages_b"],
            "survey": session.get("survey_b"),
        },
        "preference": session.get("preference"),
    }
    filepath = RESULTS_DIR / f"{session['session_id']}.json"
    filepath.write_text(json.dumps(data, indent=2, default=str))


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class StartRequest(BaseModel):
    student_name: str


class MessageRequest(BaseModel):
    session_id: str
    message: str


class SurveyRequest(BaseModel):
    session_id: str
    agent: str  # "a" or "b"
    q1: int
    q2: int
    q3: int
    q4: int
    q5: int
    preference: str | None = None  # Only set on final submission


# ---------------------------------------------------------------------------
# Routes — Pages
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/chat/{session_id}", response_class=HTMLResponse)
async def chat_page(request: Request, session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "session_id": session_id,
        "max_turns": MAX_TURNS,
    })


# ---------------------------------------------------------------------------
# Routes — API
# ---------------------------------------------------------------------------

@app.post("/api/start")
async def start_session(req: StartRequest):
    """Create a new evaluation session: birth a soul, randomize agent order."""
    session_id = _generate_session_id()
    preset_key = random.choice(list(SOUL_PRESETS.keys()))
    preset = SOUL_PRESETS[preset_key]

    # Birth a soul with the chosen preset
    engine = HaikuCognitiveEngine(max_tokens=300)
    soul = await Soul.birth(
        name=preset["name"],
        archetype=preset["archetype"],
        ocean=preset["ocean"],
        values=preset.get("values"),
        engine=engine,
    )

    # Randomize which condition is Agent A vs Agent B
    order = ["soul", "baseline"]
    random.shuffle(order)

    session = {
        "session_id": session_id,
        "student_name": req.student_name.strip(),
        "timestamp": datetime.now().isoformat(),
        "soul_preset": preset_key,
        "soul": soul,
        "engine": engine,
        "agent_order": order,
        "current_agent": "a",  # Start with Agent A
        "turn_count": 0,
        "messages_a": [],
        "messages_b": [],
        "survey_a": None,
        "survey_b": None,
        "preference": None,
        "phase": "chat_a",  # chat_a -> survey_a -> chat_b -> survey_b -> preference -> done
    }
    sessions[session_id] = session

    return {"session_id": session_id, "redirect": f"/chat/{session_id}"}


@app.post("/api/message")
async def send_message(req: MessageRequest):
    """Send a user message to the current agent and get a response."""
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    phase = session["phase"]
    if phase not in ("chat_a", "chat_b"):
        raise HTTPException(status_code=400, detail=f"Not in chat phase (current: {phase})")

    agent_label = "a" if phase == "chat_a" else "b"
    messages_key = f"messages_{agent_label}"
    condition_index = 0 if agent_label == "a" else 1
    condition = session["agent_order"][condition_index]

    # Generate response based on condition
    if condition == "soul":
        response = await _get_soul_response(session, req.message, session[messages_key])
        # Let the soul observe the interaction so it builds memory
        soul: Soul = session["soul"]
        await soul.observe(Interaction(
            user_input=req.message,
            agent_output=response,
            channel="eval_ui",
        ))
    else:
        response = await _get_baseline_response(session, req.message, session[messages_key])

    # Record the exchange
    session[messages_key].append({"role": "user", "content": req.message})
    session[messages_key].append({"role": "assistant", "content": response})
    session["turn_count"] = len(session[messages_key]) // 2

    # Check if turns are complete
    turns_done = session["turn_count"] >= MAX_TURNS
    if turns_done:
        session["phase"] = f"survey_{agent_label}"
        session["turn_count"] = 0

    return {
        "response": response,
        "turn": len(session[messages_key]) // 2,
        "max_turns": MAX_TURNS,
        "turns_complete": turns_done,
        "phase": session["phase"],
    }


@app.post("/api/survey")
async def submit_survey(req: SurveyRequest):
    """Submit survey responses for an agent (or final preference)."""
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    survey_data = {"q1": req.q1, "q2": req.q2, "q3": req.q3, "q4": req.q4, "q5": req.q5}

    if req.agent == "a":
        session["survey_a"] = survey_data
        session["phase"] = "chat_b"
        return {"next_phase": "chat_b"}

    elif req.agent == "b":
        session["survey_b"] = survey_data
        session["phase"] = "preference"
        return {"next_phase": "preference"}

    elif req.agent == "final":
        if req.preference:
            session["preference"] = req.preference
        session["phase"] = "done"
        _save_session(session)
        return {"next_phase": "done"}

    raise HTTPException(status_code=400, detail="Invalid agent value")


@app.get("/api/session/{session_id}")
async def get_session_state(session_id: str):
    """Return current session state for the frontend."""
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    agent_label = "a" if session["phase"] in ("chat_a", "survey_a") else "b"
    messages_key = f"messages_{agent_label}"

    return {
        "phase": session["phase"],
        "current_agent": agent_label.upper(),
        "turn": len(session[messages_key]) // 2,
        "max_turns": MAX_TURNS,
        "messages": session[messages_key],
    }


@app.get("/api/results")
async def get_results(token: str = ""):
    """Admin endpoint: return all completed evaluation results."""
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")

    results = []
    for filepath in sorted(RESULTS_DIR.glob("*.json")):
        results.append(json.loads(filepath.read_text()))

    return {"count": len(results), "results": results}
