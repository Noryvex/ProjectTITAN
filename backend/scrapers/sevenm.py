import re
import json
from pathlib import Path

# ProjectTITAN 폴더 위치
project_root = Path(__file__).resolve().parents[2]

# 저장해 둔 7M 파일 위치
html_path = project_root / "sevenm_page.html"

# 파일 존재 여부 확인
if not html_path.exists():
    print("파일을 찾을 수 없습니다:", html_path)
    raise SystemExit

# 저장된 파일 읽기
text = html_path.read_text(encoding="utf-8", errors="ignore")

# 경기 문자열 추출
matches = re.findall(r'"([^"]+)"', text)

print("경기 수:", len(matches))

# 첫 경기 확인
games = []

for match in matches:
    parts = match.split("|")

    if len(parts) < 11:
        continue

    game = {
        "match_id": parts[0],
        "match_time": parts[1],
        "league": parts[3],
        "home_team": parts[6],
        "away_team": parts[7],
        "home_odds": float(parts[8]),
        "draw_odds": float(parts[9]),
       "away_odds": float(parts[10]),
    }

    games.append(game)

print("저장된 경기 수:", len(games))
print("첫 번째 저장 결과:", games[0])

save_path = project_root / "backend" / "data" / "sevenm_games.json"

with open(save_path, "w", encoding="utf-8") as f:
    json.dump(games, f, ensure_ascii=False, indent=4)

print("저장 완료")