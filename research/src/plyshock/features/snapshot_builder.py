"""Build mid-game snapshot rows from filtered game records."""

from __future__ import annotations

DEFAULT_SNAPSHOT_MOVES = [15, 20, 25, 30, 35]
SNAPSHOT_COLUMNS = [
    "game_id",
    "snapshot_move",
    "snapshot_ply",
    "fen",
    "side_to_move",
    "white_elo",
    "black_elo",
    "result",
    "winner_color",
    "time_control",
    "initial_time_sec",
    "increment_sec",
    "final_fullmove_number",
    "rating_gap",
    "higher_rated_color",
    "lower_rated_color",
    "lower_is_white",
    "white_clock_sec",
    "black_clock_sec",
    "lower_clock_sec",
    "higher_clock_sec",
    "upset_label",
]


def build_snapshots_from_game_record(
    record: dict[str, object], snapshot_moves: list[int] | None = None
) -> list[dict[str, object]]:
    """Build mid-game snapshot rows for one filtered game record.

    Args:
        record: Filtered game record from the parquet dataset.
        snapshot_moves: Fullmove numbers to sample. Defaults to ``[15, 20, 25, 30, 35]``.

    Returns:
        Snapshot rows for each requested fullmove reached by the game.
    """
    selected_moves = snapshot_moves or DEFAULT_SNAPSHOT_MOVES
    fens_after_move = _as_list(record.get("fens_after_move"))
    clock_by_ply = _as_list(record.get("clock_by_ply"))
    final_fullmove_number = int(record["final_fullmove_number"])

    snapshots: list[dict[str, object]] = []
    for snapshot_move in selected_moves:
        if snapshot_move > final_fullmove_number or not fens_after_move:
            continue

        snapshot_ply_index = min(snapshot_move * 2 - 1, len(fens_after_move) - 1)
        snapshot_ply = snapshot_ply_index + 1
        fen = str(fens_after_move[snapshot_ply_index])
        white_clock_sec, black_clock_sec = _latest_clocks(clock_by_ply, snapshot_ply_index)
        lower_clock_sec, higher_clock_sec = _rating_mapped_clocks(
            lower_rated_color=str(record["lower_rated_color"]),
            higher_rated_color=str(record["higher_rated_color"]),
            white_clock_sec=white_clock_sec,
            black_clock_sec=black_clock_sec,
        )

        snapshots.append(
            {
                "game_id": record["game_id"],
                "snapshot_move": snapshot_move,
                "snapshot_ply": snapshot_ply,
                "fen": fen,
                "side_to_move": _side_to_move_from_fen(fen),
                "white_elo": record["white_elo"],
                "black_elo": record["black_elo"],
                "result": record["result"],
                "winner_color": record["winner_color"],
                "time_control": record["time_control"],
                "initial_time_sec": record["initial_time_sec"],
                "increment_sec": record["increment_sec"],
                "final_fullmove_number": record["final_fullmove_number"],
                "rating_gap": record["rating_gap"],
                "higher_rated_color": record["higher_rated_color"],
                "lower_rated_color": record["lower_rated_color"],
                "lower_is_white": record["lower_is_white"],
                "white_clock_sec": white_clock_sec,
                "black_clock_sec": black_clock_sec,
                "lower_clock_sec": lower_clock_sec,
                "higher_clock_sec": higher_clock_sec,
                "upset_label": record["upset_label"],
            }
        )

    return snapshots


def _as_list(value: object) -> list[object]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if hasattr(value, "tolist"):
        return value.tolist()
    return list(value)  # type: ignore[arg-type]


def _latest_clocks(
    clock_by_ply: list[object], snapshot_ply_index: int
) -> tuple[int | None, int | None]:
    white_clock_sec: int | None = None
    black_clock_sec: int | None = None
    for index, clock in enumerate(clock_by_ply[: snapshot_ply_index + 1]):
        if clock is None:
            continue

        if (index + 1) % 2 == 1:
            white_clock_sec = int(clock)
        else:
            black_clock_sec = int(clock)

    return white_clock_sec, black_clock_sec


def _rating_mapped_clocks(
    *,
    lower_rated_color: str,
    higher_rated_color: str,
    white_clock_sec: int | None,
    black_clock_sec: int | None,
) -> tuple[int | None, int | None]:
    clock_by_color = {"white": white_clock_sec, "black": black_clock_sec}
    return clock_by_color[lower_rated_color], clock_by_color[higher_rated_color]


def _side_to_move_from_fen(fen: str) -> str:
    parts = fen.split()
    if len(parts) < 2:
        raise ValueError(f"Invalid FEN {fen!r}; missing active color field.")
    if parts[1] == "w":
        return "white"
    if parts[1] == "b":
        return "black"
    raise ValueError(f"Invalid FEN {fen!r}; active color must be 'w' or 'b'.")
