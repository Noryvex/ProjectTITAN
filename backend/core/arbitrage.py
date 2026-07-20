from dataclasses import dataclass


@dataclass
class ArbitrageResult:
    total_stake: int

    stake_a: int
    stake_b: int

    payout_a: float
    payout_b: float

    profit_a: float
    profit_b: float

    worst_profit: float
    worst_roi_percent: float


def calculate_two_way_arbitrage(
    odds_a: float,
    odds_b: float,
    total_stake: int,
    betting_unit: int = 1000,
) -> ArbitrageResult:
    """
    2지선다 양방 베팅 금액과
    최악 결과 기준 순이익을 계산한다.
    """

    if odds_a <= 1:
        raise ValueError("A 배당은 1보다 커야 합니다.")

    if odds_b <= 1:
        raise ValueError("B 배당은 1보다 커야 합니다.")

    if total_stake <= 0:
        raise ValueError("총 베팅 금액은 0보다 커야 합니다.")

    if betting_unit <= 0:
        raise ValueError("베팅 단위는 0보다 커야 합니다.")

    if total_stake < betting_unit * 2:
        raise ValueError(
            "총 베팅 금액이 베팅 단위에 비해 너무 작습니다."
        )

    if total_stake % betting_unit != 0:
        raise ValueError(
            "총 베팅 금액은 베팅 단위로 나누어떨어져야 합니다."
        )

    implied_probability_sum = (1 / odds_a) + (1 / odds_b)

    if implied_probability_sum >= 1:
        raise ValueError(
            "양방 수익이 발생하지 않는 배당 조합입니다."
        )

    # 베팅 단위에 맞는 모든 배분을 검사해서
    # 최악 결과 기준 순이익이 가장 큰 조합을 찾는다.
    best_stake_a = 0
    best_stake_b = 0
    best_worst_profit = float("-inf")

    for candidate_stake_a in range(
        betting_unit,
        total_stake,
        betting_unit,
    ):
        candidate_stake_b = total_stake - candidate_stake_a

        if candidate_stake_b < betting_unit:
            continue

        candidate_profit_a = (
            candidate_stake_a * odds_a
        ) - total_stake

        candidate_profit_b = (
            candidate_stake_b * odds_b
        ) - total_stake

        candidate_worst_profit = min(
            candidate_profit_a,
            candidate_profit_b,
        )

        if candidate_worst_profit > best_worst_profit:
            best_worst_profit = candidate_worst_profit
            best_stake_a = candidate_stake_a
            best_stake_b = candidate_stake_b

    stake_a = best_stake_a
    stake_b = best_stake_b

    actual_total_stake = stake_a + stake_b

    payout_a = stake_a * odds_a
    payout_b = stake_b * odds_b

    profit_a = payout_a - actual_total_stake
    profit_b = payout_b - actual_total_stake

    worst_profit = min(profit_a, profit_b)

    worst_roi_percent = (
        worst_profit / actual_total_stake
    ) * 100

    return ArbitrageResult(
        total_stake=actual_total_stake,
        stake_a=stake_a,
        stake_b=stake_b,
        payout_a=payout_a,
        payout_b=payout_b,
        profit_a=profit_a,
        profit_b=profit_b,
        worst_profit=worst_profit,
        worst_roi_percent=worst_roi_percent,
    )


if __name__ == "__main__":
    result = calculate_two_way_arbitrage(
        odds_a=2.10,
        odds_b=2.05,
        total_stake=1_000_000,
        betting_unit=1_000,
    )

    print("===== 2지선다 양방 계산 결과 =====")
    print(f"실제 총 베팅액: {result.total_stake:,.0f}원")
    print(f"A 베팅액: {result.stake_a:,.0f}원")
    print(f"B 베팅액: {result.stake_b:,.0f}원")
    print()

    print(f"A 적중 시 환급액: {result.payout_a:,.0f}원")
    print(f"A 적중 시 순이익: {result.profit_a:,.0f}원")
    print()

    print(f"B 적중 시 환급액: {result.payout_b:,.0f}원")
    print(f"B 적중 시 순이익: {result.profit_b:,.0f}원")
    print()

    print(
        f"최악 결과 기준 순이익: "
        f"{result.worst_profit:,.0f}원"
    )

    print(
        f"최악 결과 기준 수익률: "
        f"{result.worst_roi_percent:.2f}%"
    )