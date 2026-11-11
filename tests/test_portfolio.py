"""Проверки Portfolio X-Ray по ТЗ первого модуля.

Запуск из корня проекта: python -m pytest -v

Текущие требования: AssetType (Enum), Asset (frozen dataclass), Portfolio,
валидация отрицательных value/duration, add_asset, total_value, get_asset_weight.

Тесты с меткой future фиксируют потенциальные улучшения, НЕ входящие в ТЗ:
отказ от NaN / +Infinity и контроль переполнения float. Они отмечены xfail.
"""

from dataclasses import FrozenInstanceError
import math
import random
import sys

import pytest

from portfolio_xray.models.portfolio import Asset, AssetType, Portfolio


def make_asset(
    ticker: str = "SBER",
    value: float = 50_000.0,
    *,
    name: str = "Сбербанк",
    asset_type: AssetType = AssetType.STOCK,
    duration: float = 0.0,
) -> Asset:
    """Фабрика тестовых активов; именованные аргументы исключают путаницу с порядком полей."""
    return Asset(
        ticker=ticker,
        name=name,
        value=value,
        asset_type=asset_type,
        duration=duration,
    )


# --- Enum и модель Asset ---

def test_asset_type_values() -> None:
    assert isinstance(AssetType.STOCK, AssetType)
    assert {item.name: item.value for item in AssetType} == {
        "STOCK": "stock",
        "BOND": "bond",
        "CASH": "cash",
    }


def test_asset_type_members_are_distinct() -> None:
    """Different enum values must never compare equal."""
    assert AssetType.CASH != AssetType.STOCK
    assert AssetType.STOCK != AssetType.BOND
    assert AssetType.CASH != AssetType.BOND


def test_asset_type_is_hashable() -> None:
    """Enum members must remain usable as dictionary keys and set entries."""
    assert len({AssetType.CASH, AssetType.STOCK, AssetType.BOND}) == 3


def test_create_asset() -> None:
    asset = make_asset("SBER", 50_000.0, name="Сбербанк", asset_type=AssetType.STOCK, duration=2.0)
    assert asset.ticker == "SBER"
    assert asset.name == "Сбербанк"
    assert asset.value == 50_000.0
    assert asset.asset_type == AssetType.STOCK
    assert asset.duration == 2.0


def test_default_duration() -> None:
    assert make_asset().duration == 0.0


def test_asset_is_frozen() -> None:
    asset = make_asset()
    with pytest.raises(FrozenInstanceError):
        asset.value = 123.0  # type: ignore[misc]


@pytest.mark.parametrize("value", [-1.0, -0.0001, -sys.float_info.max, -math.nextafter(0.0, 1.0), -math.inf])
def test_negative_value(value: float) -> None:
    with pytest.raises(ValueError):
        make_asset(value=value)


@pytest.mark.parametrize("duration", [-1.0, -0.0001, -sys.float_info.max, -math.nextafter(0.0, 1.0), -math.inf])
def test_negative_duration(duration: float) -> None:
    with pytest.raises(ValueError):
        make_asset(duration=duration)


@pytest.mark.parametrize("value", [0.0, -0.0, math.nextafter(0.0, 1.0), sys.float_info.min, 1.0, sys.float_info.max])
def test_valid_boundary_values(value: float) -> None:
    asset = make_asset(value=value)
    assert asset.value == value


@pytest.mark.parametrize("duration", [0.0, -0.0, math.nextafter(0.0, 1.0), sys.float_info.min, sys.float_info.max])
def test_valid_boundary_durations(duration: float) -> None:
    asset = make_asset(duration=duration)
    assert asset.duration == duration


@pytest.mark.parametrize("length", [0, 1, 255, 4096, 10_000])
def test_ticker_string_lengths(length: int) -> None:
    """В ТЗ нет ограничения длины/непустоты строки: строки этих длин разрешены."""
    ticker = "T" * length
    asset = make_asset(ticker=ticker)
    assert asset.ticker == ticker
    assert len(asset.ticker) == length
    assert Portfolio([asset]).get_asset_weight(ticker) == pytest.approx(100.0)


@pytest.mark.parametrize("name", ["", "A", "Сбербанк", "Акции 🚀", "Имя " * 2000])
def test_name_unicode_empty_and_long(name: str) -> None:
    asset = make_asset(name=name)
    assert asset.name == name


# --- Portfolio и расчёты ---

def test_empty_portfolio() -> None:
    portfolio = Portfolio()
    assert portfolio.assets == []
    assert portfolio.total_value() == pytest.approx(0.0)


def test_portfolios_do_not_share_lists() -> None:
    first = Portfolio()
    second = Portfolio()
    first.add_asset(make_asset())
    assert len(first.assets) == 1
    assert second.assets == []
    assert first.assets is not second.assets


def test_portfolio_accepts_initial_assets() -> None:
    asset = make_asset()
    portfolio = Portfolio(assets=[asset])
    assert portfolio.assets == [asset]


def test_add_asset() -> None:
    portfolio = Portfolio()
    asset = make_asset()
    result = portfolio.add_asset(asset)
    assert result is None
    assert portfolio.assets == [asset]
    assert portfolio.assets[0] is asset


def test_add_asset_preserves_order() -> None:
    portfolio = Portfolio()
    sber = make_asset("SBER", 50_000)
    rub = make_asset("RUB", 15_000, asset_type=AssetType.CASH)
    portfolio.add_asset(sber)
    portfolio.add_asset(rub)
    assert portfolio.assets == [sber, rub]


def test_total_value() -> None:
    portfolio = Portfolio([
        make_asset("SBER", 50_000),
        make_asset("OFZ", 35_000, asset_type=AssetType.BOND, duration=3.2),
    ])
    assert portfolio.total_value() == pytest.approx(85_000.0)


