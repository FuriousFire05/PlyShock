export type PlayerColor = "white" | "black";

export interface BackendHealth {
  status: string;
  app: string;
  model_exists: boolean;
  schema_exists: boolean;
  stockfish_exists?: boolean;
  demo_games_count?: number;
}

export interface DemoGame {
  id: string;
  filename: string;
  path: string;
}

export interface ReplayMetadata {
  game_id: string;
  white: string | null;
  black: string | null;
  white_elo: number;
  black_elo: number;
  result: string;
  winner_color: PlayerColor;
  rating_gap: number;
  higher_rated_color: PlayerColor;
  lower_rated_color: PlayerColor;
  actual_upset_label: number;
}

export interface PlyShockPrediction {
  upset_probability: number | null;
  predicted_label: 0 | 1;
  interpretation: string;
  eval_cp_lower_pov: number;
  lower_clock_sec: number | null;
  higher_clock_sec: number | null;
}

export interface ReplayMove {
  ply: number;
  fullmove: number;
  san: string | null;
  uci: string | null;
  fen: string;
  side_to_move: PlayerColor;
  white_clock_sec: number | null;
  black_clock_sec: number | null;
  stockfish_eval_cp_white_pov: number | null;
  stockfish_bar: number | null;
  is_checkpoint: boolean;
  checkpoint_move: number | null;
  plyshock: PlyShockPrediction | null;
}

export interface ReplayCheckpoint {
  snapshot_move: number;
  ply: number;
  fen: string;
  upset_probability: number | null;
  predicted_label: 0 | 1;
  eval_cp_lower_pov: number;
}

export interface ReplaySummary {
  total_plies: number;
  returned_plies: number;
  checkpoint_count: number;
  eval_depth: number;
  prediction_depth: number;
  model_name: string;
}

export interface ReplayResponse {
  metadata: ReplayMetadata;
  moves: ReplayMove[];
  checkpoints: ReplayCheckpoint[];
  summary: ReplaySummary;
}
