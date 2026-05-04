from plyshock.features.snapshot_builder import build_snapshots_from_game_record


def test_game_reaching_35_produces_five_default_snapshots() -> None:
    record = _game_record(final_fullmove_number=35)

    snapshots = build_snapshots_from_game_record(record)

    assert [snapshot["snapshot_move"] for snapshot in snapshots] == [15, 20, 25, 30, 35]


def test_game_reaching_20_produces_15_and_20_snapshots_only() -> None:
    record = _game_record(final_fullmove_number=20)

    snapshots = build_snapshots_from_game_record(record)

    assert [snapshot["snapshot_move"] for snapshot in snapshots] == [15, 20]


def test_snapshot_clocks_are_assigned_to_sides_and_rating_context() -> None:
    record = _game_record(final_fullmove_number=35)

    snapshot = build_snapshots_from_game_record(record, snapshot_moves=[15])[0]

    assert snapshot["snapshot_ply"] == 30
    assert snapshot["white_clock_sec"] == 971
    assert snapshot["black_clock_sec"] == 970
    assert snapshot["higher_clock_sec"] == 971
    assert snapshot["lower_clock_sec"] == 970


def test_snapshot_side_to_move_is_extracted_from_fen() -> None:
    record = _game_record(final_fullmove_number=35)

    snapshot = build_snapshots_from_game_record(record, snapshot_moves=[15])[0]

    assert snapshot["side_to_move"] == "white"


def _game_record(final_fullmove_number: int) -> dict[str, object]:
    ply_count = final_fullmove_number * 2
    return {
        "game_id": "test-game",
        "site": "https://lichess.org/test-game",
        "white_elo": 2100,
        "black_elo": 2000,
        "result": "0-1",
        "winner_color": "black",
        "time_control": "300+0",
        "initial_time_sec": 300,
        "increment_sec": 0,
        "final_fullmove_number": final_fullmove_number,
        "moves_san": ["e4"] * ply_count,
        "fens_after_move": [_fen_after_ply(ply) for ply in range(1, ply_count + 1)],
        "clock_by_ply": [1000 - ply for ply in range(1, ply_count + 1)],
        "rating_gap": 100,
        "higher_rated_color": "white",
        "lower_rated_color": "black",
        "lower_is_white": False,
        "upset_label": 1,
    }


def _fen_after_ply(ply: int) -> str:
    active_color = "b" if ply % 2 == 1 else "w"
    return f"8/8/8/8/8/8/8/8 {active_color} - - 0 1"
