import chess
import chess.engine
import pytest
from plyshock.engine.stockfish_client import evaluate_fens, score_to_cp


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


def test_evaluate_fens_reuses_one_engine_and_preserves_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fens = [
        "8/8/8/8/8/8/8/8 w - - 0 1",
        "8/8/8/8/8/8/8/8 b - - 0 1",
    ]
    fake_engine = _FakeEngine([chess.engine.Cp(10), chess.engine.Cp(-20)])
    opened_paths: list[str] = []

    def fake_popen_uci(engine_path: str) -> _FakeEngine:
        opened_paths.append(engine_path)
        return fake_engine

    monkeypatch.setattr(chess.engine.SimpleEngine, "popen_uci", fake_popen_uci)

    evaluations = evaluate_fens("stockfish.exe", fens, depth=9)

    assert opened_paths == ["stockfish.exe"]
    assert [evaluation.fen for evaluation in evaluations] == fens
    assert [evaluation.eval_cp_white_pov for evaluation in evaluations] == [10, -20]
    assert [evaluation.depth for evaluation in evaluations] == [9, 9]
    assert fake_engine.analyse_calls == 2
    assert fake_engine.quit_calls == 1


def test_evaluate_fens_quits_engine_when_analysis_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_engine = _FailingEngine()

    def fake_popen_uci(engine_path: str) -> _FailingEngine:
        return fake_engine

    monkeypatch.setattr(chess.engine.SimpleEngine, "popen_uci", fake_popen_uci)

    with pytest.raises(RuntimeError, match="analysis failed"):
        evaluate_fens("stockfish.exe", ["8/8/8/8/8/8/8/8 w - - 0 1"])

    assert fake_engine.quit_calls == 1


class _FakeEngine:
    def __init__(self, scores: list[chess.engine.Score]) -> None:
        self._scores = scores
        self.analyse_calls = 0
        self.quit_calls = 0

    def analyse(self, board: chess.Board, limit: chess.engine.Limit) -> dict[str, object]:
        del board, limit
        score = self._scores[self.analyse_calls]
        self.analyse_calls += 1
        return {"score": chess.engine.PovScore(score, chess.WHITE)}

    def quit(self) -> None:
        self.quit_calls += 1


class _FailingEngine:
    def __init__(self) -> None:
        self.quit_calls = 0

    def analyse(self, board: chess.Board, limit: chess.engine.Limit) -> dict[str, object]:
        del board, limit
        raise RuntimeError("analysis failed")

    def quit(self) -> None:
        self.quit_calls += 1
