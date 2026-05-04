"""Parsing helpers for Lichess time controls and clock annotations."""

from __future__ import annotations

import re

_TIME_CONTROL_RE = re.compile(r"^(?P<initial>\d+)\+(?P<increment>\d+)$")
_CLOCK_TAG_RE = re.compile(r"\[%clk\b(?P<body>[^\]]*)\]")


def parse_time_control(value: str) -> tuple[int, int]:
    """Parse a Lichess time control string into initial and increment seconds.

    Args:
        value: Time control in ``initial+increment`` format, such as ``"600+5"``.

    Returns:
        A tuple of ``(initial_seconds, increment_seconds)``.

    Raises:
        ValueError: If the value is not in Lichess ``initial+increment`` format.
    """
    if not isinstance(value, str):
        raise ValueError("Time control must be a string in 'initial+increment' format.")

    match = _TIME_CONTROL_RE.fullmatch(value.strip())
    if match is None:
        raise ValueError(
            f"Invalid time control {value!r}; expected 'initial+increment' seconds, "
            "for example '300+0'."
        )

    return int(match["initial"]), int(match["increment"])


def parse_clock_to_seconds(value: str) -> int:
    """Parse a Lichess clock value into total seconds.

    Supports ``H:MM:SS`` and ``M:SS`` formats.

    Args:
        value: Clock value such as ``"0:04:56"`` or ``"4:56"``.

    Returns:
        The total number of seconds represented by the clock.

    Raises:
        ValueError: If the value is not a valid clock string.
    """
    if not isinstance(value, str):
        raise ValueError("Clock value must be a string in 'H:MM:SS' or 'M:SS' format.")

    parts = value.strip().split(":")
    if len(parts) == 2:
        minutes, seconds = _parse_clock_parts(value, parts, minute_index=0)
        return minutes * 60 + seconds

    if len(parts) == 3:
        hours_text, minutes_text, seconds_text = parts
        if not hours_text.isdigit():
            raise _invalid_clock_error(value)

        hours = int(hours_text)
        minutes, seconds = _parse_clock_parts(value, [minutes_text, seconds_text], minute_index=1)
        return hours * 3600 + minutes * 60 + seconds

    raise _invalid_clock_error(value)


def extract_clock_comment(comment: str) -> int | None:
    """Extract a Lichess ``[%clk ...]`` annotation from a PGN comment.

    Args:
        comment: A PGN comment that may contain a Lichess clock tag.

    Returns:
        Clock seconds if a valid clock tag is present, otherwise ``None``.

    Raises:
        ValueError: If a clock tag is present but malformed.
    """
    if not isinstance(comment, str):
        raise ValueError("Comment must be a string.")

    if "[%clk" in comment and (match := _CLOCK_TAG_RE.search(comment)) is None:
        raise ValueError(f"Malformed clock tag in comment {comment!r}.")

    match = _CLOCK_TAG_RE.search(comment)
    if match is None:
        return None

    clock_text = match["body"].strip()
    if not clock_text:
        raise ValueError(f"Malformed clock tag in comment {comment!r}; missing clock value.")

    return parse_clock_to_seconds(clock_text)


def _parse_clock_parts(value: str, parts: list[str], minute_index: int) -> tuple[int, int]:
    minutes_text, seconds_text = parts
    if (
        not minutes_text.isdigit()
        or not seconds_text.isdigit()
        or len(seconds_text) != 2
        or (minute_index == 1 and len(minutes_text) != 2)
    ):
        raise _invalid_clock_error(value)

    minutes = int(minutes_text)
    seconds = int(seconds_text)
    if seconds >= 60 or (minute_index == 1 and minutes >= 60):
        raise _invalid_clock_error(value)

    return minutes, seconds


def _invalid_clock_error(value: str) -> ValueError:
    return ValueError(
        f"Invalid clock value {value!r}; expected 'H:MM:SS' or 'M:SS' with seconds below 60."
    )
