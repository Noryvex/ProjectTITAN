import requests

from backend.models.event import SportEvent


class PinnacleScraper:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    def fetch_events(self) -> list[SportEvent]:
        response = requests.get(
            self.base_url,
            timeout=10,
        )

        print(f"피나클 응답 코드: {response.status_code}")
        print(response.text[:500])

        return []


if __name__ == "__main__":
    scraper = PinnacleScraper(
        base_url="https://www.pinnacle.com"
    )

    events = scraper.fetch_events()

    print("===== 피나클 수집기 테스트 =====")
    print(f"수집된 경기 수: {len(events)}")