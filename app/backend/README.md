# PlyShock Demo Backend

Run the FastAPI backend from the repository root:

```bash
uv run uvicorn app.backend.main:app --reload
```

Open Swagger docs:

http://127.0.0.1:8000/docs

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
