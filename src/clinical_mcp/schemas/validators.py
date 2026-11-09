"""Reusable clinical validator helpers with human-readable errors."""

from __future__ import annotations


def check_range(name: str, value: float, low: float, high: float) -> float:
    """Raise a clinically worded error when a value is incompatible with life."""
    if not low <= value <= high:
        raise ValueError(
            f"{name} {value:g} is incompatible with life (valid range: {low:g}-{high:g})"
        )
    return value
