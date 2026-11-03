# Portfolio X-Ray

**Интерактивный симулятор рисков инвестиционного портфеля**  
*Investment portfolio risk analysis & stress-testing — work in progress*

> **Статус:** готово доменное ядро (модели активов и портфеля). Стресс-тесты, веб-интерфейс и AI-интеграции пока в разработке.

**Portfolio X-Ray** — учебный FinTech-проект, который мы развиваем как прототип для хакатона. Его цель — помочь инвестору ответить на вопрос **«Что произойдёт с моим портфелем, если рынок изменится?»** с помощью прозрачных расчётов, наглядной визуализации и, в перспективе, AI-объяснений.

🔗 **Репозиторий:** https://github.com/MarkFontenell/portfolio-xray

---

## Идея продукта

Пользователь сможет загрузить состав инвестиционного портфеля и смоделировать рыночные события, например:

- стоимость акций снизилась на **15%**;
- доходности облигаций выросли на **2 процентных пункта**;
- отдельный актив занимает слишком большую долю портфеля.

В будущей версии приложение покажет изменение общей стоимости, вклад каждого актива в прибыль или убыток, концентрацию рисков и понятное объяснение результата.

**Принцип:** финансовые расчёты выполняет Python-код; языковая модель, если будет подключена, объясняет результаты, а не придумывает числа.

## Что уже реализовано

- [x] `AssetType` — типы активов: акции, облигации, деньги (`Enum`).
- [x] `Asset` — неизменяемая модель позиции (`@dataclass(frozen=True)`).
- [x] Валидация отрицательных `value` и `duration`.
- [x] `Portfolio` — коллекция активов с независимым списком у каждого экземпляра.
- [x] `add_asset()` — добавление позиции.
- [x] `total_value()` — сумма стоимостей всех позиций.
- [x] `get_asset_weight(ticker)` — доля тикера в портфеле; учитывает повторяющиеся тикеры и нулевой портфель.
- [x] Автоматические тесты на `pytest`.

**Последний локально подтверждённый запуск:** **57 passed, 3 xfailed** (60 проверок). Три ожидаемых сбоя относятся к будущей обработке `NaN`, `Infinity` и переполнения `float`.

## Быстрое демо — уже работает

Для текущей версии не нужны API-ключи и доступ к брокерскому счёту.

Из корня проекта открой Python-консоль и выполни:

```python
from portfolio_xray.models.portfolio import Asset, AssetType, Portfolio

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
```

Ожидаемый результат:

```text
Стоимость: 100,000 ₽
Доля SBER: 50.0%
Доля OFZ: 35.0%
```

> Сейчас `value` означает **полную стоимость позиции**, а не цену одной акции. Рыночные котировки пока не загружаются.

## Локальный запуск и тестирование

**Требования:** Python 3.11+ (проверялось в Python 3.14), Git. Для тестов — `pytest`.

```powershell
# Клонирование
 git clone https://github.com/MarkFontenell/portfolio-xray.git
 cd portfolio-xray

# Виртуальное окружение (Windows / PowerShell)
 py -m venv .venv
 .\.venv\Scripts\Activate.ps1

# Тестирование
 python -m pip install pytest
 python -m pytest tests/test_portfolio.py -v
```

*Веб-приложения пока нет: текущий результат запускается через Python и тесты.*

## Архитектура

```text
portfolio-xray/
├── portfolio_xray/
│   ├── models/
│   │   └── portfolio.py       # AssetType, Asset, Portfolio — реализовано
│   ├── core/                  # Движок сценариев и анализ рисков — план
│   ├── services/              # Загрузка и обработка портфеля — план
│   ├── ui/                    # Визуальный интерфейс — план
│   ├── integrations/          # Подключение T-Invest MCP — план
│   └── ai/                    # AI-агент и объяснения — план
├── tests/
│   └── test_portfolio.py     # Автоматические проверки
├── .gitignore
└── README.md
```

**Архитектурное решение:** расчётная логика отделяется от UI и внешних API. Это позволит подключить Streamlit, FastAPI или брокерские данные без переписывания доменных моделей.

## Технологии

| Используются сейчас | Планируются |
|---|---|
| Python, `dataclasses`, `Enum`, Git/GitHub, Pytest | Pandas, Streamlit, T-Invest MCP, LLM API, FastAPI (при необходимости) |

## Roadmap

- [x] **Этап 1. Domain Models:** активы, портфель, валидация, тесты.
- [ ] **Этап 2. Scenario Engine:** пересчёт акций по процентному шоку; приближённая переоценка облигаций через дюрацию; P&L.
- [ ] **Этап 3. Dashboard:** интерактивные сценарии, графики, доли активов.
- [ ] **Этап 4. T-Invest MCP:** получение доступных данных портфеля и финансовых инструментов (при наличии авторизации и разрешений).
- [ ] **Этап 5. AI Explainability:** объяснение риска простым языком на основе проверенных вычислений.
- [ ] **Этап 6. Демонстрация MVP:** сценарий, который можно показать на хакатоне.

## Ограничения

Это **прототип**, а не сервис инвестиционных рекомендаций. Сценарии «что, если» не являются прогнозом доходности. Для расчёта реальных денежных сумм в дальнейшем потребуется более строгая обработка точности чисел, включая изучение `Decimal`.

---

### English summary

**Portfolio X-Ray** is a Python-based investment portfolio analysis prototype designed to evolve into an interactive stress-testing tool. The current version provides immutable asset models, portfolio value and allocation calculations, validation, and automated tests. Planned features include market scenario simulation, a dashboard, T-Invest MCP integration, and explainable AI-generated summaries. **The trading, market-data, and AI features are not implemented yet.**
