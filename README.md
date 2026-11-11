# Portfolio X-Ray

**Интерактивный симулятор рисков инвестиционного портфеля**  
*Investment portfolio risk analysis & stress-testing — Python prototype*

> **Статус:** реализованы модели портфеля и движок стресс-сценариев (Scenario Engine); расчёты протестированы. Веб-интерфейс, получение рыночных данных и AI-интеграции пока не реализованы.

**Portfolio X-Ray** — учебный FinTech-проект, который мы развиваем как прототип для хакатона. Его цель — помочь инвестору ответить на вопрос **«Что произойдёт с моим портфелем, если рынок изменится?»** с помощью прозрачных расчётов, наглядной визуализации и, в перспективе, AI-объяснений.

🔗 **Репозиторий:** https://github.com/MarkFontenell/portfolio-xray

---

## Идея продукта

В текущей Python-версии можно создать портфель вручную и смоделировать рыночные события, например:

- стоимость акций снизилась на **15%**;
- доходности облигаций выросли на **2 процентных пункта**;
Расчётный движок уже возвращает новую стоимость портфеля, общий P&L и вклад каждого актива. **В планах:** анализ концентрации рисков, загрузка реальных позиций, интерактивный интерфейс и объяснения результатов.

**Принцип:** финансовые расчёты выполняет Python-код; языковая модель, если будет подключена, объясняет результаты, а не придумывает числа.

## Что уже реализовано

- [x] `AssetType` — типы активов: акции, облигации, деньги (`Enum`).
- [x] `Asset` — неизменяемая модель позиции (`@dataclass(frozen=True)`).
- [x] Валидация отрицательных `value` и `duration`.
- [x] `Portfolio` — коллекция активов с независимым списком у каждого экземпляра.
- [x] `add_asset()` — добавление позиции.
- [x] `total_value()` — сумма стоимостей всех позиций.
- [x] `get_asset_weight(ticker)` — доля тикера в портфеле; учитывает повторяющиеся тикеры и нулевой портфель.
- [x] `simulate_stock()` — переоценка акций при процентном изменении стоимости (без плеча).
- [x] `simulate_bond()` — приближённая переоценка облигаций через модифицированную дюрацию и изменение доходности в процентных пунктах.
- [x] `simulate_asset()` — выбор расчёта по типу актива (`STOCK`, `BOND`, `CASH`).
- [x] `calculate_pnl()` — абсолютная и процентная прибыль/убыток.
- [x] `simulate_portfolio()` — стресс-тест всего портфеля с результатами по каждой позиции.
- [x] `AssetScenarioResult` и `PortfolioScenarioResult` — неизменяемые модели результатов.
- [x] Автоматические тесты на `pytest` для доменных моделей и сценарного движка.

**Последний подтверждённый локальный запуск (11 ноября 2026):** **126 passed, 3 xfailed** (129 тестовых случаев, Python 3.14). `XFAIL` — ожидаемые непройденные тесты на дополнительную защиту моделей от `NaN`, `+Infinity` и переполнения суммы `float`; это не ошибки прогона. CI в GitHub Actions пока не настроен.

## Быстрое демо — уже работает

Для текущей версии не нужны API-ключи и доступ к брокерскому счёту.

Из корня проекта открой Python-консоль и выполни:

```python
from portfolio_xray.models.portfolio import Asset, AssetType, Portfolio
from portfolio_xray.core.scenarios import simulate_portfolio

portfolio = Portfolio()
portfolio.add_asset(Asset(
    ticker="SBER", name="Сбербанк", value=50_000.0,
    asset_type=AssetType.STOCK,
))
portfolio.add_asset(Asset(
    ticker="OFZ", name="ОФЗ", value=35_000.0,
    asset_type=AssetType.BOND, duration=3.2,
))
portfolio.add_asset(Asset(
    ticker="RUB", name="Рубли", value=15_000.0,
    asset_type=AssetType.CASH,
))

print(f"Стоимость: {portfolio.total_value():,.0f} ₽")
print(f"Доля SBER: {portfolio.get_asset_weight('SBER'):.1f}%")
print(f"Доля OFZ: {portfolio.get_asset_weight('OFZ'):.1f}%")

# Стресс-сценарий: акции -15%, доходность облигаций +2 п. п.
scenario = simulate_portfolio(
    portfolio,
    stock_change_percent=-15.0,
    bond_yield_change_pp=2.0,
)
print(f"После сценария: {scenario.simulated_value:,.0f} ₽")
print(f"PnL: {scenario.pnl:,.0f} ₽ ({scenario.pnl_percent:.2f}%)")
for item in scenario.asset_results:
    print(f"{item.ticker}: {item.original_value:,.0f} → {item.simulated_value:,.0f} ₽; PnL {item.pnl:,.0f} ₽")
```

