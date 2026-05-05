"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Chess, DEFAULT_POSITION } from "chess.js";
import type { PieceDropHandlerArgs } from "react-chessboard";
import { api } from "@/lib/api";
import type {
  LiveCheckpointHistoryItem,
  LiveEvaluateRequest,
  LiveEvaluateResponse,
  LiveMoveRecord,
  PlayerColor,
} from "@/types/plyshock";
import { LiveClockPanel } from "./LiveClockPanel";
import { LiveEvalPanel } from "./LiveEvalPanel";
import { LiveMoveList } from "./LiveMoveList";
import { LiveSetupPanel, type LiveSetupValues } from "./LiveSetupPanel";

const Chessboard = dynamic(
  () => import("react-chessboard").then((module) => module.Chessboard),
  {
    ssr: false,
    loading: () => <div className="aspect-square w-full animate-pulse rounded-2xl bg-white/[0.04]" />,
  }
);

const CHECKPOINT_MOVES = new Set([15, 20, 25, 30, 35]);

export function LiveBoardMode() {
  const chessRef = useRef(new Chess());
  const [setup, setSetup] = useState<LiveSetupValues>({
    whiteElo: 1500,
    blackElo: 1700,
    initialMinutes: 10,
    incrementSeconds: 5,
  });
  const [fen, setFen] = useState(DEFAULT_POSITION);
  const [ply, setPly] = useState(0);
  const [moves, setMoves] = useState<LiveMoveRecord[]>([]);
  const [whiteClock, setWhiteClock] = useState(600);
  const [blackClock, setBlackClock] = useState(600);
  const [running, setRunning] = useState(false);
  const [paused, setPaused] = useState(true);
  const [timedOutColor, setTimedOutColor] = useState<PlayerColor | null>(null);
  const [evaluation, setEvaluation] = useState<LiveEvaluateResponse | null>(null);
  const [latestCheckpoint, setLatestCheckpoint] = useState<LiveEvaluateResponse | null>(null);
  const [checkpointHistory, setCheckpointHistory] = useState<LiveCheckpointHistoryItem[]>([]);
  const [evaluating, setEvaluating] = useState(false);
  const [evaluationError, setEvaluationError] = useState<string | null>(null);

  const activeColor: PlayerColor = useMemo(() => {
    try {
      return new Chess(fen).turn() === "w" ? "white" : "black";
    } catch {
      return "white";
    }
  }, [fen]);
  const initialSeconds = Math.max(1, setup.initialMinutes) * 60;

  const requestEvaluation = useCallback(
    async (nextFen: string, nextPly: number, nextWhiteClock: number, nextBlackClock: number) => {
      setEvaluating(true);
      setEvaluationError(null);

      const board = new Chess(nextFen);
      const body: LiveEvaluateRequest = {
        fen: nextFen,
        white_elo: setup.whiteElo,
        black_elo: setup.blackElo,
        white_clock_sec: Math.max(0, Math.round(nextWhiteClock)),
        black_clock_sec: Math.max(0, Math.round(nextBlackClock)),
        initial_time_sec: initialSeconds,
        increment_sec: setup.incrementSeconds,
        fullmove_number: board.moveNumber(),
        ply: nextPly,
        checkpoint_history: checkpointHistory,
        eval_depth: 6,
        prediction_depth: 8,
      };

      try {
        const result = await api.liveEvaluate(body);
        setEvaluation(result);
        if (result.plyshock && result.checkpoint_move !== null) {
          const checkpointMove = result.checkpoint_move;
          setLatestCheckpoint(result);
          setCheckpointHistory((history) => {
            if (history.some((item) => item.checkpoint_move === checkpointMove)) {
              return history;
            }
            return [
              ...history,
              {
                checkpoint_move: checkpointMove,
                eval_cp_lower_pov: result.plyshock?.eval_cp_lower_pov ?? 0,
              },
            ];
          });
        }
      } catch (error) {
        setEvaluationError(error instanceof Error ? error.message : "Live evaluation failed");
      } finally {
        setEvaluating(false);
      }
    },
    [checkpointHistory, initialSeconds, setup.blackElo, setup.incrementSeconds, setup.whiteElo]
  );

  const resetGame = useCallback(() => {
    chessRef.current = new Chess();
    const clock = Math.max(1, setup.initialMinutes) * 60;
    setFen(chessRef.current.fen());
    setPly(0);
    setMoves([]);
    setWhiteClock(clock);
    setBlackClock(clock);
    setRunning(false);
    setPaused(true);
    setTimedOutColor(null);
    setEvaluation(null);
    setLatestCheckpoint(null);
    setCheckpointHistory([]);
    setEvaluationError(null);
  }, [setup.initialMinutes]);

  const startGame = useCallback(() => {
    chessRef.current = new Chess();
    const clock = Math.max(1, setup.initialMinutes) * 60;
    const nextFen = chessRef.current.fen();
    setFen(nextFen);
    setPly(0);
    setMoves([]);
    setWhiteClock(clock);
    setBlackClock(clock);
    setRunning(true);
    setPaused(false);
    setTimedOutColor(null);
    setEvaluation(null);
    setLatestCheckpoint(null);
    setCheckpointHistory([]);
    setEvaluationError(null);
    requestEvaluation(nextFen, 0, clock, clock);
  }, [requestEvaluation, setup.initialMinutes]);

  const makeMove = useCallback(
    (sourceSquare: string, targetSquare: string | null) => {
      if (!targetSquare || !running || paused || timedOutColor) {
        return false;
      }

      const sideToMove = chessRef.current.turn() === "w" ? "white" : "black";
      const move = chessRef.current.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: "q",
      });

      if (!move) {
        return false;
      }

      const nextPly = ply + 1;
      const nextFen = chessRef.current.fen();
      const checkpoint = CHECKPOINT_MOVES.has(chessRef.current.moveNumber());
      const increment = Math.max(0, setup.incrementSeconds);
      const nextWhiteClock = sideToMove === "white" ? whiteClock + increment : whiteClock;
      const nextBlackClock = sideToMove === "black" ? blackClock + increment : blackClock;

      setFen(nextFen);
      setPly(nextPly);
      setWhiteClock(nextWhiteClock);
      setBlackClock(nextBlackClock);
      setMoves((history) => [
        ...history,
        {
          ply: nextPly,
          fullmove: chessRef.current.moveNumber(),
          san: move.san,
          uci: move.lan.replace(/[-x+#]/g, ""),
          is_checkpoint: checkpoint,
        },
      ]);
      requestEvaluation(nextFen, nextPly, nextWhiteClock, nextBlackClock);
      return true;
    },
    [
      blackClock,
      paused,
      ply,
      requestEvaluation,
      running,
      setup.incrementSeconds,
      timedOutColor,
      whiteClock,
    ]
  );

  useEffect(() => {
    if (!running || paused || timedOutColor) {
      return;
    }

    const timer = window.setInterval(() => {
      if (chessRef.current.turn() === "w") {
        setWhiteClock((clock) => {
          const next = Math.max(0, clock - 1);
          if (next === 0) {
            setTimedOutColor("white");
            setPaused(true);
          }
          return next;
        });
      } else {
        setBlackClock((clock) => {
          const next = Math.max(0, clock - 1);
          if (next === 0) {
            setTimedOutColor("black");
            setPaused(true);
          }
          return next;
        });
      }
    }, 1000);

    return () => window.clearInterval(timer);
  }, [paused, running, timedOutColor]);

  const boardOptions = useMemo(
    () => ({
      position: fen,
      boardOrientation: "white" as const,
      allowDragging: running && !paused && !timedOutColor,
      allowDrawingArrows: false,
      showAnimations: true,
      onPieceDrop: ({ sourceSquare, targetSquare }: PieceDropHandlerArgs) =>
        makeMove(sourceSquare, targetSquare),
      boardStyle: {
        borderRadius: "14px",
        boxShadow: "0 24px 80px rgba(0,0,0,0.52)",
        overflow: "hidden",
      },
      darkSquareStyle: { backgroundColor: "#2a211d" },
      lightSquareStyle: { backgroundColor: "#b6a06d" },
      darkSquareNotationStyle: { color: "rgba(246,240,220,0.72)" },
      lightSquareNotationStyle: { color: "rgba(25,22,19,0.72)" },
    }),
    [fen, makeMove, paused, running, timedOutColor]
  );

  return (
    <section className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)_380px]">
      <aside className="space-y-6">
        <LiveSetupPanel
          values={setup}
          running={running}
          evaluating={evaluating}
          onChange={setSetup}
          onStart={startGame}
          onReset={resetGame}
        />
        <LiveClockPanel
          whiteClock={whiteClock}
          blackClock={blackClock}
          activeColor={activeColor}
          running={running}
          paused={paused}
          timedOutColor={timedOutColor}
          onTogglePause={() => setPaused((value) => !value)}
        />
      </aside>

      <section className="space-y-6">
        <div className="panel border border-gold/15 p-4 shadow-2xl shadow-black/35">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="font-mono text-[0.66rem] uppercase tracking-[0.22em] text-gold">
                Live board
              </p>
              <h2 className="mt-2 text-2xl font-semibold text-ivory">
                Ply {ply} · {activeColor} to move
              </h2>
            </div>
            <div className="rounded-full border border-white/10 bg-black/25 px-3 py-1.5 font-mono text-xs text-stone-300">
              Drag legal moves for either side
            </div>
          </div>

          <div className="rounded-[1.2rem] border border-gold/15 bg-black/35 p-3">
            <Chessboard options={boardOptions} />
          </div>
        </div>

        <div className="panel border border-gold/15 bg-gold/[0.045] p-5">
          <p className="font-mono text-[0.66rem] uppercase tracking-[0.22em] text-gold">
            Live mode note
          </p>
          <p className="mt-2 text-sm leading-6 text-stone-300">
            Live mode uses Stockfish every move; PlyShock predictions are only produced at trained
            mid-game checkpoints.
          </p>
        </div>
      </section>

      <aside className="space-y-6">
        <LiveEvalPanel
          evaluation={evaluation}
          latestCheckpoint={latestCheckpoint}
          evaluating={evaluating}
          currentPly={ply}
          error={evaluationError}
        />
        <LiveMoveList moves={moves} />
      </aside>
    </section>
  );
}
