# PlyShock Frontend

Interactive Next.js replay lab for PlyShock.

## Run

Start the backend from the repository root:

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

If unset, it falls back to `http://127.0.0.1:8000`.

The app uses:

- `GET /health`
- `GET /demo-games`
- `GET /demo-games/{game_id}/replay`

## Checks

```bash
pnpm lint
pnpm build
```
