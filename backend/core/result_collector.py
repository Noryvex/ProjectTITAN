import html
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "backend" / "data"
RESULTS_PATH = DATA_DIR / "match_results.json"


def fetch_result_script(target_date: str) -> str:
    url = (
        "https://data.7mkr2.com/result/"
        f"{target_date}/index_kr.js"
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/150.0.0.0 Safari/537.36"
        ),
        "Referer": "https://data.7mkr2.com/result/",
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=20,
    )
    response.raise_for_status()
    response.encoding = response.apparent_encoding

    return response.text


def extract_array_content(
    text: str,
    variable_name: str,
) -> str:
    pattern = (
        rf"(?:var\s+)?{re.escape(variable_name)}"
        rf"\s*=\s*\[(.*?)\]\s*;"
    )

    match = re.search(
        pattern,
        text,
        re.DOTALL,
    )

    if not match:
        raise ValueError(
            f"{variable_name} 배열을 찾지 못했습니다."
        )

    return match.group(1)


def split_js_array(content: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []

    quote: str | None = None
    escaped = False

    for character in content:
        if escaped:
            current.append(character)
            escaped = False
            continue

        if character == "\\":
            current.append(character)
            escaped = True
            continue

        if quote:
            current.append(character)

            if character == quote:
                quote = None

            continue

        if character in ("'", '"'):
            quote = character
            current.append(character)
            continue

        if character == ",":
            items.append("".join(current).strip())
            current = []
            continue

        current.append(character)

    final_item = "".join(current).strip()

    if final_item:
        items.append(final_item)

    return items


def decode_js_string(value: str) -> str:
    value = value.strip()

    if (
        len(value) >= 2
        and value[0] in ("'", '"')
        and value[-1] == value[0]
    ):
        value = value[1:-1]

    replacements = {
        r"\'": "'",
        r"\"": '"',
        r"\/": "/",
        r"\n": " ",
        r"\r": " ",
        r"\t": " ",
        r"\\": "\\",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    return value


def parse_js_array(
    text: str,
    variable_name: str,
) -> list[str]:
    content = extract_array_content(
        text,
        variable_name,
    )

    return [
        decode_js_string(item)
        for item in split_js_array(content)
    ]


def parse_number_array(
    text: str,
    variable_name: str,
) -> list[int]:
    raw_values = parse_js_array(
        text,
        variable_name,
    )

    values: list[int] = []

    for raw_value in raw_values:
        value = raw_value.strip()

        if value == "":
            raise ValueError(
                f"{variable_name} 배열에 빈 숫자 값이 있습니다."
            )

        try:
            values.append(int(float(value)))
        except ValueError as error:
            raise ValueError(
                f"{variable_name} 숫자 변환 실패: {value}"
            ) from error

    return values


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    cleaned = str(value)

    cleaned = re.sub(
        r"<script.*?</script>",
        "",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )

    cleaned = re.sub(
        r"<style.*?</style>",
        "",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )

    cleaned = re.sub(
        r"<[^>]+>",
        "",
        cleaned,
    )

    cleaned = html.unescape(cleaned)
    cleaned = cleaned.replace("\xa0", " ")

    cleaned = re.sub(
        r"\s+",
        " ",
        cleaned,
    )

    return cleaned.strip()


def normalize_match_time(
    target_date: str,
    raw_time: str,
) -> str:
    cleaned_time = clean_text(raw_time)

    if not cleaned_time:
        return ""

    comma_match = re.fullmatch(
        r"(\d{4}),(\d{1,2}),(\d{1,2}),"
        r"(\d{1,2}),(\d{1,2}),(\d{1,2})",
        cleaned_time,
    )

    if comma_match:
        year, month, day, hour, minute, second = map(
            int,
            comma_match.groups(),
        )

        parsed = datetime(
            year,
            month,
            day,
            hour,
            minute,
            second,
        )

        return parsed.strftime("%Y-%m-%d %H:%M:%S")

    full_datetime_patterns = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
    )

    for pattern in full_datetime_patterns:
        try:
            parsed = datetime.strptime(
                cleaned_time,
                pattern,
            )

            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass

    time_patterns = (
        "%H:%M:%S",
        "%H:%M",
    )

    for pattern in time_patterns:
        try:
            parsed = datetime.strptime(
                cleaned_time,
                pattern,
            )

            return (
                f"{target_date} "
                f"{parsed.strftime('%H:%M:%S')}"
            )
        except ValueError:
            pass
        
    return cleaned_time

def determine_result(
    home_score: int,
    away_score: int,
) -> str:
    if home_score > away_score:
        return "HOME"

    if home_score < away_score:
        return "AWAY"

    return "DRAW"


def load_existing_results() -> dict[str, dict]:
    if not RESULTS_PATH.exists():
        return {}

    with open(
        RESULTS_PATH,
        "r",
        encoding="utf-8",
    ) as file:
        results = json.load(file)

    if not isinstance(results, list):
        raise ValueError(
            "match_results.json 형식이 올바르지 않습니다."
        )

    return {
        str(result["match_id"]): result
        for result in results
        if result.get("match_id") is not None
    }


def validate_array_lengths(
    arrays: dict[str, list],
) -> None:
    lengths = {
        name: len(values)
        for name, values in arrays.items()
    }

    if len(set(lengths.values())) != 1:
        length_text = ", ".join(
            f"{name}={length}"
            for name, length in lengths.items()
        )

        raise ValueError(
            "결과 배열 길이가 서로 다릅니다: "
            f"{length_text}"
        )


def collect_results(
    target_date: str,
) -> tuple[list[dict], int]:
    script = fetch_result_script(target_date)

    match_ids = parse_number_array(
        script,
        "live_bh_Arr",
    )

    home_scores = parse_number_array(
        script,
        "live_a_Arr",
    )

    away_scores = parse_number_array(
        script,
        "live_b_Arr",
    )

    home_teams = parse_js_array(
        script,
        "Team_A_Arr",
    )

    away_teams = parse_js_array(
        script,
        "Team_B_Arr",
    )

    leagues = parse_js_array(
        script,
        "Match_name_Arr",
    )

    start_times = parse_js_array(
        script,
        "Start_time_Arr",
    )

    arrays = {
        "live_bh_Arr": match_ids,
        "live_a_Arr": home_scores,
        "live_b_Arr": away_scores,
        "Team_A_Arr": home_teams,
        "Team_B_Arr": away_teams,
        "Match_name_Arr": leagues,
        "Start_time_Arr": start_times,
    }

    validate_array_lengths(arrays)

    existing_results = load_existing_results()
    collected_at = datetime.now().isoformat(
        timespec="seconds"
    )

    collected_count = 0

    for index, match_id_value in enumerate(match_ids):
        match_id = str(match_id_value)

        result_data = {
            "match_id": match_id,
            "match_date": target_date,
            "match_time": normalize_match_time(
                target_date,
                start_times[index],
            ),
            "league": clean_text(leagues[index]),
            "home_team": clean_text(
                home_teams[index]
            ),
            "away_team": clean_text(
                away_teams[index]
            ),
            "home_score": home_scores[index],
            "away_score": away_scores[index],
            "result": determine_result(
                home_scores[index],
                away_scores[index],
            ),
            "status": "FINISHED",
            "collected_at": collected_at,
        }

        existing_results[match_id] = result_data
        collected_count += 1

    sorted_results = sorted(
        existing_results.values(),
        key=lambda item: (
            item.get("match_date", ""),
            item.get("match_time", ""),
            item.get("match_id", ""),
        ),
    )

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        RESULTS_PATH,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            sorted_results,
            file,
            ensure_ascii=False,
            indent=4,
        )

    return sorted_results, collected_count


