import chess
import chess.engine
from plyshock.engine.stockfish_client import score_to_cp


def test_score_to_cp_handles_cp_score() -> None:
    assert score_to_cp(chess.engine.Cp(125)) == (125, False)


def test_score_to_cp_handles_pov_score_from_white_pov() -> None:
    score = chess.engine.PovScore(chess.engine.Cp(75), chess.WHITE)

    assert score_to_cp(score) == (75, False)


def test_score_to_cp_converts_black_pov_to_white_pov() -> None:
    score = chess.engine.PovScore(chess.engine.Cp(75), chess.BLACK)

    assert score_to_cp(score) == (-75, False)


def test_score_to_cp_maps_mate_scores_to_mate_score() -> None:
    assert score_to_cp(chess.engine.Mate(3), mate_score=1000) == (1000, True)
    assert score_to_cp(chess.engine.Mate(-2), mate_score=1000) == (-1000, True)


def test_score_to_cp_clips_centipawn_scores() -> None:
    assert score_to_cp(chess.engine.Cp(1500), mate_score=1000) == (1000, False)
    assert score_to_cp(chess.engine.Cp(-1500), mate_score=1000) == (-1000, False)
