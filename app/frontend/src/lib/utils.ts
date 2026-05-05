import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPercent(value: number | null | undefined, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "N/A";
  }
  return `${(value * 100).toFixed(digits)}%`;
}

export function formatClock(seconds: number | null | undefined) {
  if (seconds === null || seconds === undefined || Number.isNaN(seconds)) {
    return "--:--";
  }

  const safe = Math.max(0, Math.round(seconds));
  const minutes = Math.floor(safe / 60);
  const remainder = safe % 60;
  return `${minutes}:${remainder.toString().padStart(2, "0")}`;
}

export function formatEval(centipawns: number | null | undefined) {
  if (centipawns === null || centipawns === undefined || Number.isNaN(centipawns)) {
    return "N/A";
  }

  const pawns = centipawns / 100;
  return `${pawns > 0 ? "+" : ""}${pawns.toFixed(2)}`;
}

export function formatMetric(value: number, digits = 3) {
  return value.toFixed(digits);
}

export function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}
