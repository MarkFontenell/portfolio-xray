"""Tests for Portfolio X-Ray scenario engine (module 2).

Place this file at tests/test_scenarios.py.
Run from the repository root: python -m pytest tests/test_scenarios.py -v

These tests cover the agreed specification, not future margin trading or
market-data integrations. The calculations are approximate risk scenarios,
not exact bond pricing.
"""

from dataclasses import FrozenInstanceError
import math

import pytest

from portfolio_xray.models.portfolio import Asset, AssetType, Portfolio
from portfolio_xray.core.scenarios import (
    AssetScenarioResult,
    PortfolioScenarioResult,
    simulate_stock,
    simulate_bond,
    simulate_asset,
    calculate_pnl,
    simulate_portfolio,
)


def make_asset(
    ticker: str = "SBER",
    value: float = 50_000.0,
    *,
    asset_type: AssetType = AssetType.STOCK,
    duration: float = 0.0,
) -> Asset:
    return Asset(
        ticker=ticker,
        name=ticker,
        value=value,
        asset_type=asset_type,
        duration=duration,
    )


def sample_portfolio() -> Portfolio:
    return Portfolio(assets=[
        make_asset("SBER", 50_000.0),
        make_asset("OFZ", 35_000.0, asset_type=AssetType.BOND, duration=3.2),
        make_asset("RUB", 15_000.0, asset_type=AssetType.CASH),
    ])


# 1. Stocks: ordinary unleveraged long positions

@pytest.mark.parametrize("value, change_percent, expected", [
    (50_000.0, -15.0, 42_500.0),
    (50_000.0, 20.0, 60_000.0),
    (50_000.0, 0.0, 50_000.0),
    (50_000.0, -100.0, 0.0),
    (0.0, 50.0, 0.0),
    (0.0, -100.0, 0.0),
])
def test_simulate_stock_valid(value, change_percent, expected):
    assert simulate_stock(value, change_percent) == pytest.approx(expected)


@pytest.mark.parametrize("value, change_percent", [
    (-1.0, 10.0),
    (50_000.0, -100.00001),
    (50_000.0, -120.0),
    (math.nan, 10.0),
    (math.inf, 10.0),
    (-math.inf, 10.0),
    (50_000.0, math.nan),
    (50_000.0, math.inf),
    (50_000.0, -math.inf),
    (1e308, 100.0),  # finite inputs; infinite result
])
def test_simulate_stock_invalid(value, change_percent):
    with pytest.raises(ValueError):
        simulate_stock(value, change_percent)


# 2. Bonds: linear modified-duration approximation

@pytest.mark.parametrize("value, duration, yield_change_pp, expected", [
    (35_000.0, 3.2, 2.0, 32_760.0),
    (35_000.0, 3.2, -2.0, 37_240.0),
    (35_000.0, 3.2, 0.0, 35_000.0),
    (35_000.0, 0.0, 2.0, 35_000.0),
    (0.0, 3.2, 2.0, 0.0),
    (10_000.0, 2.0, 50.0, 0.0),
])
def test_simulate_bond_valid(value, duration, yield_change_pp, expected):
    assert simulate_bond(value, duration, yield_change_pp) == pytest.approx(expected)


@pytest.mark.parametrize("value, duration, yield_change_pp", [
    (-1.0, 3.2, 2.0),
    (35_000.0, -1.0, 2.0),
    (math.nan, 3.2, 2.0),
    (math.inf, 3.2, 2.0),
    (35_000.0, math.nan, 2.0),
    (35_000.0, math.inf, 2.0),
    (35_000.0, 3.2, math.nan),
    (35_000.0, 3.2, math.inf),
    (35_000.0, 3.2, -math.inf),
    (35_000.0, 3.2, 100.0),  # negative modeled price
    (1e308, 1e308, -100.0),  # overflow
])
def test_simulate_bond_invalid(value, duration, yield_change_pp):
    with pytest.raises(ValueError):
        simulate_bond(value, duration, yield_change_pp)


