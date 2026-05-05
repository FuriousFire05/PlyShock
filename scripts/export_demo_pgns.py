from pathlib import Path

import pandas as pd


def sec_to_clk(value: object) -> str:
    total = int(float(value))
    hours = total // 3600
    minutes = (total % 3600) // 60
    seconds = total % 60
    return f"{hours}:{minutes:02d}:{seconds:02d}"


def normalize_list(value: object) -> list:
    if isinstance(value, list):
        return value
    if hasattr(value, "tolist"):
        return value.tolist()
    return list(value)


def moves_to_pgn(moves_san: list[str], clock_by_ply: list[object], result: str) -> str:
    tokens: list[str] = []

    for i, san in enumerate(moves_san):
        move_no = (i // 2) + 1
        clock = sec_to_clk(clock_by_ply[i]) if i < len(clock_by_ply) else None
        clock_comment = f" {{ [%clk {clock}] }}" if clock is not None else ""

        if i % 2 == 0:
            tokens.append(f"{move_no}. {san}{clock_comment}")
        else:
            tokens.append(f"{san}{clock_comment}")

    tokens.append(result)
    return " ".join(tokens)


def main() -> None:
    input_path = Path("research/data/interim/filtered_games_50k.parquet")
    output_dir = Path("app/backend/demo_games")
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(input_path)

    # Prefer games that reach move 35 so all demo snapshots exist.
    df = df[df["final_fullmove_number"] >= 35].head(5)

    print("selected demo games", len(df))

    for idx, (_, row) in enumerate(df.iterrows(), start=1):
        moves_san = normalize_list(row["moves_san"])
        clock_by_ply = normalize_list(row["clock_by_ply"])
        result = str(row["result"])

        headers = {
            "Event": str(row.get("event", "PlyShock Demo Game")),
            "Site": str(row.get("site", f"https://lichess.org/{row['game_id']}")),
            "Date": str(row.get("utc_date", "????.??.??")).replace("-", "."),
            "White": str(row.get("white", "White")),
            "Black": str(row.get("black", "Black")),
            "Result": result,
            "WhiteElo": str(int(row["white_elo"])),
            "BlackElo": str(int(row["black_elo"])),
            "TimeControl": str(row.get("time_control", "-")),
            "Termination": str(row.get("termination", "Normal")),
        }

        header_text = "\n".join(f'[{key} "{value}"]' for key, value in headers.items())
        moves_text = moves_to_pgn(moves_san, clock_by_ply, result)

        out_path = output_dir / f"demo_game_{idx}.pgn"
        out_path.write_text(f"{header_text}\n\n{moves_text}\n", encoding="utf-8")

        print(
            out_path,
            "game_id=",
            row["game_id"],
            "white_elo=",
            row["white_elo"],
            "black_elo=",
            row["black_elo"],
            "result=",
            result,
            "moves=",
            row["final_fullmove_number"],
        )


if __name__ == "__main__":
    main()