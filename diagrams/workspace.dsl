workspace "Telco Customer Churn ML" "C4 model for the local batch-oriented customer churn analysis project." {

    !identifiers hierarchical
    !impliedRelationships false

    model {
        analyst = person "Специалист по данным" "Запускает сценарии подготовки данных и EDA, проверяет отчёты."

        sourceData = softwareSystem "Датасет Telco Churn" "Статический CSV-источник. Имитация поступления пакетов." {
            tags "External, Data Source"
        }

        gitHub = softwareSystem "Git / GitHub" "Средства версионного контроля. Вне runtime-обработки." {
            tags "External, Development Tool"
        }

        churnSystem = softwareSystem "ML-система оттока" "Локальное пакетное Python-приложение. Подготовка данных и EDA реализованы. Обучение и прогноз — в планах." {
            !docs documentation
            !adrs decisions

            cli = container "Python CLI" "Запускает подготовку выборок и EDA. Обучение и прогноз запланированы." "Python / CLI" {
                tags "CLI, Partially Implemented"
            }

            dataStore = container "Файловое хранилище" "Хранит исходный CSV (data/raw), начальную выборку и входящие пакеты." "Файловая система / CSV" {
                tags "Data Store, Partially Implemented"
            }

            artifactsStore = container "Хранилище артефактов" "Отчёты, графики, манифест. Модели и прогнозы будут добавлены позже." "Файловая система / CSV, JSON, PNG" {
                tags "Artifacts, Partially Implemented"
            }
        }

        analyst -> churnSystem "Использует" "Командная строка"
        sourceData -> churnSystem "Передаёт CSV" "CSV"
        analyst -> gitHub "Версионирует" "Git over HTTPS"

        analyst -> churnSystem.cli "Запускает сценарии" "PowerShell / CLI"
        analyst -> churnSystem.artifactsStore "Читает отчёты" "Файловая система"
        sourceData -> churnSystem.dataStore "Копирует CSV" "CSV"
        churnSystem.cli -> churnSystem.dataStore "Читает / пишет" "Локальный I/O / CSV"
        churnSystem.cli -> churnSystem.artifactsStore "Пишет отчёты" "Локальный I/O"
    }

    views {
        systemLandscape "landscape" "Общая среда проекта" {
            include *?
            autoLayout lr
        }

        systemContext churnSystem "context" "Контекст локальной пакетной системы" {
            include *?
            exclude gitHub
            autoLayout lr
        }

        container churnSystem "containers" "Внутренние контейнеры приложения" {
            include *?
            exclude gitHub
            autoLayout lr
        }

        styles {
            element "Element" {
                color #FFFFFF
                stroke #243B53
                strokeWidth 2
                shape roundedbox
                metadata true
            }
            element "Person" {
                background #526579
                shape person
            }
            element "Software System" {
                background #17324D
            }
            element "Container" {
                background #315A7D
            }
            element "CLI" {
                background #23756E
            }
            element "Data Store" {
                background #F0B35D
                color #172B3A
                shape cylinder
            }
            element "Artifacts" {
                background #8265A5
                shape folder
            }
            element "External" {
                background #E8EDF2
                color #263746
                stroke #8493A2
            }
            element "Data Source" {
                background #F0B35D
                color #263746
                stroke #A77B22
                shape folder
            }
            element "Development Tool" {
                background #E8EDF2
                color #263746
                stroke #8493A2
            }
            relationship "Relationship" {
                color #64788B
                thickness 2
            }
        }
    }

    configuration {
        scope softwaresystem
    }
}