def test_total_value_with_cash_and_zeros() -> None:
    portfolio = Portfolio([
        make_asset("SBER", 0),
        make_asset("RUB", 15_000, asset_type=AssetType.CASH),
        make_asset("OFZ", 0, asset_type=AssetType.BOND),
    ])
    assert portfolio.total_value() == pytest.approx(15_000.0)


def test_total_value_with_fractions() -> None:
    portfolio = Portfolio([make_asset("A", 0.1), make_asset("B", 0.2)])
    assert portfolio.total_value() == pytest.approx(0.3)


def test_total_value_with_max_float() -> None:
    portfolio = Portfolio([make_asset("MAX", sys.float_info.max)])
    assert portfolio.total_value() == sys.float_info.max
    assert portfolio.get_asset_weight("MAX") == pytest.approx(100.0)


def test_total_value_with_min_positive_float() -> None:
    smallest_positive = math.nextafter(0.0, 1.0)
    portfolio = Portfolio([make_asset("MIN", smallest_positive)])
    assert portfolio.total_value() == smallest_positive
    assert portfolio.get_asset_weight("MIN") == pytest.approx(100.0)


def test_asset_weight() -> None:
    portfolio = Portfolio([make_asset("SBER", 50_000), make_asset("RUB", 50_000, asset_type=AssetType.CASH)])
    assert portfolio.get_asset_weight("SBER") == pytest.approx(50.0)


def test_unknown_ticker() -> None:
    portfolio = Portfolio([make_asset("SBER", 50_000)])
    with pytest.raises(ValueError):
        portfolio.get_asset_weight("AAPL")


def test_unknown_ticker_in_empty_portfolio() -> None:
    with pytest.raises(ValueError):
        Portfolio().get_asset_weight("SBER")


def test_zero_portfolio() -> None:
    portfolio = Portfolio([make_asset("SBER", 0), make_asset("RUB", 0, asset_type=AssetType.CASH)])
    assert portfolio.get_asset_weight("SBER") == pytest.approx(0.0)


def test_zero_valued_asset_in_nonzero_portfolio() -> None:
    portfolio = Portfolio([make_asset("SBER", 0), make_asset("RUB", 50_000, asset_type=AssetType.CASH)])
    assert portfolio.get_asset_weight("SBER") == pytest.approx(0.0)


def test_duplicate_tickers() -> None:
    portfolio = Portfolio([make_asset("SBER", 20_000), make_asset("SBER", 30_000), make_asset("RUB", 50_000)])
    assert portfolio.get_asset_weight("SBER") == pytest.approx(50.0)


def test_duplicate_ticker_with_zero_value() -> None:
    portfolio = Portfolio([make_asset("SBER", 0), make_asset("SBER", 30_000), make_asset("RUB", 70_000)])
    assert portfolio.get_asset_weight("SBER") == pytest.approx(30.0)


def test_ticker_case_sensitive() -> None:
    portfolio = Portfolio([make_asset("SBER", 20_000), make_asset("sber", 80_000)])
    assert portfolio.get_asset_weight("SBER") == pytest.approx(20.0)
    assert portfolio.get_asset_weight("sber") == pytest.approx(80.0)


def test_ticker_compared_by_ticker_not_name() -> None:
    portfolio = Portfolio([make_asset("AAA", 10_000, name="Same"), make_asset("BBB", 90_000, name="Same")])
    assert portfolio.get_asset_weight("AAA") == pytest.approx(10.0)


def test_weight_of_one_asset_is_100_percent() -> None:
    assert Portfolio([make_asset("ONLY", 123.45)]).get_asset_weight("ONLY") == pytest.approx(100.0)


def test_large_portfolio_10k_assets() -> None:
    portfolio = Portfolio()
    for i in range(10_000):
        portfolio.add_asset(make_asset(f"T{i}", 0.5))
    assert portfolio.total_value() == pytest.approx(5000.0)
    assert portfolio.get_asset_weight("T0") == pytest.approx(0.01)


def test_randomized_portfolio_invariants() -> None:
    """Детерминированная выборка: 100 портфелей, сумма долей всех уникальных тикеров ≈ 100%."""
    rng = random.Random(20261103)
    for _ in range(100):
        count = rng.randint(1, 30)
        assets = [make_asset(f"T{rng.randint(1, 8)}", rng.uniform(0.01, 100_000)) for _ in range(count)]
        portfolio = Portfolio(assets)
        expected_total = sum(asset.value for asset in assets)
        assert portfolio.total_value() == pytest.approx(expected_total)
        weights_sum = sum(portfolio.get_asset_weight(ticker) for ticker in {a.ticker for a in assets})
        assert weights_sum == pytest.approx(100.0)


# --- Необязательные улучшения: НЕ входили в исходное ТЗ ---
# xfail = известное ограничение текущей модели; не является провалом обязательных проверок.

@pytest.mark.xfail(strict=True, reason="В исходном ТЗ проверка NaN не требовалась")
def test_future_reject_nan() -> None:
    with pytest.raises(ValueError):
        make_asset(value=float("nan"))


@pytest.mark.xfail(strict=True, reason="В исходном ТЗ проверка +Infinity не требовалась")
def test_future_reject_positive_infinity() -> None:
    with pytest.raises(ValueError):
        make_asset(value=float("inf"))


@pytest.mark.xfail(strict=True, reason="В исходном ТЗ защита от переполнения суммы float не требовалась")
def test_future_reject_float_overflow() -> None:
    portfolio = Portfolio([make_asset("A", sys.float_info.max), make_asset("B", sys.float_info.max)])
    assert math.isfinite(portfolio.total_value())
