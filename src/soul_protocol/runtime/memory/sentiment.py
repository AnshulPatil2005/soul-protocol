# memory/sentiment.py — Heuristic emotion detection from text (no LLM).
# Updated: 2026-03-12 — Decoupled arousal from valence scores via AROUSAL_HINTS,
#   expanded vocabulary (~200 words), widened sadness/gratitude label map boundaries,
#   added neutral floor threshold for mild signals. Fixes joy/excitement and
#   sadness/frustration misclassification.
# Created: v0.2.0 — Implements Damasio's Somatic Marker Hypothesis.
# Word-list approach: positive/negative words, intensity modifiers.
# Returns SomaticMarker with valence, arousal, and emotion label.

from __future__ import annotations

from soul_protocol.runtime.types import SomaticMarker

# ---------------------------------------------------------------------------
# Curated word lists (~200 words total)
# ---------------------------------------------------------------------------

POSITIVE_WORDS: dict[str, float] = {
    # Joy / happiness (high valence)
    "happy": 0.8,
    "love": 0.9,
    "great": 0.7,
    "wonderful": 0.9,
    "amazing": 0.9,
    "awesome": 0.8,
    "excellent": 0.8,
    "fantastic": 0.9,
    "beautiful": 0.7,
    "brilliant": 0.8,
    "perfect": 0.9,
    "enjoy": 0.7,
    "delighted": 0.8,
    "pleased": 0.6,
    "glad": 0.6,
    "cheerful": 0.7,
    "lovely": 0.7,
    "warm": 0.5,
    "peaceful": 0.5,
    "calm": 0.4,
    "content": 0.5,
    "bliss": 0.8,
    "comfort": 0.5,
    # Gratitude
    "thanks": 0.5,
    "thank": 0.5,
    "grateful": 0.7,
    "appreciate": 0.6,
    "thankful": 0.7,
    # Excitement
    "excited": 0.8,
    "thrilled": 0.9,
    "eager": 0.7,
    "enthusiastic": 0.8,
    "pumped": 0.7,
    "stoked": 0.8,
    # Life events (high positive valence)
    "promoted": 0.9,
    "won": 0.8,
    "married": 0.8,
    "graduated": 0.8,
    "accepted": 0.7,
    "passed": 0.6,
    "best": 0.8,
    "dream": 0.7,
    "championship": 0.7,
    "celebrate": 0.8,
    "adopted": 0.6,
    "born": 0.7,
    "alive": 0.6,
    "blessed": 0.7,
    "incredible": 0.8,
    "extraordinary": 0.8,
    # Curiosity / interest (moderate valence — keeps them in curiosity zone)
    "curious": 0.35,
    "interesting": 0.35,
    "fascinated": 0.55,
    "intrigued": 0.45,
    "wonder": 0.5,
    "explore": 0.4,
    # Satisfaction
    "satisfied": 0.6,
    "accomplished": 0.7,
    "proud": 0.7,
    "success": 0.7,
    "achieved": 0.7,
    "solved": 0.6,
    "fixed": 0.5,
    "works": 0.4,
    "working": 0.3,
    "done": 0.3,
    "completed": 0.5,
    "relief": 0.6,
    "hope": 0.6,
    "trust": 0.5,
    # General positive (mild — low signal)
    "good": 0.4,
    "nice": 0.15,
    "cool": 0.35,
    "fine": 0.15,
    "okay": 0.1,
    "helpful": 0.6,
    "useful": 0.5,
    "impressive": 0.7,
    "remarkable": 0.7,
}

