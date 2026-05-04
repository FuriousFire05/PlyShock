"""Reusable Stockfish evaluation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import chess
import chess.engine


@dataclass(frozen=True)
class EngineEvaluation:
    """A Stockfish evaluation normalized from White's point of view."""

    fen: str
    eval_cp_white_pov: int
    eval_cp_clipped: int
    mate_flag: bool
    depth: int | None


def score_to_cp(
    score: chess.engine.PovScore | chess.engine.Score, mate_score: int = 1000
) -> tuple[int, bool]:
    """Convert a python-chess score into clipped centipawns from White's point of view.

    Args:
        score: A python-chess ``PovScore`` or ``Score``.
        mate_score: Centipawn value used for mate scores and clipping bounds.

    Returns:
        Tuple of ``(centipawns, mate_flag)``.
    """
    white_score = score.white() if isinstance(score, chess.engine.PovScore) else score
    mate_flag = white_score.is_mate()
    if mate_flag:
        mate_in = white_score.mate()
        if mate_in is None:
            raise ValueError(f"Could not convert mate score {score!r} to centipawns.")
        centipawns = mate_score if mate_in > 0 else -mate_score
    else:
        centipawns = white_score.score()
        if centipawns is None:
            raise ValueError(f"Could not convert score {score!r} to centipawns.")

    clipped = max(-mate_score, min(mate_score, int(centipawns)))
    return clipped, mate_flag


def evaluate_fen(engine_path: str | Path, fen: str, depth: int = 8) -> EngineEvaluation:
    """Evaluate a FEN with Stockfish through python-chess.

    Args:
        engine_path: Path to the Stockfish executable.
        fen: FEN position to evaluate.
        depth: Search depth for the analysis limit.

    Returns:
        Normalized engine evaluation.
    """
    return evaluate_fens(engine_path, [fen], depth=depth)[0]


def evaluate_fens(
    engine_path: str | Path, fens: list[str], depth: int = 8
) -> list[EngineEvaluation]:
    """Evaluate multiple FENs with a single Stockfish process.

    Args:
        engine_path: Path to the Stockfish executable.
        fens: FEN positions to evaluate.
        depth: Search depth for the analysis limit.

    Returns:
        Normalized engine evaluations in the same order as ``fens``.
    """
    engine = chess.engine.SimpleEngine.popen_uci(str(Path(engine_path)))
    try:
        evaluations: list[EngineEvaluation] = []
        for fen in fens:
            board = chess.Board(fen)
            info = engine.analyse(board, chess.engine.Limit(depth=depth))
            score = info.get("score")
            if score is None:
                raise ValueError(f"Engine returned no score for FEN {fen!r}.")

            eval_cp, mate_flag = score_to_cp(score)
            evaluations.append(
                EngineEvaluation(
                    fen=fen,
                    eval_cp_white_pov=eval_cp,
                    eval_cp_clipped=eval_cp,
                    mate_flag=mate_flag,
                    depth=depth,
                )
            )

        return evaluations
    finally:
        engine.quit()
