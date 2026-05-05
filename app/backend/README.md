# PlyShock Demo Backend

Run the FastAPI backend from the repository root:

```bash
uv run uvicorn app.backend.main:app --reload
```

Open Swagger docs:

http://127.0.0.1:8000/docs

The backend enables local-development CORS for `localhost` and `127.0.0.1` frontend
origins on ports 3000 and 3001.

## Local Artifacts

The demo relies on local artifacts:

- `research/artifacts/models/best_model.joblib`
- `research/data/processed/feature_schema_50k.json`
- `research/tools/stockfish/stockfish.exe`

These model, schema, and Stockfish files are local demo artifacts and may not be committed in
all clones. Missing artifacts are reported through `/health` and clear API errors.

## Demo Games

List bundled PGNs:

```bash
curl http://127.0.0.1:8000/demo-games
```

Fetch one bundled PGN:

```bash
curl http://127.0.0.1:8000/demo-games/sample
```

Analyze one bundled PGN:

```bash
curl http://127.0.0.1:8000/demo-games/sample/analysis
```

Analyze one bundled PGN with full move replay:

```bash
curl "http://127.0.0.1:8000/demo-games/sample/replay?eval_depth=6&prediction_depth=8&max_plies=90"
```

Replay responses include:

- `metadata`: game, Elo, result, rating-gap, and upset-label context
- `moves`: ply-by-ply FEN, SAN/UCI, clock state, Stockfish eval, and eval-bar value
- `checkpoints`: compact PlyShock predictions at trained checkpoint moves
- `summary`: returned plies, evaluation depth, prediction depth, and model name

## Analyze Uploaded PGN

Submit a PGN directly:

```bash
curl -X POST http://127.0.0.1:8000/analyze-pgn \
  -H "Content-Type: application/json" \
  -d "{\"pgn_text\":\"...\",\"depth\":8,\"snapshot_moves\":[15,20,25,30,35]}"
```

Submit a PGN for full replay:

```bash
curl -X POST http://127.0.0.1:8000/analyze-pgn-replay \
  -H "Content-Type: application/json" \
  -d "{\"pgn_text\":\"...\",\"eval_depth\":6,\"prediction_depth\":8,\"checkpoint_moves\":[15,20,25,30,35],\"max_plies\":90}"
```

Predictions activate only at the configured mid-game snapshot moves. The default snapshot
moves are 15, 20, 25, 30, and 35. Replay responses include every returned ply for board,
clock, and Stockfish eval-bar rendering, but `plyshock` is only populated on checkpoint plies.

## Live Board Evaluation

Evaluate a live FEN with clocks:

```bash
curl -X POST http://127.0.0.1:8000/live/evaluate \
  -H "Content-Type: application/json" \
  -d "{\"fen\":\"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\",\"white_elo\":1500,\"black_elo\":1700,\"white_clock_sec\":600,\"black_clock_sec\":600,\"initial_time_sec\":600,\"increment_sec\":5,\"fullmove_number\":1,\"ply\":0,\"checkpoint_history\":[],\"eval_depth\":6,\"prediction_depth\":8}"
```

`/live/evaluate` is stateless. Stockfish evaluation runs for every submitted FEN and returns
`stockfish_eval_cp_white_pov` plus a normalized `stockfish_bar`. PlyShock model prediction only
appears when the submitted position is at a trained checkpoint move: 15, 20, 25, 30, or 35.
Before those checkpoints, and between them, `plyshock` is `null`.