NEGATIVE_WORDS: dict[str, float] = {
    # Frustration / anger (high arousal)
    "frustrated": 0.7,
    "annoyed": 0.6,
    "angry": 0.8,
    "furious": 0.9,
    "irritated": 0.6,
    "mad": 0.7,
    "hate": 0.8,
    "terrible": 0.8,
    "awful": 0.8,
    "horrible": 0.8,
    "worst": 0.9,
    "infuriating": 0.8,
    "livid": 0.9,
    "outraged": 0.9,
    "resentful": 0.6,
    # Confusion
    "confused": 0.5,
    "confusing": 0.5,
    "unclear": 0.4,
    "lost": 0.5,
    "stuck": 0.5,
    "puzzled": 0.4,
    "baffled": 0.6,
    # Sadness (low arousal — grief, loss, melancholy)
    "sad": 0.6,
    "disappointed": 0.6,
    "unhappy": 0.7,
    "depressed": 0.8,
    "miserable": 0.8,
    "heartbroken": 0.9,
    "lonely": 0.6,
    "hopeless": 0.8,
    "grief": 0.8,
    "mourning": 0.7,
    "mourn": 0.7,
    "sorrow": 0.7,
    "empty": 0.5,
    "numb": 0.5,
    "crushed": 0.8,
    "devastating": 0.8,
    "betrayed": 0.8,
    "miss": 0.5,
    "regret": 0.6,
    "defeated": 0.6,
    "helpless": 0.7,
    "worthless": 0.7,
    "crying": 0.7,
    # Fear / anxiety
    "afraid": 0.6,
    "scared": 0.7,
    "worried": 0.5,
    "anxious": 0.6,
    "nervous": 0.5,
    "terrified": 0.9,
    "panic": 0.8,
    "overwhelmed": 0.7,
    # Failure / problems
    "failed": 0.6,
    "broken": 0.6,
    "error": 0.4,
    "bug": 0.4,
    "crash": 0.6,
    "wrong": 0.5,
    "bad": 0.5,
    "problem": 0.4,
    "issue": 0.3,
    "difficult": 0.4,
    "hard": 0.3,
    "struggle": 0.5,
    # General negative
    "boring": 0.4,
    "ugly": 0.5,
    "stupid": 0.6,
    "useless": 0.6,
    "waste": 0.5,
    "sucks": 0.7,
    "mess": 0.5,
    "pain": 0.6,
}

# ---------------------------------------------------------------------------
# Arousal hints — decouple arousal from valence intensity
# ---------------------------------------------------------------------------
# By default, arousal = valence score (high-intensity word → high arousal).
# But joy, gratitude, and sadness are high-intensity emotions with LOW energy.
# This dict overrides the arousal contribution for specific words so that
# "heartbroken" (high valence, low energy) lands in sadness, not frustration.