def main() -> None:
    target_date = input(
        "결과 날짜를 입력하세요 "
        "(예: 2026-07-20): "
    ).strip()

    if not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}",
        target_date,
    ):
        print("날짜 형식이 올바르지 않습니다.")
        print("예시: 2026-07-20")
        return

    try:
        datetime.strptime(
            target_date,
            "%Y-%m-%d",
        )
    except ValueError:
        print("존재하지 않는 날짜입니다.")
        return

    try:
        results, collected_count = collect_results(
            target_date
        )
    except requests.RequestException as error:
        print("7M 결과 데이터 요청 실패:")
        print(error)
        return
    except (
        ValueError,
        json.JSONDecodeError,
        OSError,
    ) as error:
        print("결과 처리 실패:")
        print(error)
        return

    print()
    print("===== 결과 수집 완료 =====")
    print("이번 수집 결과 수:", collected_count)
    print("전체 저장 결과 수:", len(results))
    print("저장 위치:", RESULTS_PATH)

    today_results = [
        result
        for result in results
        if result.get("match_date") == target_date
    ]

    if today_results:
        print()
        print("첫 번째 결과:")
        print(
            json.dumps(
                today_results[0],
                ensure_ascii=False,
                indent=4,
            )
        )


if __name__ == "__main__":
    main()