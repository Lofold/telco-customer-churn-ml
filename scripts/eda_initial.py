from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, mannwhitneyu

# Корневая папка репозитория определяется относительно этого скрипта.
ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "data" / "initial" / "initial_60.csv"
OUTPUT_DIR = ROOT / "reports" / "eda"
FIGURES_DIR = OUTPUT_DIR / "figures"
RANDOM_STATE = 42

TARGET = "Churn"
ID_COLUMN = "customerID"
CONTINUOUS_COLUMNS = ["tenure", "MonthlyCharges", "TotalCharges"]
CATEGORICAL_COLUMNS = [
    "gender",
    "SeniorCitizen",
    "Partner",
    "Dependents",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
]

FEATURE_MEANINGS = {
    "customerID": "Уникальный идентификатор клиента; не использовать как предиктор модели",
    "gender": "Пол клиента",
    "SeniorCitizen": "Признак пожилого клиента (0/1)",
    "Partner": "Наличие партнера/супруга",
    "Dependents": "Наличие иждивенцев",
    "tenure": "Продолжительность обслуживания, месяцев",
    "PhoneService": "Подключена ли телефонная услуга",
    "MultipleLines": "Наличие нескольких телефонных линий",
    "InternetService": "Тип интернет-подключения",
    "OnlineSecurity": "Подключена ли онлайн-защита",
    "OnlineBackup": "Подключено ли онлайн-резервное копирование",
    "DeviceProtection": "Подключена ли защита оборудования",
    "TechSupport": "Подключена ли техническая поддержка",
    "StreamingTV": "Подключен ли стриминг телевидения",
    "StreamingMovies": "Подключен ли стриминг фильмов",
    "Contract": "Тип договора",
    "PaperlessBilling": "Используется ли электронный счет",
    "PaymentMethod": "Способ оплаты",
    "MonthlyCharges": "Ежемесячные начисления клиенту",
    "TotalCharges": "Суммарные начисления за период обслуживания",
    "Churn": "Целевой признак: факт оттока (Yes/No)",
}


def save_csv(frame: pd.DataFrame, name: str) -> None:
    """Сохраняет отчет в CSV с UTF-8 BOM для удобного открытия в Excel."""
    frame.to_csv(OUTPUT_DIR / name, index=False, encoding="utf-8-sig")


def rate_yes(series: pd.Series) -> float:
    """Рассчитывает долю Churn=Yes в процентах."""
    if len(series) == 0:
        return float("nan")
    return float((series == "Yes").mean() * 100)


def save_bar_chart(
    values: pd.Series,
    title: str,
    xlabel: str,
    ylabel: str,
    filename: str,
    percent: bool = False,
) -> None:
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    bars = ax.bar([str(x) for x in values.index], values.values)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=15)
    ax.grid(axis="y", alpha=0.25)
    top = max(values.values) if len(values) else 1
    ax.set_ylim(0, top * 1.18 if top > 0 else 1)
    for bar, value in zip(bars, values.values):
        label = f"{value:.2f}%" if percent else f"{int(value)}"
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value,
            label,
            ha="center",
            va="bottom",
            fontsize=9,
        )
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / filename, bbox_inches="tight")
    plt.close(fig)


def run_chi_square(table: pd.DataFrame) -> tuple[float, float, int]:
    """Возвращает chi-square, p-value и число степеней свободы."""
    chi2, p_value, dof, _ = chi2_contingency(table)
    return float(chi2), float(p_value), int(dof)