AROUSAL_HINTS: dict[str, float] = {
    # --- Low-arousal positive: joy, contentment, gratitude ---
    "happy": 0.35,
    "glad": 0.25,
    "pleased": 0.25,
    "cheerful": 0.30,
    "enjoy": 0.30,
    "delighted": 0.35,
    "beautiful": 0.25,
    "lovely": 0.25,
    "wonderful": 0.40,
    "perfect": 0.40,
    "brilliant": 0.40,
    "great": 0.35,
    "content": 0.15,
    "peaceful": 0.10,
    "calm": 0.10,
    "bliss": 0.30,
    "comfort": 0.15,
    "warm": 0.15,
    "relief": 0.20,
    "hope": 0.25,
    "trust": 0.20,
    "blessed": 0.25,
    # Gratitude (very low arousal — warm, not energetic)
    # Kept low enough that even with 1.3x intensifier, stays below joy's 0.20 floor
    "grateful": 0.12,
    "thankful": 0.12,
    "appreciate": 0.12,
    "thanks": 0.10,
    "thank": 0.10,
    # Satisfaction (moderate-low)
    "satisfied": 0.25,
    "accomplished": 0.35,
    "proud": 0.35,
    "success": 0.35,
    "achieved": 0.35,
    "solved": 0.25,
    "completed": 0.25,
    "done": 0.15,
    "fixed": 0.20,
    "works": 0.15,
    "working": 0.10,
    # Life events — moderate arousal (joyful but not frenzied)
    "married": 0.45,
    "adopted": 0.35,
    "born": 0.40,
    "graduated": 0.45,
    "accepted": 0.40,
    "passed": 0.30,
    "best": 0.40,
    "dream": 0.35,
    # Mild positive (very low arousal)
    "good": 0.15,
    "nice": 0.10,
    "cool": 0.15,
    "fine": 0.05,
    "okay": 0.05,
    # --- Low-arousal negative: sadness, grief, melancholy ---
    "sad": 0.25,
    "disappointed": 0.30,
    "unhappy": 0.30,
    "depressed": 0.35,
    "miserable": 0.35,
    "heartbroken": 0.35,
    "lonely": 0.20,
    "hopeless": 0.30,
    "grief": 0.30,
    "mourning": 0.25,
    "mourn": 0.25,
    "sorrow": 0.25,
    "empty": 0.15,
    "numb": 0.10,
    "crushed": 0.35,
    "devastating": 0.35,
    "miss": 0.15,
    "regret": 0.25,
    "defeated": 0.25,
    "helpless": 0.30,
    "worthless": 0.25,
    "crying": 0.30,
    # Curiosity (moderate arousal — engaged but not frantic)
    "curious": 0.35,
    "interesting": 0.30,
    "intrigued": 0.35,
    "wonder": 0.30,
    "explore": 0.30,
    # Confusion (moderate arousal)
    "confused": 0.40,
    "confusing": 0.40,
    "unclear": 0.30,
    "puzzled": 0.35,
    "baffled": 0.45,
}

# Intensity modifiers scale the detected valence/arousal
INTENSIFIERS: dict[str, float] = {
    "very": 1.3,
    "really": 1.3,
    "extremely": 1.5,
    "incredibly": 1.5,
    "absolutely": 1.4,
    "totally": 1.3,
    "completely": 1.3,
    "super": 1.3,
    "so": 1.2,
    "quite": 1.1,
    "pretty": 1.1,
    "fairly": 1.0,
    "most": 1.2,
}

DIMINISHERS: dict[str, float] = {
    "slightly": 0.5,
    "somewhat": 0.6,
    "a bit": 0.6,
    "barely": 0.4,
    "hardly": 0.4,
    "kind of": 0.6,
    "sort of": 0.6,
}

# Negation words flip valence
NEGATIONS: set[str] = {
    "not",
    "no",
    "never",
    "don't",
    "dont",
    "doesn't",
    "doesnt",
    "didn't",
    "didnt",
    "won't",
    "wont",
    "can't",
    "cant",
    "isn't",
    "isnt",
    "wasn't",
    "wasnt",
    "aren't",
    "arent",
    "wouldn't",
    "wouldnt",
    "shouldn't",
    "shouldnt",
    "couldn't",
    "couldnt",
}

# ---------------------------------------------------------------------------
# Emotion label mapping from (valence, arousal) quadrants
# ---------------------------------------------------------------------------
# Boundaries widened for sadness (arousal up to 0.50) and gratitude (up to 0.45)
# to accommodate high-intensity-but-low-energy emotions.

_LABEL_MAP: list[tuple[str, float, float, float, float]] = [
    # (label, min_valence, max_valence, min_arousal, max_arousal)
    ("excitement", 0.3, 1.0, 0.50, 1.0),
    ("joy", 0.3, 1.0, 0.20, 0.50),
    ("gratitude", 0.1, 1.0, 0.0, 0.20),
    ("curiosity", 0.1, 0.5, 0.2, 0.6),
    ("frustration", -1.0, -0.3, 0.50, 1.0),
    ("sadness", -1.0, -0.3, 0.0, 0.50),
    ("confusion", -0.5, -0.1, 0.2, 0.6),
]


