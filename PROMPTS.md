# Промпты для Claude Code — неделя 1 (Reconciliation Agent)

Положи `CLAUDE.md` в корень пустого репозитория, открой там Claude Code и иди по шагам. Каждый шаг — отдельный промпт. Не переходи к следующему, пока не прочитал diff и `docs/learning/` по текущему.

---

## 0. Скелет проекта

```
Прочитай CLAUDE.md. Это мой учебный и портфолио-проект.

Задача на сейчас — только скелет, без бизнес-логики:
- uv-проект на Python 3.12, ruff, mypy, pytest
- структура папок из CLAUDE.md (пустые модули с __init__.py)
- docker-compose.yml с Postgres
- .gitignore, .env.example, пустые README.md и DECISIONS.md
- GitHub Actions: lint + mypy + pytest на push

Сначала покажи план и дождись моего OK.
После — создай docs/learning/00-project-setup.md: uv vs pip/poetry
(сравни с Maven/Gradle), структура Python-пакета, pyproject.toml, зачем mypy в Python.
```

## 1. Модели

```
Шаг 1: доменные модели в src/recon/models.py (pydantic).
- Money: Decimal + currency (ISO 4217), запрет float, операции только в одной валюте
- StatementTx, LedgerEntry, ExceptionCase (тип исключения как Enum:
  BANK_FEE, PARTIAL_PAYMENT, REFERENCE_TYPO, FX_DIFFERENCE, DUPLICATE,
  REVERSAL, SPLIT_PAYMENT, MISSING_ENTRY, UNKNOWN), Adjustment
- unit-тесты на Money: округление, смешение валют, сериализация в JSON

Сначала план. В конце docs/learning/01-models.md: pydantic vs Java record +
Bean Validation, Decimal vs BigDecimal (контекст, округление), Enum в Python.
ADR в DECISIONS.md про представление денег.
```

## 2. Генератор синтетических данных

```
Шаг 2: генератор в data/generator/.
- на входе seed и параметры (кол-во транзакций, доля исключений по типам)
- генерирует леджер и выписку: большинство строк совпадает точно,
  в часть намеренно вшиты исключения всех типов из Enum
- выписка в двух форматах: CSV и ISO 20022 camt.053 (XML)
- пишет labels.json: для каждой исключённой строки — правильный тип
  и правильная пара(ы) в леджере (или "нет пары")
- детерминированность: один seed → одинаковые файлы (тест на это)
- закоммить маленький пример в data/samples/

docs/learning/02-generator.md: генераторы и random в Python, зачем seed,
почему ground truth важнее объёма данных для evals.
```

## 3. Парсеры

```
Шаг 3: парсеры в src/recon/parsers/.
- csv_statement.py, camt053.py, ledger.py → списки моделей из шага 1
- суммы сразу в Decimal, никаких промежуточных float
- понятные ошибки на битых файлах: какой файл, какая строка, что не так
- тесты на data/samples/ + на битые файлы

docs/learning/03-parsers.md: csv и xml в стандартной библиотеке vs lxml,
сравнение с тем, как это делается в Camel (data formats, unmarshal).
```

## 4. Детерминированный матчер

```
Шаг 4: src/recon/matching/.
- правила точного матчинга: сумма + валюта + дата (с окном ±N дней) + reference
- на выходе: matched pairs и unmatched (с обеих сторон)
- никакой LLM здесь — это обычный код
- тесты + сверка с labels.json: все неисключённые строки должны сматчиться,
  все исключения — попасть в unmatched

docs/learning/04-matching.md: почему детерминированная часть до LLM
(стоимость, предсказуемость, аудит), какие правила можно было добавить и почему нет.
ADR про границу между кодом и LLM.
```

## 5. MCP-серверы statements и ledger (read-only)

```
Шаг 5: два MCP-сервера через FastMCP.
- statements: list_unmatched(account_id), get_statement_tx(account_id, tx_id),
  search_statement(account_id, filters)
- ledger: search_ledger(account_id, amount_range, date_range, text),
  get_entry(account_id, entry_id), get_account_history(account_id, period)
- каждый вызов обязательно с account_id — изоляция данных
- чёткие описания tools и схем: их читает LLM, это часть промпта
- лимиты на размер ответа
- integration-тесты через MCP-клиент

docs/learning/05-mcp.md: что такое MCP, stdio vs HTTP, как модель видит tools,
почему описание tool — это prompt engineering. Сравни с REST/OpenAPI в Spring.
```

## 6. Простой агент без фреймворка

```
Шаг 6: минимальный агент на прямом API модели (Anthropic SDK), без LangGraph.
- подключается к statements и ledger, берёт одно исключение
- ищет пару через tools и классифицирует: тип исключения, кандидаты из леджера,
  уверенность, обоснование — структурированный вывод (pydantic)
- явный tool use loop с лимитом итераций и обработкой ошибок tools
- логирует каждый шаг: запрос, вызовы tools, токены
- маленький скрипт: прогнать агента по 10 исключениям и сравнить с labels.json

Это учебный шаг: хочу увидеть agent loop руками, до фреймворка.
docs/learning/06-agent-loop.md: tool use loop, stop reasons, зачем лимит
итераций, что происходит при ошибке tool, чем это отличается от вызова REST-сервиса.
```

---

## Что дальше (недели 2–4, промпты сделаем позже)
- **Неделя 2:** граф LangGraph, Postgres-чекпоинтер, interrupt на approval, MCP `postings` с идемпотентностью, MCP `reference`, память решений операциониста по счёту.
- **Неделя 3:** LiteLLM + Bedrock, Langfuse, полноценные evals против labels.json, failure-тесты, evals как gate в CI.
- **Неделя 4:** деплой в AWS, README с архитектурой и цифрами, демо.

---

## Полезные промпты на любой неделе

**Проверка понимания (после каждого модуля):**
```
Задай мне по одному вопросы из docs/learning/<файл>. После каждого моего
ответа — оцени честно, что упустил, без подсказок заранее.
```

**Ревью как на интервью:**
```
Представь, что ты интервьюер на позицию AI Agent Engineer в финтехе. Посмотри
на модуль <путь> и задай 5 каверзных вопросов о trade-offs и failure modes.
```

**Сломать специально:**
```
Предложи 3 способа сломать <модуль> (сбой сети, битые данные, падение процесса).
Не чини — напиши тесты, которые это воспроизводят, и покажи, как система себя ведёт.
```

**Объяснить кусок кода:**
```
Объясни <файл:строки> так, будто я senior Java-разработчик. Что здесь
идиоматичный Python, а что я бы сделал иначе в Java и почему тут так не нужно.
```
