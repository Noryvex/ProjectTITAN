from dataclasses import dataclass
from typing import List


@dataclass
class Selection:
    name: str
    odds: float


@dataclass
class SportEvent:
    sport: str
    league: str

    home_team: str
    away_team: str

    market: str

    selections: List[Selection]

    source: str