def _classify_label(valence: float, arousal: float) -> str:
    """Map valence+arousal coordinates to an emotion label."""
    best_label = "neutral"
    best_dist = float("inf")

    for label, v_min, v_max, a_min, a_max in _LABEL_MAP:
        if v_min <= valence <= v_max and a_min <= arousal <= a_max:
            # Distance from center of the region
            v_center = (v_min + v_max) / 2
            a_center = (a_min + a_max) / 2
            dist = (valence - v_center) ** 2 + (arousal - a_center) ** 2
            if dist < best_dist:
                best_dist = dist
                best_label = label

    return best_label


def detect_sentiment(text: str) -> SomaticMarker:
    """Detect emotional sentiment from text using word-list heuristics.

    Scans for positive/negative words, applies intensity modifiers and
    negation detection. Returns a SomaticMarker with valence (-1 to 1),
    arousal (0 to 1), and an emotion label.

    Arousal is computed separately from valence using AROUSAL_HINTS so that
    high-intensity but low-energy emotions (joy, gratitude, sadness) are
    correctly distinguished from high-energy emotions (excitement, frustration).

    Args:
        text: The text to analyze.

    Returns:
        A SomaticMarker capturing the emotional tone.
    """
    words = text.lower().split()
    if not words:
        return SomaticMarker(valence=0.0, arousal=0.0, label="neutral")

    pos_scores: list[float] = []
    neg_scores: list[float] = []
    arousal_scores: list[float] = []
    intensity_modifier = 1.0

    # Check for intensifiers/diminishers that precede emotion words
    for i, word in enumerate(words):
        # Strip punctuation for matching
        clean = word.strip(".,!?;:'\"()[]{}#@")

        if clean in INTENSIFIERS:
            intensity_modifier = max(intensity_modifier, INTENSIFIERS[clean])
        elif clean in DIMINISHERS:
            intensity_modifier = min(intensity_modifier, DIMINISHERS[clean])

        # Check negation in a 3-word window before this word
        is_negated = any(
            words[j].strip(".,!?;:'\"()[]{}#@") in NEGATIONS for j in range(max(0, i - 3), i)
        )

        if clean in POSITIVE_WORDS:
            score = POSITIVE_WORDS[clean]
            arousal = AROUSAL_HINTS.get(clean, score)  # default: arousal = valence score
            if is_negated:
                neg_scores.append(score * 0.7)  # Negated positive → mild negative
                arousal_scores.append(arousal * 0.5)
            else:
                pos_scores.append(score)
                arousal_scores.append(arousal)
        elif clean in NEGATIVE_WORDS:
            score = NEGATIVE_WORDS[clean]
            arousal = AROUSAL_HINTS.get(clean, score)
            if is_negated:
                pos_scores.append(score * 0.5)  # Negated negative → mild positive
                arousal_scores.append(arousal * 0.5)
            else:
                neg_scores.append(score)
                arousal_scores.append(arousal)

    if not pos_scores and not neg_scores:
        return SomaticMarker(valence=0.0, arousal=0.0, label="neutral")

    # Aggregate scores
    avg_pos = sum(pos_scores) / len(pos_scores) if pos_scores else 0.0
    avg_neg = sum(neg_scores) / len(neg_scores) if neg_scores else 0.0

    # Valence: net positive vs negative, scaled by intensity
    raw_valence = (avg_pos - avg_neg) * intensity_modifier
    valence = max(-1.0, min(1.0, raw_valence))

    # Arousal: use arousal-specific scores (decoupled from valence intensity)
    raw_arousal = (sum(arousal_scores) / len(arousal_scores)) * intensity_modifier
    arousal = max(0.0, min(1.0, raw_arousal))

    # Neutral floor: if the emotional signal is too weak, classify as neutral.
    # Catches mild words like "nice", "fine", "okay" in short phrases.
    if abs(valence) < 0.2 and arousal < 0.15:
        return SomaticMarker(valence=round(valence, 3), arousal=round(arousal, 3), label="neutral")

    label = _classify_label(valence, arousal)

    return SomaticMarker(valence=round(valence, 3), arousal=round(arousal, 3), label=label)
