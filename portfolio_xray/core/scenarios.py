import math
from dataclasses import dataclass
from portfolio_xray.models.portfolio import Asset, AssetType, Portfolio


def simulate_stock(value: float, change_percent: float) -> float:
    if value < 0:
        raise ValueError("Value cannot be negative")
    elif value == float('+inf') or value == float('-inf') or not math.isfinite(value):
        raise ValueError()
    elif change_percent < -100:
        raise ValueError()
    elif not math.isfinite(change_percent):
        raise ValueError()

    result = value * (1 + change_percent/100)

    if result == float('+inf') or result == float('-inf'):
        raise ValueError()
    return result


def simulate_bond(
    value: float,
    duration: float,
    yield_change_pp: float
) -> float:
    if value < 0:
        raise ValueError
    elif duration < 0:
        raise ValueError
    elif not math.isfinite(value) or not math.isfinite(duration) or not math.isfinite(yield_change_pp):
        raise ValueError
    result = value * (1 - duration * yield_change_pp/100)
    if result < 0 or not math.isfinite(result):
        raise ValueError
    return result

def simulate_asset(
    asset: Asset,
    stock_change_percent: float,
    bond_yield_change_pp: float
) -> float:

    if not math.isfinite(stock_change_percent) or not math.isfinite(bond_yield_change_pp) or stock_change_percent < -100:
        raise ValueError
    elif asset.asset_type == AssetType.STOCK:
        return simulate_stock(asset.value, stock_change_percent)

    elif asset.asset_type == AssetType.BOND:
        return simulate_bond(asset.value, asset.duration ,bond_yield_change_pp)

    elif asset.asset_type == AssetType.CASH:
        return asset.value

    else:
        raise ValueError

def calculate_pnl(
    before: float,
    after: float
) -> tuple[float, float]:
    if not math.isfinite(before) or not math.isfinite(after):
        raise ValueError("Values must be finite")
    elif before < 0 or after < 0:
        raise ValueError

    if before == 0:
        if after == 0:
            return 0.0, 0.0

        raise ValueError("Cannot calculate percentage from zero")

    pnl_abs = after - before
    pnl_prc = pnl_abs / before * 100

    if not math.isfinite(pnl_abs) or not math.isfinite(pnl_prc):
        raise ValueError("PnL result must be finite")

    return (pnl_abs, pnl_prc)


@dataclass(frozen=True)
class AssetScenarioResult:
    ticker : str
    asset_type : AssetType
    original_value : float
    simulated_value : float
    pnl : float

@dataclass(frozen=True)
class PortfolioScenarioResult:
    original_value : float
    simulated_value : float
    pnl : float
    pnl_percent : float
    asset_results : tuple[AssetScenarioResult, ...]

def simulate_portfolio(
    portfolio: Portfolio,
    stock_change_percent: float,
    bond_yield_change_pp: float
) -> PortfolioScenarioResult:
    if (not math.isfinite(stock_change_percent)
            or not math.isfinite(bond_yield_change_pp)
            or stock_change_percent < -100
    ):
        raise ValueError("Invalid scenario parameters")
    asset_results = []
    total_before = 0.0
    total_after = 0.0
    for asset in portfolio.assets:
        new_price = simulate_asset(asset, stock_change_percent, bond_yield_change_pp)
        total_before += asset.value
        total_after += new_price
        pnl_abs, _ = calculate_pnl(asset.value, new_price)
        asr = AssetScenarioResult(asset.ticker, asset.asset_type, asset.value, new_price, pnl_abs)
        asset_results.append(asr)
    pnl_abs, pnl_percent = calculate_pnl(total_before, total_after)
    portfolio_result = PortfolioScenarioResult(total_before, total_after, pnl_abs, pnl_percent, tuple(asset_results))
    return portfolio_result