def main() -> None:
    if not INPUT_FILE.is_file():
        raise FileNotFoundError(
            f"Не найдена начальная выборка: {INPUT_FILE}\n"
            "Сначала успешно выполните scripts/split_data.py."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # Исходная часть читается только для анализа. CSV на диске не меняется.
    raw = pd.read_csv(INPUT_FILE)
    source_rows, source_cols = raw.shape
    original_dtypes = raw.dtypes.astype(str).to_dict()

    required_columns = {
        ID_COLUMN,
        TARGET,
        *CONTINUOUS_COLUMNS,
        *CATEGORICAL_COLUMNS,
    }
    missing_columns = sorted(required_columns - set(raw.columns))
    if missing_columns:
        raise ValueError(
            f"В исходной части отсутствуют ожидаемые столбцы: {missing_columns}"
        )

    # Пустые строки (в том числе строки из пробелов) считаются пропусками.
    df = raw.replace(r"^\s*$", pd.NA, regex=True).copy()
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")

    # 1. Описание схемы и смысла каждого признака.
    schema_rows = []
    for column in raw.columns:
        examples = (
            raw[column].dropna().astype(str).drop_duplicates().head(3).tolist()
        )
        schema_rows.append(
            {
                "feature": column,
                "meaning": FEATURE_MEANINGS.get(
                    column, "Требуется уточнить смысл по источнику данных"
                ),
                "original_dtype": original_dtypes.get(
                    column, str(raw[column].dtype)
                ),
                "analysis_dtype": str(df[column].dtype),
                "unique_values": int(df[column].nunique(dropna=True)),
                "missing_values": int(df[column].isna().sum()),
                "examples": "; ".join(examples),
            }
        )
    save_csv(pd.DataFrame(schema_rows), "feature_schema.csv")

    # 2. Контроль качества: пропуски, дубликаты, идентификаторы и диапазоны.
    missing_rows = []
    for column in df.columns:
        count = int(df[column].isna().sum())
        missing_rows.append(
            {
                "feature": column,
                "missing_count": count,
                "missing_percent": round(count / len(df) * 100, 4),
            }
        )
    missing_report = pd.DataFrame(missing_rows).sort_values(
        ["missing_count", "feature"], ascending=[False, True]
    )
    save_csv(missing_report, "missing_values.csv")

    duplicate_rows = int(df.duplicated().sum())
    duplicate_ids = int(df[ID_COLUMN].duplicated().sum())
    quality_checks = [
        {"check": "Количество записей", "result": len(df), "status": "INFO"},
        {
            "check": "Количество столбцов",
            "result": len(df.columns),
            "status": "INFO",
        },
        {
            "check": "Полные дубликаты строк",
            "result": duplicate_rows,
            "status": "PASS" if duplicate_rows == 0 else "REVIEW",
        },
        {
            "check": "Повторяющиеся customerID",
            "result": duplicate_ids,
            "status": "PASS" if duplicate_ids == 0 else "REVIEW",
        },
        {
            "check": "Пропуски/пустые строки в TotalCharges",
            "result": int(df["TotalCharges"].isna().sum()),
            "status": "PASS"
            if int(df["TotalCharges"].isna().sum()) == 0
            else "REVIEW",
        },
        {
            "check": "tenure вне диапазона [0; 72]",
            "result": int((~df["tenure"].between(0, 72)).sum()),
            "status": "PASS"
            if df["tenure"].between(0, 72).all()
            else "REVIEW",
        },
        {
            "check": "Отрицательные MonthlyCharges",
            "result": int((df["MonthlyCharges"] < 0).sum()),
            "status": "PASS"
            if (df["MonthlyCharges"] >= 0).all()
            else "REVIEW",
        },
        {
            "check": "Отрицательные TotalCharges",
            "result": int((df["TotalCharges"].dropna() < 0).sum()),
            "status": "PASS"
            if (df["TotalCharges"].dropna() >= 0).all()
            else "REVIEW",
        },
        {
            "check": "Неожиданные значения Churn",
            "result": int((~df[TARGET].isin(["Yes", "No"])).sum()),
            "status": "PASS"
            if df[TARGET].isin(["Yes", "No"]).all()
            else "REVIEW",
        },
    ]
    save_csv(pd.DataFrame(quality_checks), "quality_checks.csv")

    # 3. Целевая переменная и баланс классов.
    target_counts = df[TARGET].value_counts(dropna=False)
    target_distribution = pd.DataFrame(
        {
            "class": target_counts.index.astype(str),
            "count": target_counts.values,
            "percent": (target_counts.values / len(df) * 100).round(4),
        }
    )
    save_csv(target_distribution, "target_distribution.csv")
    save_bar_chart(
        target_counts.reindex(["No", "Yes"]).dropna(),
        "Распределение целевого признака Churn (начальная выборка)",
        "Churn",
        "Количество записей",
        "churn_distribution.png",
    )

    # 4. Описательные статистики непрерывных признаков.
    numeric_summary = (
        df[CONTINUOUS_COLUMNS].describe().T.reset_index(names="feature")
    )
    save_csv(numeric_summary, "numeric_summary.csv")

    # Проверка выбросов методом межквартильного размаха (IQR).
    outlier_rows = []
    for column in CONTINUOUS_COLUMNS:
        values = df[column].dropna()
        if values.empty:
            outlier_rows.append(
                {
                    "feature": column,
                    "q1": np.nan,
                    "q3": np.nan,
                    "iqr": np.nan,
                    "lower_bound": np.nan,
                    "upper_bound": np.nan,
                    "outlier_count": 0,
                    "outlier_percent": 0.0,
                }
            )
            continue
        q1 = float(values.quantile(0.25))
        q3 = float(values.quantile(0.75))
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        count = int(((values < lower) | (values > upper)).sum())
        outlier_rows.append(
            {
                "feature": column,
                "q1": q1,
                "q3": q3,
                "iqr": iqr,
                "lower_bound": lower,
                "upper_bound": upper,
                "outlier_count": count,
                "outlier_percent": round(count / len(values) * 100, 4),
            }
        )
    save_csv(pd.DataFrame(outlier_rows), "iqr_outliers.csv")

    # 5. Связи признаков с оттоком: доля Churn=Yes по категориям.
    churn_rates = []
    for column in CATEGORICAL_COLUMNS:
        # SeniorCitizen является числовым бинарным признаком, но по смыслу категориальный.
        grouped = (
            df.groupby(column, dropna=False, observed=False)[TARGET]
            .agg(records="size", churn_yes=lambda x: int((x == "Yes").sum()))
            .reset_index()
        )
        grouped["churn_rate_percent"] = (
            grouped["churn_yes"] / grouped["records"] * 100
        ).round(4)
        grouped.insert(0, "feature", column)
        grouped = grouped.rename(columns={column: "category"})
        churn_rates.append(grouped)
    save_csv(
        pd.concat(churn_rates, ignore_index=True),
        "churn_rates_by_category.csv",
    )

    contract_rates = (
        df.groupby("Contract", dropna=False)[TARGET]
        .apply(rate_yes)
        .sort_values(ascending=False)
    )
    save_bar_chart(
        contract_rates,
        "Доля оттока по типу договора",
        "Тип договора",
        "Клиенты с Churn = Yes, %",
        "churn_by_contract.png",
        percent=True,
    )

    internet_rates = (
        df.groupby("InternetService", dropna=False)[TARGET]
        .apply(rate_yes)
        .sort_values(ascending=False)
    )
    save_bar_chart(
        internet_rates,
        "Доля оттока по типу интернет-услуги",
        "Тип услуги",
        "Клиенты с Churn = Yes, %",
        "churn_by_internet_service.png",
        percent=True,
    )

    # Boxplot tenure by churn.
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    tenure_groups = [
        df.loc[df[TARGET] == label, "tenure"].dropna().values
        for label in ["No", "Yes"]
    ]
    ax.boxplot(tenure_groups, tick_labels=["Churn = No", "Churn = Yes"])
    ax.set_title("Продолжительность обслуживания по классу Churn")
    ax.set_ylabel("Tenure, месяцев")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "tenure_by_churn.png", bbox_inches="tight")
    plt.close(fig)

    # 6. Корреляции числовых признаков и целевого признака (Churn: No=0, Yes=1).
    corr_df = df[CONTINUOUS_COLUMNS].copy()
    corr_df["Churn_encoded"] = df[TARGET].map({"No": 0, "Yes": 1})
    correlations = corr_df.corr(numeric_only=True)["Churn_encoded"].drop(
        "Churn_encoded"
    )
    correlation_report = (
        correlations.rename("pearson_correlation_with_churn")
        .rename_axis("feature")
        .reset_index()
    )
    save_csv(correlation_report, "numeric_correlations_with_churn.csv")

    # 7. Формальная проверка предметных гипотез.
    hypothesis_rows = []

    # H1: Contract and Churn are associated.
    table_contract = pd.crosstab(df["Contract"], df[TARGET])
    chi2, p_value, dof = run_chi_square(table_contract)
    rates = (
        table_contract.get("Yes", pd.Series(dtype=float))
        / table_contract.sum(axis=1)
        * 100
    )
    hypothesis_rows.append(
        {
            "hypothesis": "H1: тип договора связан с оттоком клиентов",
            "test": "Критерий хи-квадрат независимости",
            "statistic": chi2,
            "degrees_of_freedom": dof,
            "p_value": p_value,
            "descriptive_result": "; ".join(
                f"{idx}: {value:.2f}% Churn=Yes"
                for idx, value in rates.items()
            ),
            "decision_alpha_0_05": "Есть статистические основания считать признаки связанными"
            if p_value < 0.05
            else "Недостаточно оснований отвергнуть независимость",
        }
    )

    # H2: tenure distribution for churners is lower than for non-churners.
    tenure_yes = df.loc[df[TARGET] == "Yes", "tenure"].dropna()
    tenure_no = df.loc[df[TARGET] == "No", "tenure"].dropna()
    u_stat, p_value = mannwhitneyu(tenure_yes, tenure_no, alternative="less")
    hypothesis_rows.append(
        {
            "hypothesis": "H2: у ушедших клиентов tenure меньше, чем у оставшихся",
            "test": "Односторонний критерий Манна—Уитни",
            "statistic": float(u_stat),
            "degrees_of_freedom": np.nan,
            "p_value": float(p_value),
            "descriptive_result": f"Медиана tenure: Churn=Yes — {tenure_yes.median():.2f}; Churn=No — {tenure_no.median():.2f} месяцев",
            "decision_alpha_0_05": "Гипотеза поддерживается данными"
            if p_value < 0.05
            else "Статистических оснований недостаточно",
        }
    )

    # H3: TechSupport Yes/No comparison only; 'No internet service' is excluded.
    tech_df = df[df["TechSupport"].isin(["Yes", "No"])].copy()
    tech_table = pd.crosstab(tech_df["TechSupport"], tech_df[TARGET]).reindex(
        index=["No", "Yes"], columns=["No", "Yes"], fill_value=0
    )
    chi2, p_value, dof = run_chi_square(tech_table)
    tech_rates = tech_df.groupby("TechSupport")[TARGET].apply(rate_yes)
    hypothesis_rows.append(
        {
            "hypothesis": "H3: у клиентов без техподдержки отток выше, чем у клиентов с техподдержкой",
            "test": "Критерий хи-квадрат (только группы Yes/No)",
            "statistic": chi2,
            "degrees_of_freedom": dof,
            "p_value": p_value,
            "descriptive_result": "; ".join(
                f"TechSupport={idx}: {value:.2f}% Churn=Yes"
                for idx, value in tech_rates.items()
            ),
            "decision_alpha_0_05": "Гипотеза поддерживается данными"
            if p_value < 0.05
            and tech_rates.get("No", 0) > tech_rates.get("Yes", 0)
            else "Гипотеза не получила достаточного подтверждения",
        }
    )

    # H4: electronic-check payment vs all other methods.
    payment_group = np.where(
        df["PaymentMethod"] == "Electronic check",
        "Electronic check",
        "Other methods",
    )
    payment_table = pd.crosstab(payment_group, df[TARGET]).reindex(
        index=["Electronic check", "Other methods"],
        columns=["No", "Yes"],
        fill_value=0,
    )
    chi2, p_value, dof = run_chi_square(payment_table)
    pay_rates = payment_table["Yes"] / payment_table.sum(axis=1) * 100
    hypothesis_rows.append(
        {
            "hypothesis": "H4: при оплате Electronic check отток выше, чем при других способах оплаты",
            "test": "Критерий хи-квадрат независимости",
            "statistic": chi2,
            "degrees_of_freedom": dof,
            "p_value": p_value,
            "descriptive_result": "; ".join(
                f"{idx}: {value:.2f}% Churn=Yes"
                for idx, value in pay_rates.items()
            ),
            "decision_alpha_0_05": "Гипотеза поддерживается данными"
            if p_value < 0.05
            and pay_rates.get("Electronic check", 0)
            > pay_rates.get("Other methods", 0)
            else "Гипотеза не получила достаточного подтверждения",
        }
    )

    hypotheses = pd.DataFrame(hypothesis_rows)
    hypotheses["p_value"] = hypotheses["p_value"].astype(float)
    hypotheses["p_value"] = hypotheses["p_value"].map(
        lambda value: f"{value:.6g}"
    )
    save_csv(hypotheses, "hypothesis_tests.csv")

    # 8. Риски утечки целевой переменной и использования признаков.
    leakage_rows = [
        {
            "field": "Churn",
            "assessment": "Целевая переменная; использовать только как y, не включать в X.",
        },
        {
            "field": "customerID",
            "assessment": "Идентификатор; исключить из признаков модели, если нет отдельного обоснования.",
        },
        {
            "field": "TotalCharges",
            "assessment": "Проверить временную точку формирования. Признак допустим, только если сумма доступна на дату прогноза и не включает сведения после ухода.",
        },
        {
            "field": "Остальные признаки",
            "assessment": "Подтвердить, что значения известны на дату прогнозирования; исходный статический набор не содержит явной временной метки наблюдения.",
        },
    ]
    save_csv(pd.DataFrame(leakage_rows), "leakage_review.csv")

    # 9. Сводный текстовый отчет.
    churn_counts = df[TARGET].value_counts()
    churn_percent = df[TARGET].value_counts(normalize=True) * 100
    report_lines = [
        "ПРЕДМЕТНЫЙ EDA: НАЧАЛЬНАЯ ВЫБОРКА",
        f"Файл: {INPUT_FILE.relative_to(ROOT).as_posix()}",
        f"Размер: {source_rows} строк, {source_cols} столбцов",
        f"Полные дубликаты: {duplicate_rows}",
        f"Повторяющиеся customerID: {duplicate_ids}",
        f"Пропуски после обработки пустых строк: {int(df.isna().sum().sum())} ячеек",
        f"TotalCharges: {int(df['TotalCharges'].isna().sum())} пропусков после числового преобразования",
        f"Churn=No: {int(churn_counts.get('No', 0))} ({churn_percent.get('No', 0):.2f}%)",
        f"Churn=Yes: {int(churn_counts.get('Yes', 0))} ({churn_percent.get('Yes', 0):.2f}%)",
        "",
        "КЛЮЧЕВЫЕ НАБЛЮДЕНИЯ",
        f"Доля оттока по Contract: {', '.join(f'{k} — {v:.2f}%' for k, v in contract_rates.items())}",
        f"Медиана tenure: Churn=Yes — {tenure_yes.median():.2f}; Churn=No — {tenure_no.median():.2f} месяцев",
        "",
        "Проверки статистических гипотез сохранены в hypothesis_tests.csv.",
        "Результаты носят исследовательский характер и показывают ассоциации, а не причинно-следственные связи.",
        "Перед обучением необходимо исключить customerID и Churn из матрицы предикторов; для TotalCharges проверить временную доступность.",
        "",
        "ОГРАНИЧЕНИЕ: в исходном статическом наборе не указана дата каждого снимка клиента, поэтому временная доступность отдельных признаков требует подтверждения по источнику данных.",
    ]
    (OUTPUT_DIR / "eda_summary.txt").write_text(
        "\n".join(report_lines), encoding="utf-8"
    )

    # JSON метаданные для быстрой машинной проверки.
    metadata = {
        "input_file": INPUT_FILE.relative_to(ROOT).as_posix(),
        "rows": int(source_rows),
        "columns": int(source_cols),
        "duplicate_rows": duplicate_rows,
        "duplicate_customer_ids": duplicate_ids,
        "missing_cells_after_blank_normalization": int(df.isna().sum().sum()),
        "churn_counts": {str(k): int(v) for k, v in churn_counts.items()},
        "random_state_for_split": RANDOM_STATE,
    }
    (OUTPUT_DIR / "eda_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("EDA начальной выборки выполнен успешно.")
    print(f"Входной файл: {INPUT_FILE.relative_to(ROOT)}")
    print(f"Размер: {source_rows} записей, {source_cols} столбцов")
    print(f"Полные дубликаты: {duplicate_rows}")
    print(f"Повторяющиеся customerID: {duplicate_ids}")
    print(
        f"Пропуски после нормализации пустых строк: {int(df.isna().sum().sum())}"
    )
    print(f"TotalCharges: {int(df['TotalCharges'].isna().sum())} пропусков")
    print("\nРаспределение Churn:")
    print(target_distribution.to_string(index=False))
    print("\nПроверка гипотез:")
    print(
        hypotheses[["hypothesis", "p_value", "decision_alpha_0_05"]].to_string(
            index=False
        )
    )
    print(f"\nОтчеты: {OUTPUT_DIR.relative_to(ROOT)}")
    print(f"Графики: {FIGURES_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
