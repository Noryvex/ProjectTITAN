import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
RESULT_FILE = BASE_DIR / "data" / "analysis_results.json"


def load_analysis_results() -> list[dict]:
    if not RESULT_FILE.exists():
        raise FileNotFoundError(
            f"분석 결과 파일을 찾을 수 없습니다: {RESULT_FILE}"
        )

    with RESULT_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("analysis_results.json의 형식이 리스트가 아닙니다.")

    return data


def calculate_titan_score(game: dict) -> float:
    home_prob = float(game.get("home_prob", 0))
    draw_prob = float(game.get("draw_prob", 0))
    away_prob = float(game.get("away_prob", 0))

    probabilities = [
        home_prob,
        draw_prob,
        away_prob,
    ]

    highest_probability = max(probabilities)
    sorted_probabilities = sorted(probabilities, reverse=True)

    probability_gap = sorted_probabilities[0] - sorted_probabilities[1]

    titan_score = (
        highest_probability * 0.7
        + probability_gap * 0.3
    )

    return round(titan_score, 2)


def get_recommended_pick(game: dict) -> tuple[str, float]:
    selections = {
        "홈승": float(game.get("home_prob", 0)),
        "무승부": float(game.get("draw_prob", 0)),
        "원정승": float(game.get("away_prob", 0)),
    }

    pick = max(selections, key=selections.get)
    probability = selections[pick]

    return pick, probability


def main() -> None:
    results = load_analysis_results()

    scored_games = []

    for game in results:
        titan_score = calculate_titan_score(game)
        recommended_pick, recommended_probability = get_recommended_pick(game)

        scored_game = game.copy()
        scored_game["titan_score"] = titan_score
        scored_game["recommended_pick"] = recommended_pick
        scored_game["recommended_probability"] = round(
            recommended_probability,
            2,
        )

        scored_games.append(scored_game)

    scored_games.sort(
        key=lambda game: game["titan_score"],
        reverse=True,
    )

    print("===== TITAN SCORE TOP 10 =====")

    for rank, game in enumerate(scored_games[:10], start=1):
        home_team = game.get("home_team", "홈팀 정보 없음")
        away_team = game.get("away_team", "원정팀 정보 없음")

        print()
        print(f"{rank}위")
        print(f"경기: {home_team} vs {away_team}")
        print(f"추천: {game['recommended_pick']}")
        print(
            f"추천 확률: "
            f"{game['recommended_probability']:.2f}%"
        )
        print(f"TITAN SCORE: {game['titan_score']:.2f}")


if __name__ == "__main__":
    main()