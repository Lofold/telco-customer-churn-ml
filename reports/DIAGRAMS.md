# Редактируемые диаграммы проекта

Все архитектурные, UML- и процессные схемы поддерживаются в нативном формате diagrams.net (`.drawio`). Для редактирования открой соответствующий файл в diagrams.net или через расширение Draw.io Integration в Visual Studio Code.

## Архитектура и UML

| Диаграмма | Редактируемый файл | Экспорт SVG |
|---|---|---|
| C4 Context | [c4_context.drawio](architecture/diagrams/c4_context.drawio) | [c4_context.svg](architecture/diagrams/c4_context.svg) |
| C4 Container | [c4_container.drawio](architecture/diagrams/c4_container.drawio) | [c4_container.svg](architecture/diagrams/c4_container.svg) |
| UML Use Case | [use_case.drawio](architecture/diagrams/use_case.drawio) | [use_case.svg](architecture/diagrams/use_case.svg) |
| UML Sequence | [sequence_batch_prediction.drawio](architecture/diagrams/sequence_batch_prediction.drawio) | [sequence_batch_prediction.svg](architecture/diagrams/sequence_batch_prediction.svg) |
| Архитектура системы (Приложение Б) | [system_architecture.drawio](architecture/diagrams/system_architecture.drawio) | [system_architecture.svg](architecture/diagrams/system_architecture.svg) |

## Конвейер

| Диаграмма | Редактируемый файл | Экспорт SVG |
|---|---|---|
| Конвейер подготовки данных и прогнозирования оттока | [ml_pipeline_activity.drawio](pipeline/diagrams/ml_pipeline_activity.drawio) | [ml_pipeline_activity.svg](pipeline/diagrams/ml_pipeline_activity.svg) |

SVG-файлы являются экспортами для просмотра в Markdown и вставки в отчёт. В Word используются PNG-экспорты тех же схем; редактируемый исходник `.drawio` хранится в репозитории.

Четыре графика EDA остаются программно генерируемыми изображениями: они строятся из актуальных данных скриптом `scripts/eda_initial.py`, поэтому их не следует вручную редактировать в diagrams.net.