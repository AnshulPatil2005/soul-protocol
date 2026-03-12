# tests/test_demo.py — Smoke test for developer onboarding demo
# Created: 2026-03-12

import pytest
from soul_protocol.demo import run_demo


@pytest.mark.asyncio
async def test_demo_runs_without_error():
    """The onboarding demo should complete without raising."""
    await run_demo()