Ожидаемый результат:

```text
Стоимость: 100,000 ₽
Доля SBER: 50.0%
Доля OFZ: 35.0%
После сценария: 90,260 ₽
PnL: -9,740 ₽ (-9.74%)
SBER: 50,000 → 42,500 ₽; PnL -7,500 ₽
OFZ: 35,000 → 32,760 ₽; PnL -2,240 ₽
RUB: 15,000 → 15,000 ₽; PnL 0 ₽
```

> `value` означает **полную стоимость позиции**, а не цену одной акции. Доходность облигаций задаётся в **процентных пунктах**, а `duration` интерпретируется как **модифицированная дюрация**. Данные вводятся вручную; рыночные котировки пока не загружаются.

## Локальный запуск и тестирование

**Требования:** Python 3.11+ (проверялось в Python 3.14), Git. Для тестов — `pytest`.

```powershell
# Клонирование
git clone https://github.com/MarkFontenell/portfolio-xray.git
cd portfolio-xray

# Виртуальное окружение (Windows / PowerShell)
py -m venv .venv
.\.venv\Scripts\Activate.ps1

# Установка pytest и запуск всех тестов
python -m pip install pytest
python -m pytest tests/ -v
```

Для ручного демо запусти приведённый выше код из Python-консоли, открытой из корня проекта, или сохрани его в отдельный скрипт.

*Веб-приложения пока нет: текущий результат запускается через Python и тесты.*

## Архитектура

```text
portfolio-xray/
├── portfolio_xray/
│   ├── models/
│   │   └── portfolio.py       # AssetType, Asset, Portfolio — реализовано
│   ├── core/
│   │   └── scenarios.py       # Scenario Engine — реализован
│   ├── services/              # Сервисный слой — план
│   ├── ui/                    # Визуальный интерфейс — план
│   ├── integrations/
│   │   └── t_invest_mcp.py    # Заготовка интеграции, не подключена
│   └── ai/
│       ├── agent.py           # Заготовка AI-агента
│       └── explainer.py       # Заготовка объяснений
├── tests/
│   ├── test_portfolio.py     # Тесты доменных моделей
│   └── test_scenarios.py     # Тесты Scenario Engine
├── .gitignore
└── README.md
```

**Архитектурное решение:** расчётная логика отделяется от UI и внешних API. Это позволит подключить Streamlit, FastAPI или брокерские данные без переписывания доменных моделей.

## Технологии

| Используются сейчас | Планируются |
|---|---|
| Python 3, `dataclasses`, `Enum`, `math`, Git/GitHub, Pytest | Pandas, Streamlit, T-Invest MCP, LLM API, FastAPI (при необходимости), GitHub Actions |

## Roadmap

- [x] **Этап 1. Domain Models:** активы, портфель, валидация, тесты.
- [x] **Этап 2. Scenario Engine:** переоценка акций и облигаций, учёт денежных средств, P&L и результаты по позициям; 69 сценарных тестов пройдены.
- [ ] **Этап 3. Risk Analytics:** концентрация портфеля, доли классов активов, дополнительные риск-метрики.
- [ ] **Этап 4. Dashboard:** интерактивные сценарии, графики, доли активов.
- [ ] **Этап 5. T-Invest MCP:** получение доступных данных портфеля и инструментов (при наличии авторизации и разрешений).
- [ ] **Этап 6. AI Explainability:** объяснения рисков на основе проверенных расчётов.
- [ ] **Этап 7. MVP и CI:** автоматический запуск тестов в GitHub Actions, демонстрационный сценарий для хакатона.

## Ограничения

Это **учебный прототип**, а не сервис инвестиционных рекомендаций. Сценарии «что, если» не являются прогнозом доходности. Сейчас один процентный шок применяется ко всем акциям, облигации пересчитываются по **линейному приближению модифицированной дюрации** (без учёта купонов, выпуклости и кредитных спредов), а денежные средства не переоцениваются. Не учитываются торговые издержки, налоги, валютные курсы, плечо и короткие позиции. Для денежных расчётов в реальной системе потребуется более строгая обработка точности чисел, например `Decimal`.

---

### English summary

**Portfolio X-Ray** is a Python-based educational investment portfolio risk and stress-testing prototype. The implemented domain models support asset types, position values and portfolio weights. The Scenario Engine models stock percentage shocks, approximate bond repricing via modified duration, cash positions, and portfolio-level/asset-level P&L. The latest local test run reported **126 passed, 3 expected failures**. Planned features include risk analytics, an interactive dashboard, T-Invest MCP integration and explainable AI summaries. **Live market data, trading, the dashboard and AI features are not implemented.**
