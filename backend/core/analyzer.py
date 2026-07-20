import json
from pathlib import Path


project_root = Path(__file__).resolve().parents[2]

data_path = project_root / "backend" / "data" / "sevenm_games.json"


with open(data_path, "r", encoding="utf-8") as f:
    games = json.load(f)


print("불러온 경기 수:", len(games))


results = []


for game in games:

    home_prob = 1 / game["home_odds"]
    draw_prob = 1 / game["draw_odds"]
    away_prob = 1 / game["away_odds"]

    total = home_prob + draw_prob + away_prob

    fair_home = home_prob / total
    fair_draw = draw_prob / total
    fair_away = away_prob / total


    result = { 
        
        "home_team": game["home_team"],
        "away_team": game["away_team"],
        
        "home_prob": round(fair_home * 100, 2),
        "draw_prob": round(fair_draw * 100, 2),
        "away_prob": round(fair_away * 100, 2),
        
        "home_ev": round((fair_home * game["home_odds"] - 1) * 100, 2),
        "draw_ev": round((fair_draw * game["draw_odds"] - 1) * 100, 2),
        "away_ev": round((fair_away * game["away_odds"] - 1) * 100, 2),

        "home_odds": game["home_odds"],
        "draw_odds": game["draw_odds"],
        "away_odds": game["away_odds"],
        
    }

    results.append(result)


print("분석 완료:", len(results))


print("===== 첫 번째 분석 결과 =====")
print(results[0])

import json

save_path = project_root / "backend" / "data" / "analysis_results.json"

with open(save_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=4)

print("분석 결과 저장 완료")

print("===== EV 후보 =====")

for result in results:
    if (
        result["home_ev"] > 0
        or result["draw_ev"] > 0
        or result["away_ev"] > 0
    ):
        print(result)