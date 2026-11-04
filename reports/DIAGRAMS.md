# Исходники и экспорт диаграмм проекта

Диаграммы проекта создаются из текстовых исходников. Ручное редактирование экспортированных SVG/PNG не применяется: при изменении схемы обновляется исходный файл и повторно выполняется экспорт.

## Архитектура C4 — Structurizr DSL

| Представление | Исходник | SVG | PNG |
|---|---|---|---|
| C4 System Landscape | [`diagrams/workspace.dsl`](../diagrams/workspace.dsl), view `landscape` | [`c4_landscape.svg`](../diagrams/svg/c4_landscape.svg) | [`c4_landscape.png`](../diagrams/png/c4_landscape.png) |
| C4 System Context | [`diagrams/workspace.dsl`](../diagrams/workspace.dsl), view `context` | [`c4_context.svg`](../diagrams/svg/c4_context.svg) | [`c4_context.png`](../diagrams/png/c4_context.png) |
| C4 Container | [`diagrams/workspace.dsl`](../diagrams/workspace.dsl), view `containers` | [`c4_containers.svg`](../diagrams/svg/c4_containers.svg) | [`c4_containers.png`](../diagrams/png/c4_containers.png) |

*Примечание: файлы `*-key.svg` и `*-key.png` в папках экспорта являются отдельными легендами к C4-диаграммам.*

## UML — PlantUML

| Диаграмма | Исходник | SVG | PNG |
|---|---|---|---|
| Use Case | [`use_case.puml`](../diagrams/source/use_case.puml) | [`use_case.svg`](../diagrams/svg/use_case.svg) | [`use_case.png`](../diagrams/png/use_case.png) |
| Sequence — пакетное прогнозирование | [`sequence_batch_prediction.puml`](../diagrams/source/sequence_batch_prediction.puml) | [`sequence_batch_prediction.svg`](../diagrams/svg/sequence_batch_prediction.svg) | [`sequence_batch_prediction.png`](../diagrams/png/sequence_batch_prediction.png) |
| Activity — реализованный процесс подготовки данных и EDA | [`ml_pipeline_activity.puml`](../diagrams/source/ml_pipeline_activity.puml) | [`ml_pipeline_activity.svg`](../diagrams/svg/ml_pipeline_activity.svg) | [`ml_pipeline_activity.png`](../diagrams/png/ml_pipeline_activity.png) |

## Архитектурные и процессные схемы — D2

| Диаграмма | Исходник | SVG | PNG |
|---|---|---|---|
| ML pipeline — целевой контур обучения и пакетного прогнозирования | [`ml_pipeline.d2`](../diagrams/source/ml_pipeline.d2) | [`ml_pipeline.svg`](../diagrams/svg/ml_pipeline.svg) | [`ml_pipeline.png`](../diagrams/png/ml_pipeline.png) |
| Логическая архитектура системы (Приложение Б) | [`system_architecture.d2`](../diagrams/source/system_architecture.d2) | [`system_architecture.svg`](../diagrams/svg/system_architecture.svg) | [`system_architecture.png`](../diagrams/png/system_architecture.png) |

## Правила интерпретации

- Зелёным отмечены реализованные компоненты; синим — этапы обработки; фиолетовым — хранилища артефактов; янтарным — решения и проектируемые функции; красным — ошибки; серым — внешние сущности.
- UML Activity отражает фактически реализованный сценарий `split_data.py` и `eda_initial.py`.
- D2 ML pipeline показывает целевой процесс разработки модели и последующего batch inference. Наличие схемы не означает, что валидация incoming, Train/Validation/Test, обучение и прогнозирование уже реализованы.
- C4 Landscape/Context/Container создаются из одного `workspace.dsl`. Git/GitHub показан в Landscape как инструмент разработки и исключён из Context и Container как не-runtime компонент.
- `data/incoming/batch_*.csv` — воспроизводимая имитация поступления пакетов; достоверной временной последовательности событий в исходном наборе нет.
- `Churn` — целевая переменная, а `customerID` — идентификатор для сопоставления результатов; ни один из них не включается в матрицу предикторов. Доступность `TotalCharges` на момент реального прогноза требует отдельного подтверждения.

## Экспорт

Исходники хранятся в `diagrams/source/`, C4-модель — в `diagrams/workspace.dsl`; готовые экспорты размещаются в `diagrams/svg/` и `diagrams/png/`.

Для D2 из корня репозитория:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\render_d2_diagrams.ps1
```

PlantUML экспортируется через VS Code PlantUML (`Alt+D` -> `PlantUML: Export Current Diagram`). Structurizr Local открывает `diagrams/workspace.dsl`; из него экспортируются представления в SVG и PNG. Кэш `.structurizr/`, локальный `workspace.json` и резервная копия `workspace.initial.backup.dsl` не являются исходниками проекта и не должны попадать в Git.

Четыре графика EDA остаются программно генерируемыми скриптом `scripts/eda_initial.py`, а не редактируемыми архитектурными диаграммами.