# 3. Dispatcher: appropriate calculation for every asset type

@pytest.mark.parametrize("asset, expected", [
    (make_asset("SBER", 50_000.0), 42_500.0),
    (make_asset("OFZ", 35_000.0, asset_type=AssetType.BOND, duration=3.2), 32_760.0),
    (make_asset("RUB", 15_000.0, asset_type=AssetType.CASH), 15_000.0),
])
def test_simulate_asset_dispatch(asset, expected):
    assert simulate_asset(asset, -15.0, 2.0) == pytest.approx(expected)


@pytest.mark.parametrize("stock_change_percent, bond_yield_change_pp", [
    (-101.0, 0.0),
    (math.nan, 0.0),
    (math.inf, 0.0),
    (0.0, math.nan),
    (0.0, -math.inf),
])
def test_simulate_asset_rejects_invalid_scenario_even_for_cash(
    stock_change_percent, bond_yield_change_pp
):
    with pytest.raises(ValueError):
        simulate_asset(
            make_asset("RUB", 100.0, asset_type=AssetType.CASH),
            stock_change_percent,
            bond_yield_change_pp,
        )


def test_simulate_asset_rejects_unknown_type():
    # Runtime dataclass annotations do not enforce AssetType; dispatcher must reject.
    unknown = make_asset("???", 100.0, asset_type="unknown")
    with pytest.raises(ValueError):
        simulate_asset(unknown, 0.0, 0.0)


def test_simulate_asset_does_not_modify_asset():
    asset = make_asset("OFZ", 35_000.0, asset_type=AssetType.BOND, duration=3.2)
    before = (asset.ticker, asset.asset_type, asset.value, asset.duration)
    simulate_asset(asset, -15.0, 2.0)
    assert (asset.ticker, asset.asset_type, asset.value, asset.duration) == before


# 4. Absolute and percentage P&L

@pytest.mark.parametrize("before, after, expected_abs, expected_percent", [
    (100_000.0, 90_000.0, -10_000.0, -10.0),
    (100_000.0, 120_000.0, 20_000.0, 20.0),
    (100_000.0, 100_000.0, 0.0, 0.0),
    (100_000.0, 0.0, -100_000.0, -100.0),
    (0.0, 0.0, 0.0, 0.0),
])
def test_calculate_pnl_valid(before, after, expected_abs, expected_percent):
    actual_abs, actual_percent = calculate_pnl(before, after)
    assert actual_abs == pytest.approx(expected_abs)
    assert actual_percent == pytest.approx(expected_percent)


@pytest.mark.parametrize("before, after", [
    (0.0, 10_000.0),
    (-100.0, 50.0),
    (100.0, -50.0),
    (-100.0, -50.0),
    (math.nan, 100.0),
    (100.0, math.nan),
    (math.inf, 100.0),
    (100.0, math.inf),
    (1e-300, 1e300),  # percentage overflow, though both inputs are finite
])
def test_calculate_pnl_invalid(before, after):
    with pytest.raises(ValueError):
        calculate_pnl(before, after)


# 5. Aggregation and immutable result models

def test_simulate_portfolio_expected_scenario():
    portfolio = sample_portfolio()
    result = simulate_portfolio(portfolio, -15.0, 2.0)

    assert isinstance(result, PortfolioScenarioResult)
    assert result.original_value == pytest.approx(100_000.0)
    assert result.simulated_value == pytest.approx(90_260.0)
    assert result.pnl == pytest.approx(-9_740.0)
    assert result.pnl_percent == pytest.approx(-9.74)
    assert isinstance(result.asset_results, tuple)
    assert len(result.asset_results) == 3

    expected = [
        ("SBER", AssetType.STOCK, 50_000.0, 42_500.0, -7_500.0),
        ("OFZ", AssetType.BOND, 35_000.0, 32_760.0, -2_240.0),
        ("RUB", AssetType.CASH, 15_000.0, 15_000.0, 0.0),
    ]
    for actual, (ticker, asset_type, old, new, pnl) in zip(result.asset_results, expected):
        assert isinstance(actual, AssetScenarioResult)
        assert actual.ticker == ticker
        assert actual.asset_type == asset_type
        assert actual.original_value == pytest.approx(old)
        assert actual.simulated_value == pytest.approx(new)
        assert actual.pnl == pytest.approx(pnl)


