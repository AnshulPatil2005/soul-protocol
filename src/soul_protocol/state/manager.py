# state/manager.py — StateManager for tracking and mutating a soul's runtime state.
# Created: 2026-02-22 — Manages mood, energy, social_battery, focus, and
# interaction-driven state changes with delta-based updates and clamping.

from __future__ import annotations

from datetime import datetime

from soul_protocol.types import Interaction, Mood, SoulState


# Default recovery rate per hour of rest (energy points)
_DEFAULT_ENERGY_REGEN_RATE: float = 10.0


class StateManager:
    """Manages the mutable runtime state of a digital soul.

    Provides delta-based updates for energy and social_battery (clamped 0-100),
    interaction-driven drain, and rest-based recovery.
    """

    def __init__(self, state: SoulState) -> None:
        self._state = state

    @property
    def current(self) -> SoulState:
        """Return the current soul state."""
        return self._state

    def update(self, **kwargs: object) -> None:
        """Update state fields.

        For ``energy`` and ``social_battery``, numeric values are treated as
        *deltas* (added to the current value) and the result is clamped to
        the 0-100 range.  All other fields are set directly.

        Examples::

            manager.update(mood=Mood.TIRED)
            manager.update(energy=-10)        # decrease by 10
            manager.update(focus="high")
            manager.update(energy=5, social_battery=-3)
        """
        for key, value in kwargs.items():
            if key == "energy" and isinstance(value, (int, float)):
                new_val = self._state.energy + float(value)
                self._state.energy = max(0.0, min(100.0, new_val))
            elif key == "social_battery" and isinstance(value, (int, float)):
                new_val = self._state.social_battery + float(value)
                self._state.social_battery = max(0.0, min(100.0, new_val))
            elif hasattr(self._state, key):
                setattr(self._state, key, value)

    def on_interaction(self, interaction: Interaction) -> None:
        """Process an interaction, draining energy and social battery.

        - Decreases energy by 2
        - Decreases social_battery by 5
        - Updates last_interaction to the interaction's timestamp
        - If energy drops below 20, mood shifts to TIRED
        """
        self.update(energy=-2, social_battery=-5)
        self._state.last_interaction = interaction.timestamp

        if self._state.energy < 20:
            self._state.mood = Mood.TIRED

    def rest(self, hours: float = 1.0) -> None:
        """Recover energy and social battery over a rest period.

        Args:
            hours: Duration of rest. Energy recovers at
                ``_DEFAULT_ENERGY_REGEN_RATE`` per hour; social_battery
                recovers at half that rate.
        """
        energy_gain = _DEFAULT_ENERGY_REGEN_RATE * hours
        social_gain = (_DEFAULT_ENERGY_REGEN_RATE / 2.0) * hours

        self.update(energy=energy_gain, social_battery=social_gain)

    def reset(self) -> None:
        """Reset state to defaults (neutral mood, full energy/battery)."""
        self._state.mood = Mood.NEUTRAL
        self._state.energy = 100.0
        self._state.focus = "medium"
        self._state.social_battery = 100.0
        self._state.last_interaction = None
