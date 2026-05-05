"use client";

import dynamic from "next/dynamic";
import { Clock, Hash, MoveRight } from "lucide-react";
import type { ReplayMetadata, ReplayMove } from "@/types/plyshock";
import { formatClock } from "@/lib/utils";

const Chessboard = dynamic(
  () => import("react-chessboard").then((module) => module.Chessboard),
  {
    ssr: false,
    loading: () => <div className="aspect-square w-full animate-pulse rounded-2xl bg-white/[0.04]" />,
  }
);

interface ChessReplayBoardProps {
  move: ReplayMove | null;
  metadata: ReplayMetadata | null;
}

export function ChessReplayBoard({ move, metadata }: ChessReplayBoardProps) {
  const orientation = metadata?.lower_rated_color === "white" ? "white" : "black";

  return (
    <section className="panel border border-gold/15 p-4 shadow-2xl shadow-black/35">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="font-mono text-[0.66rem] uppercase tracking-[0.22em] text-gold">
            Replay board
          </p>
          <h2 className="mt-2 text-2xl font-semibold text-ivory">
            Ply {move?.ply ?? 0} · Move {move?.fullmove ?? 1}
          </h2>
        </div>
        <div className="rounded-full border border-white/10 bg-black/25 px-3 py-1.5 font-mono text-xs text-stone-300">
          Oriented to {metadata?.lower_rated_color ?? "black"}
        </div>
      </div>

      <div className="rounded-[1.2rem] border border-gold/15 bg-black/35 p-3">
        {move ? (
          <Chessboard
            options={{
              position: move.fen,
              boardOrientation: orientation,
              allowDragging: false,
              allowDrawingArrows: false,
              showAnimations: true,
              boardStyle: {
                borderRadius: "14px",
                boxShadow: "0 24px 80px rgba(0,0,0,0.52)",
                overflow: "hidden",
              },
              darkSquareStyle: { backgroundColor: "#2a211d" },
              lightSquareStyle: { backgroundColor: "#b6a06d" },
              darkSquareNotationStyle: { color: "rgba(246,240,220,0.72)" },
              lightSquareNotationStyle: { color: "rgba(25,22,19,0.72)" },
            }}
          />
        ) : (
          <div className="flex aspect-square items-center justify-center rounded-2xl border border-dashed border-white/10 bg-white/[0.03] text-sm text-stone-500">
            Select a game to load the replay board.
          </div>
        )}
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <BoardFact icon={MoveRight} label="SAN" value={move?.san ?? "Starting position"} />
        <BoardFact icon={Hash} label="UCI" value={move?.uci ?? "--"} />
        <BoardFact icon={Clock} label="White clock" value={formatClock(move?.white_clock_sec)} />
        <BoardFact icon={Clock} label="Black clock" value={formatClock(move?.black_clock_sec)} />
      </div>
    </section>
  );
}

function BoardFact({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof MoveRight;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.035] p-3">
      <div className="flex items-center gap-2 text-stone-500">
        <Icon size={14} />
        <p className="font-mono text-[0.62rem] uppercase tracking-[0.18em]">{label}</p>
      </div>
      <p className="mt-2 truncate text-sm font-semibold text-ivory">{value}</p>
    </div>
  );
}
