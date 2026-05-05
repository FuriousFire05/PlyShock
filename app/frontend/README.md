# PlyShock Frontend

Premium Next.js chess analytics demo for PlyShock.

## Run

Start the FastAPI backend from the repository root:

```bash
uv run uvicorn app.backend.main:app --reload
```

Start the frontend:

```bash
cd app/frontend
pnpm dev
```

Open http://localhost:3000.

## API Configuration

The frontend reads the backend base URL from:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

If unset, it falls back to `http://127.0.0.1:8000`. No API keys, auth, or cloud services are required.

For Docker Compose, the frontend image is built with:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

This lets browser requests from `http://localhost:3000` reach the published backend port.

## Supported Modes

- Demo Replay: select a bundled PGN from `GET /demo-games`, then load move-by-move replay data from `GET /demo-games/{game_id}/replay`.
- Paste PGN: paste a custom PGN and analyze it with `POST /analyze-pgn-replay`.
- Live Board: play legal moves on the board and evaluate the current position with `POST /live/evaluate`.

Custom PGNs must include Elo headers and clock comments for full PlyShock analysis. The backend may reject games that do not satisfy the project rules used by the trained model.

Stockfish evaluation updates every move. PlyShock prediction activates only at trained checkpoint moves and should be read as an upset probability estimate.

## Checks

```bash
pnpm lint
pnpm build
```

## Docker

From the repository root:

```bash
docker compose build
docker compose up
```

Then open:

- Frontend: http://localhost:3000
- Backend docs: http://localhost:8000/docs