def test_simulate_portfolio_empty():
    result = simulate_portfolio(Portfolio(), -15.0, 2.0)
    assert result.original_value == 0.0
    assert result.simulated_value == 0.0
    assert result.pnl == 0.0
    assert result.pnl_percent == 0.0
    assert result.asset_results == ()


def test_simulate_portfolio_duplicate_tickers_stay_separate_and_ordered():
    portfolio = Portfolio(assets=[
        make_asset("SBER", 100.0),
        make_asset("RUB", 50.0, asset_type=AssetType.CASH),
        make_asset("SBER", 200.0),
    ])
    result = simulate_portfolio(portfolio, 10.0, 0.0)
    assert [r.ticker for r in result.asset_results] == ["SBER", "RUB", "SBER"]
    assert [r.simulated_value for r in result.asset_results] == pytest.approx([110.0, 50.0, 220.0])
    assert result.original_value == pytest.approx(350.0)
    assert result.simulated_value == pytest.approx(380.0)
    assert result.pnl == pytest.approx(30.0)
    assert result.pnl_percent == pytest.approx(30.0 / 350.0 * 100.0)


def test_simulate_portfolio_does_not_mutate_input():
    portfolio = sample_portfolio()
    original_list = portfolio.assets
    original_assets = tuple(portfolio.assets)
    original_values = [(a.ticker, a.value, a.duration, a.asset_type) for a in portfolio.assets]
    simulate_portfolio(portfolio, -15.0, 2.0)
    assert portfolio.assets is original_list
    assert tuple(portfolio.assets) == original_assets
    assert [(a.ticker, a.value, a.duration, a.asset_type) for a in portfolio.assets] == original_values


@pytest.mark.parametrize("stock_change_percent, bond_yield_change_pp", [
    (-101.0, 0.0),
    (math.nan, 0.0),
    (math.inf, 0.0),
    (0.0, math.nan),
    (0.0, math.inf),
])
def test_simulate_portfolio_rejects_invalid_scenario_even_if_empty(
    stock_change_percent, bond_yield_change_pp
):
    with pytest.raises(ValueError):
        simulate_portfolio(Portfolio(), stock_change_percent, bond_yield_change_pp)


def test_simulate_portfolio_rejects_total_overflow():
    # Each asset's value is finite, but adding them overflows float.
    portfolio = Portfolio(assets=[
        make_asset("A", 1e308, asset_type=AssetType.CASH),
        make_asset("B", 1e308, asset_type=AssetType.CASH),
    ])
    with pytest.raises(ValueError):
        simulate_portfolio(portfolio, 0.0, 0.0)


def test_simulate_portfolio_rejects_invalid_cash_value():
    # Asset's basic model may allow NaN under the first module's limited spec;
    # Scenario Engine must reject invalid numeric input even for cash.
    portfolio = Portfolio(assets=[make_asset("RUB", math.nan, asset_type=AssetType.CASH)])
    with pytest.raises(ValueError):
        simulate_portfolio(portfolio, 0.0, 0.0)


def test_result_dataclasses_are_frozen():
    asset_result = AssetScenarioResult("SBER", AssetType.STOCK, 100.0, 90.0, -10.0)
    portfolio_result = PortfolioScenarioResult(100.0, 90.0, -10.0, -10.0, (asset_result,))
    with pytest.raises(FrozenInstanceError):
        asset_result.pnl = 0.0
    with pytest.raises(FrozenInstanceError):
        portfolio_result.pnl_percent = 0.0
    assert isinstance(portfolio_result.asset_results, tuple)
