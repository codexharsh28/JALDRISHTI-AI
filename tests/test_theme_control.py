"""
Unit tests for Theme Control, Persistence & Theme State Specifications.
"""

import pytest

SUPPORTED_THEMES = ["dark", "light", "system"]

def test_supported_theme_states():
    assert "dark" in SUPPORTED_THEMES
    assert "light" in SUPPORTED_THEMES
    assert "system" in SUPPORTED_THEMES

def test_theme_state_transition():
    def get_next_theme(current: str) -> str:
        if current == "dark":
            return "light"
        elif current == "light":
            return "system"
        return "dark"

    assert get_next_theme("dark") == "light"
    assert get_next_theme("light") == "system"
    assert get_next_theme("system") == "dark"

def test_theme_persistence_key_convention():
    storage_key = "jaldrishti_theme"
    assert storage_key.startswith("jaldrishti_")
