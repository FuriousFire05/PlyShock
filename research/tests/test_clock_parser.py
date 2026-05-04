import pytest
from plyshock.parsing.clock_parser import (
    extract_clock_comment,
    parse_clock_to_seconds,
    parse_time_control,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("300+0", (300, 0)),
        ("600+5", (600, 5)),
        ("180+2", (180, 2)),
        (" 60+1 ", (60, 1)),
    ],
)
def test_parse_time_control_valid(value: str, expected: tuple[int, int]) -> None:
    assert parse_time_control(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "",
        "300",
        "300+",
        "+5",
        "300 + 5",
        "300-5",
        "five+0",
    ],
)
def test_parse_time_control_invalid(value: str) -> None:
    with pytest.raises(ValueError, match="Invalid time control"):
        parse_time_control(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("0:04:56", 296),
        ("4:56", 296),
        ("01:02:03", 3723),
        ("0:00:09", 9),
        ("12:34", 754),
        (" 1:00:00 ", 3600),
    ],
)
def test_parse_clock_to_seconds_valid(value: str, expected: int) -> None:
    assert parse_clock_to_seconds(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "",
        "4",
        "4:5",
        "1:2:03",
        "1:02:3",
        "1:60:00",
        "1:00:60",
        "-1:00",
        "abc",
    ],
)
def test_parse_clock_to_seconds_invalid(value: str) -> None:
    with pytest.raises(ValueError, match="Invalid clock value"):
        parse_clock_to_seconds(value)


@pytest.mark.parametrize(
    ("comment", "expected"),
    [
        ("[%clk 0:04:56]", 296),
        ("{ [%clk 0:04:56] }", 296),
        ("[%eval 0.17] [%clk 0:04:56]", 296),
        ("This is fine [%clk 4:56]", 296),
    ],
)
def test_extract_clock_comment_valid(comment: str, expected: int) -> None:
    assert extract_clock_comment(comment) == expected


@pytest.mark.parametrize(
    "comment",
    [
        "",
        "plain annotation",
        "[%eval 0.17]",
        "{ [%emt 0:00:03] }",
    ],
)
def test_extract_clock_comment_without_clock_returns_none(comment: str) -> None:
    assert extract_clock_comment(comment) is None


@pytest.mark.parametrize(
    "comment",
    [
        "[%clk]",
        "[%clk nope]",
        "[%clk 0:04:60]",
        "[%clk 0:04:56",
        "[%clk0:04:56]",
    ],
)
def test_extract_clock_comment_malformed_clock_raises(comment: str) -> None:
    with pytest.raises(ValueError):
        extract_clock_comment(comment)
