from pathlib import Path
import json
import urllib.error
import urllib.request

pgn_path = Path("app/backend/demo_games/demo_game_1.pgn")
url = "http://127.0.0.1:8000/analyze-pgn-replay"

payload = {
    "pgn_text": pgn_path.read_text(encoding="utf-8"),
    "eval_depth": 6,
    "prediction_depth": 8,
    "checkpoint_moves": [15, 20, 25, 30, 35],
    "max_plies": 90,
}

data = json.dumps(payload).encode("utf-8")
request = urllib.request.Request(
    url,
    data=data,
    headers={"Content-Type": "application/json"},
    method="POST",
)

try:
    with urllib.request.urlopen(request, timeout=120) as response:
        body = response.read().decode("utf-8")
        Path("custom_pgn_test.json").write_text(body, encoding="utf-8")
        parsed = json.loads(body)
        print("STATUS:", response.status)
        print("metadata:", parsed["metadata"])
        print("summary:", parsed["summary"])
        print("moves:", len(parsed["moves"]))
        print("checkpoints:", len(parsed["checkpoints"]))
except urllib.error.HTTPError as error:
    body = error.read().decode("utf-8", errors="replace")
    Path("custom_pgn_error.txt").write_text(body, encoding="utf-8")
    print("HTTP ERROR:", error.code)
    print(body[:2000])
except Exception as error:
    print("ERROR:", repr(error))