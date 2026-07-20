import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

RESULT_FILE = BASE_DIR / "data" / "analysis_results.json"
STRATEGY_FILE = BASE_DIR / "data" / "strategy_results.json"


def safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_analysis_results() -> list[dict]:
    if not RESULT_FILE.exists():
        raise FileNotFoundError(
            f"분석 결과 파일을 찾을 수 없습니다: {RESULT_FILE}"
        )

    with RESULT_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "analysis_results.json의 형식이 리스트가 아닙니다."
        )

    return data


def get_recommended_pick(
    game: dict,
) -> tuple[str, float, float]:
    selections = {
        "홈승": {
            "probability": safe_float(game.get("home_prob")),
            "odds": safe_float(game.get("home_odds")),
        },
        "무승부": {
            "probability": safe_float(game.get("draw_prob")),
            "odds": safe_float(game.get("draw_odds")),
        },
        "원정승": {
            "probability": safe_float(game.get("away_prob")),
            "odds": safe_float(game.get("away_odds")),
        },
    }

    recommended_pick = max(
        selections,
        key=lambda pick: selections[pick]["probability"],
    )

    recommended_probability = selections[
        recommended_pick
    ]["probability"]

    recommended_odds = selections[
        recommended_pick
    ]["odds"]

    return (
        recommended_pick,
        recommended_probability,
        recommended_odds,
    )


def calculate_ev(
    probability: float,
    odds: float,
) -> float:
    if probability <= 0 or odds <= 0:
        return -100.0

    decimal_probability = probability / 100.0

    ev = (
        decimal_probability * odds
        - 1
    ) * 100

    return round(ev, 2)


def calculate_titan_score(
    game: dict,
    recommended_probability: float,
    ev: float,
) -> float:
    probabilities = [
        safe_float(game.get("home_prob")),
        safe_float(game.get("draw_prob")),
        safe_float(game.get("away_prob")),
    ]

    sorted_probabilities = sorted(
        probabilities,
        reverse=True,
    )

    highest_probability = sorted_probabilities[0]
    second_probability = sorted_probabilities[1]

    probability_gap = (
        highest_probability
        - second_probability
    )

    positive_ev = max(ev, 0)
    negative_ev = min(ev, 0)

    titan_score = (
        recommended_probability * 0.50
        + probability_gap * 0.25
        + positive_ev * 0.25
        + negative_ev * 0.10
    )

    return round(titan_score, 2)


def analyze_games(
    results: list[dict],
) -> list[dict]:
    scored_games = []

    for game in results:
        (
            recommended_pick,
            recommended_probability,
            recommended_odds,
        ) = get_recommended_pick(game)

        ev = calculate_ev(
            probability=recommended_probability,
            odds=recommended_odds,
        )

        titan_score = calculate_titan_score(
            game=game,
            recommended_probability=recommended_probability,
            ev=ev,
        )

        scored_game = game.copy()

        scored_game["recommended_pick"] = (
            recommended_pick
        )

        scored_game["recommended_probability"] = round(
            recommended_probability,
            2,
        )

        scored_game["recommended_odds"] = round(
            recommended_odds,
            2,
        )

        scored_game["ev"] = ev
        scored_game["titan_score"] = titan_score

        scored_games.append(scored_game)

    scored_games.sort(
        key=lambda game: game["titan_score"],
        reverse=True,
    )

    return scored_games


def save_strategy_results(
    scored_games: list[dict],
) -> None:
    STRATEGY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with STRATEGY_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            scored_games,
            file,
            ensure_ascii=False,
            indent=4,
        )


def print_top_games(
    scored_games: list[dict],
    limit: int = 10,
) -> None:
    print()
    print("===== TITAN SCORE TOP 10 =====")

    for rank, game in enumerate(
        scored_games[:limit],
        start=1,
    ):
        home_team = game.get(
            "home_team",
            "홈팀 정보 없음",
        )

        away_team = game.get(
            "away_team",
            "원정팀 정보 없음",
        )

        print()
        print(f"{rank}위")
        print(
            f"경기: {home_team} vs {away_team}"
        )
        print(
            f"추천: {game['recommended_pick']}"
        )
        print(
            f"추천 확률: "
            f"{game['recommended_probability']:.2f}%"
        )
        print(
            f"추천 배당: "
            f"{game['recommended_odds']:.2f}"
        )
        print(
            f"EV: {game['ev']:.2f}%"
        )
        print(
            f"TITAN SCORE: "
            f"{game['titan_score']:.2f}"
        )


def main() -> None:
    results = load_analysis_results()

    scored_games = analyze_games(results)

    save_strategy_results(scored_games)

    print(
        f"전략 분석 완료: {len(scored_games)}경기"
    )

    print(
        f"전략 결과 저장 완료: {STRATEGY_FILE}"
    )

    print_top_games(scored_games)


if __name__ == "__main__":
    main()