# runtime/context/prompts.py — Summarization prompt templates for LCM compaction.
# Created: v0.3.0 — Templates used by the three-level compactor when a
# CognitiveEngine is available. Each template includes a [TASK:xxx] marker
# for HeuristicEngine routing compatibility.

from __future__ import annotations

SUMMARY_PROMPT = """[TASK:context_summary]
Summarize the following conversation messages into a concise prose paragraph.
Preserve all key facts, decisions, action items, and emotional tone.
Do NOT add information that isn't in the messages.

Messages:
{messages}

Write a single paragraph summary:"""

BULLETS_PROMPT = """[TASK:context_bullets]
Compress the following text into a bullet-point list.
Each bullet should capture one distinct fact, decision, or action item.
Be concise but preserve all important information. Drop filler and pleasantries.

Text:
{text}

Bullet points:"""
