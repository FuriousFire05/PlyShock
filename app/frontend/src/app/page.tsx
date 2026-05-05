"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Activity, BadgeCheck, Brain, Crown, Gauge, ShieldCheck, Trophy, User } from "lucide-react";
import { ChessReplayBoard } from "@/components/ChessReplayBoard";
import { CheckpointTimeline } from "@/components/CheckpointTimeline";
import { EvalBar } from "@/components/EvalBar";
import { GameSelector } from "@/components/GameSelector";
import { LiveBoardMode } from "@/components/LiveBoardMode";
import { MetricCard } from "@/components/MetricCard";
import { MoveList } from "@/components/MoveList";
import { PlyShockBar } from "@/components/PlyShockBar";
import { ReplayControls } from "@/components/ReplayControls";
import { ResearchSummary } from "@/components/ResearchSummary";
import { StatusBanner } from "@/components/StatusBanner";
import { api, API_BASE_URL } from "@/lib/api";
import type {
  BackendHealth,
  DemoGame,
  PlyShockPrediction,
  ReplayCheckpoint,
  ReplayResponse,
} from "@/types/plyshock";

type UiMode = "replay" | "live";

export default function Home() {
  const [health, setHealth] = useState<BackendHealth | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const [healthError, setHealthError] = useState<string | null>(null);

  const [games, setGames] = useState<DemoGame[]>([]);
  const [gamesLoading, setGamesLoading] = useState(true);
  const [gamesError, setGamesError] = useState<string | null>(null);
  const [selectedGameId, setSelectedGameId] = useState<string | null>(null);

  const [replay, setReplay] = useState<ReplayResponse | null>(null);
  const [replayLoading, setReplayLoading] = useState(false);
  const [replayError, setReplayError] = useState<string | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [mode, setMode] = useState<UiMode>("replay");

  useEffect(() => {
    let cancelled = false;

    async function loadInitialData() {
      setHealthLoading(true);
      setGamesLoading(true);

      const [healthResult, gamesResult] = await Promise.allSettled([
        api.health(),
        api.demoGames(),
      ]);

      if (cancelled) {
        return;
      }

      if (healthResult.status === "fulfilled") {
        setHealth(healthResult.value);
        setHealthError(null);
      } else {
        setHealth(null);
        setHealthError(
          healthResult.reason instanceof Error ? healthResult.reason.message : "Failed to fetch"
        );
      }
      setHealthLoading(false);

      if (gamesResult.status === "fulfilled") {
        setGames(gamesResult.value);
        setGamesError(null);
        setSelectedGameId(gamesResult.value[0]?.id ?? null);
      } else {
        setGames([]);
        setGamesError(
          gamesResult.reason instanceof Error ? gamesResult.reason.message : "Failed to fetch"
        );
      }
      setGamesLoading(false);
    }

    loadInitialData();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedGameId) {
      return;
    }

    let cancelled = false;

    async function loadReplay(gameId: string) {
      setReplayLoading(true);
      setReplayError(null);
      setReplay(null);
      setCurrentIndex(0);
      setIsPlaying(false);

      try {
        const result = await api.replay(gameId);
        if (cancelled) {
          return;
        }
        setReplay(result);
      } catch (error) {
        if (cancelled) {
          return;
        }
        setReplayError(error instanceof Error ? error.message : "Could not load replay");
      } finally {
        if (!cancelled) {
          setReplayLoading(false);
        }
      }
    }

    loadReplay(selectedGameId);

    return () => {
      cancelled = true;
    };
  }, [selectedGameId]);

  const maxIndex = Math.max(0, (replay?.moves.length ?? 1) - 1);
  const currentMove = replay?.moves[currentIndex] ?? null;

  useEffect(() => {
    if (!isPlaying || !replay?.moves.length) {
      return;
    }

    const timer = window.setInterval(() => {
      setCurrentIndex((previous) => (previous >= maxIndex ? 0 : previous + 1));
    }, 900);

    return () => window.clearInterval(timer);
  }, [isPlaying, maxIndex, replay?.moves.length]);

  const latestCheckpoint: ReplayCheckpoint | null = useMemo(() => {
    if (!replay || !currentMove) {
      return null;
    }

    let latest: ReplayCheckpoint | null = null;
    for (const checkpoint of replay.checkpoints) {
      if (checkpoint.ply <= currentMove.ply) {
        latest = checkpoint;
      }
    }
    return latest;
  }, [currentMove, replay]);

  const latestPrediction: PlyShockPrediction | null = useMemo(() => {
    if (!replay || !latestCheckpoint) {
      return null;
    }

    return replay.moves.find((move) => move.ply === latestCheckpoint.ply)?.plyshock ?? null;
  }, [latestCheckpoint, replay]);

  const selectedGame = games.find((game) => game.id === selectedGameId) ?? null;
  const backendError = healthError ?? gamesError;

  const seek = useCallback(
    (index: number) => {
      setCurrentIndex(Math.min(maxIndex, Math.max(0, index)));
      setIsPlaying(false);
    },
    [maxIndex]
  );

  const seekPly = useCallback(
    (ply: number) => {
      if (!replay) {
        return;
      }
      const nextIndex = replay.moves.findIndex((move) => move.ply === ply);
      if (nextIndex >= 0) {
        seek(nextIndex);
      }
    },
    [replay, seek]
  );

  const handleSelectGame = useCallback((gameId: string) => {
    setSelectedGameId(gameId);
  }, []);

  return (
    <main className="min-h-screen overflow-hidden bg-page text-ivory">
      <div className="pointer-events-none fixed inset-0 bg-[linear-gradient(rgba(255,255,255,0.025)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.025)_1px,transparent_1px)] bg-[size:72px_72px]" />
      <div className="relative mx-auto flex w-full max-w-[1500px] flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8 lg:py-10">
        <header className="grid gap-6 xl:grid-cols-[1fr_420px] xl:items-end">
          <motion.div initial={{ y: 14, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-gold/25 bg-gold/[0.07] px-3 py-1.5 font-mono text-[0.68rem] uppercase tracking-[0.22em] text-gold">
              <Activity size={13} />
              Interactive chess replay lab
            </div>
            <h1 className="text-5xl font-semibold tracking-tight text-ivory sm:text-6xl lg:text-7xl">
              PlyShock
            </h1>
            <p className="mt-4 max-w-4xl text-lg leading-8 text-stone-300">
              Dynamic Upset Prediction in Chess Using Mid-Game Human-Centric Features.
            </p>
            <p className="mt-3 max-w-4xl text-sm leading-7 text-stone-500">
              Replay every ply with Stockfish eval, then watch PlyShock update only at trained
              checkpoint moves. Upset means the lower-rated player beats the higher-rated player.
            </p>
          </motion.div>

          <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
            <MetricCard
              label="Backend"
              value={health?.status ?? "Offline"}
              detail={API_BASE_URL}
              icon={ShieldCheck}
              tone={health ? "green" : "red"}
            />
            <MetricCard
              label="Endpoints"
              value="/replay + /live"
              detail="Replay PGNs or evaluate a live board position."
              icon={Gauge}
              tone="gold"
            />
            <MetricCard
              label="Model"
              value="best_model"
              detail="Classical model artifact served by FastAPI."
              icon={Brain}
              tone="ivory"
            />
          </div>
        </header>

        <StatusBanner health={health} loading={healthLoading} error={backendError} />

        <section className="panel flex flex-col gap-3 border border-white/10 p-2 sm:flex-row">
          <ModeButton
            active={mode === "replay"}
            title="Replay Mode"
            detail="Inspect bundled PGNs ply by ply"
            onClick={() => setMode("replay")}
          />
          <ModeButton
            active={mode === "live"}
            title="Live Board Mode"
            detail="Play legal moves and evaluate the current board"
            onClick={() => setMode("live")}
          />
        </section>

        {mode === "live" ? (
          <LiveBoardMode />
        ) : (
          <section className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)_380px]">
          <aside className="space-y-6">
            <GameSelector
              games={games}
              selectedId={selectedGameId}
              loading={gamesLoading}
              disabled={Boolean(gamesError)}
              onSelect={handleSelectGame}
            />

            <div className="panel border border-white/10 p-5">
              <p className="font-mono text-[0.66rem] uppercase tracking-[0.22em] text-gold">
                Game metadata
              </p>
              {replay ? (
                <div className="mt-4 grid gap-3">
                  <MetricCard
                    label="White Elo"
                    value={replay.metadata.white_elo}
                    detail={replay.metadata.white ?? "White"}
                    icon={User}
                    tone={replay.metadata.higher_rated_color === "white" ? "gold" : "muted"}
                  />
                  <MetricCard
                    label="Black Elo"
                    value={replay.metadata.black_elo}
                    detail={replay.metadata.black ?? "Black"}
                    icon={User}
                    tone={replay.metadata.higher_rated_color === "black" ? "gold" : "muted"}
                  />
                  <MetricCard
                    label="Rating gap"
                    value={`${replay.metadata.rating_gap} pts`}
                    detail={`Lower-rated: ${replay.metadata.lower_rated_color}`}
                    icon={Crown}
                    tone="ivory"
                  />
                  <MetricCard
                    label="Actual result"
                    value={replay.metadata.result}
                    detail={
                      replay.metadata.actual_upset_label === 1
                        ? "Actual upset occurred"
                        : "Higher-rated player won"
                    }
                    icon={Trophy}
                    tone={replay.metadata.actual_upset_label === 1 ? "red" : "green"}
                  />
                  <MetricCard
                    label="Eval depth"
                    value={replay.summary.eval_depth}
                    detail={`Prediction depth ${replay.summary.prediction_depth}`}
                    icon={Gauge}
                    tone="gold"
                  />
                  <MetricCard
                    label="Actual upset"
                    value={replay.metadata.actual_upset_label}
                    detail="1 means the lower-rated player won."
                    icon={BadgeCheck}
                    tone={replay.metadata.actual_upset_label === 1 ? "red" : "green"}
                  />
                </div>
              ) : (
                <p className="mt-4 text-sm leading-6 text-stone-500">
                  {selectedGame
                    ? "Replay metadata will appear after analysis loads."
                    : "Select a bundled PGN to begin."}
                </p>
              )}
            </div>
          </aside>

          <section className="space-y-6">
            {replayLoading ? (
              <div className="panel flex min-h-[620px] items-center justify-center border border-white/10">
                <div className="text-center">
                  <div className="mx-auto mb-4 h-11 w-11 animate-spin rounded-full border-2 border-gold border-t-transparent" />
                  <p className="font-semibold text-ivory">Loading interactive replay</p>
                  <p className="mt-2 text-sm text-stone-500">
                    Fetching FENs, clocks, Stockfish evals, and checkpoint predictions.
                  </p>
                </div>
              </div>
            ) : replayError ? (
              <div className="panel flex min-h-[520px] items-center justify-center border border-red-400/25 bg-red-400/[0.05] p-8">
                <div className="max-w-xl text-center">
                  <p className="font-mono text-[0.66rem] uppercase tracking-[0.22em] text-red-300">
                    Replay unavailable
                  </p>
                  <h2 className="mt-3 text-2xl font-semibold text-ivory">
                    The backend could not analyze this game
                  </h2>
                  <p className="mt-3 text-sm leading-6 text-stone-400">{replayError}</p>
                </div>
              </div>
            ) : (
              <>
                <ChessReplayBoard move={currentMove} metadata={replay?.metadata ?? null} />
                <ReplayControls
                  currentIndex={currentIndex}
                  maxIndex={maxIndex}
                  isPlaying={isPlaying}
                  onFirst={() => seek(0)}
                  onPrevious={() => seek(currentIndex - 1)}
                  onNext={() => seek(currentIndex + 1)}
                  onLast={() => seek(maxIndex)}
                  onTogglePlay={() => setIsPlaying((playing) => !playing)}
                  onSeek={seek}
                />
                <CheckpointTimeline
                  checkpoints={replay?.checkpoints ?? []}
                  currentPly={currentMove?.ply ?? 0}
                  onSelectPly={seekPly}
                />
              </>
            )}
          </section>

          <aside className="space-y-6">
            <EvalBar move={currentMove} />
            <PlyShockBar
              currentMove={currentMove}
              latestCheckpoint={latestCheckpoint}
              latestPrediction={latestPrediction}
              metadata={replay?.metadata ?? null}
            />
            <MoveList
              moves={replay?.moves ?? []}
              currentPly={currentMove?.ply ?? 0}
              onSelectPly={seekPly}
            />
          </aside>
        </section>
        )}

        <ResearchSummary />
      </div>
    </main>
  );
}

function ModeButton({
  active,
  title,
  detail,
  onClick,
}: {
  active: boolean;
  title: string;
  detail: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={
        active
          ? "flex-1 rounded-2xl border border-gold/45 bg-gold/15 px-4 py-3 text-left text-ivory shadow-[0_0_28px_rgba(212,175,55,0.12)]"
          : "flex-1 rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-left text-stone-400 transition hover:border-gold/30 hover:text-ivory"
      }
    >
      <span className="block text-sm font-semibold">{title}</span>
      <span className="mt-1 block text-xs text-stone-500">{detail}</span>
    </button>
  );
}
