import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# Пути проекта
ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "data" / "raw" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"

INITIAL_FILE = ROOT / "data" / "initial" / "initial_60.csv"
INCOMING_DIR = ROOT / "data" / "incoming"
MANIFEST_FILE = ROOT / "reports" / "data_manifest.csv"

# Параметры воспроизводимого разбиения
RANDOM_STATE = 42
BATCH_COUNT = 4


def calculate_sha256(path: Path) -> str:
    """Возвращает SHA-256 файла."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if not RAW_FILE.is_file():
        raise FileNotFoundError(f"Исходный CSV не найден: {RAW_FILE}")

    INITIAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    INCOMING_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Исходный файл читается, но не изменяется.
    df = pd.read_csv(RAW_FILE)

    if "Churn" not in df.columns:
        raise ValueError("В данных отсутствует целевой признак Churn.")

    if df["Churn"].isna().any():
        raise ValueError("В целевой переменной обнаружены пропуски.")

    # Около 60% записей — начальная выборка.
    # Стратификация сохраняет соотношение классов Churn.
    initial, incoming = train_test_split(
        df,
        test_size=0.4,
        stratify=df["Churn"],
        random_state=RANDOM_STATE,
    )

    initial.to_csv(INITIAL_FILE, index=False)

    # Перемешиваем оставшуюся часть с фиксированным seed.
    incoming = incoming.sample(
        frac=1,
        random_state=RANDOM_STATE,
    ).reset_index(drop=True)

    batches = np.array_split(incoming, BATCH_COUNT)
    manifest_rows = []

    def add_manifest_record(path: Path, rows: int, source: str) -> None:
        manifest_rows.append(
            {
                "file": path.relative_to(ROOT).as_posix(),
                "rows": rows,
                "columns": len(df.columns),
                "sha256": calculate_sha256(path),
                "source": source,
                "random_state": RANDOM_STATE,
            }
        )

    add_manifest_record(
        RAW_FILE,
        len(df),
        "Immutable original CSV",
    )
    add_manifest_record(
        INITIAL_FILE,
        len(initial),
        "Initial 60 percent sample",
    )

    for index, batch in enumerate(batches, start=1):
        batch_file = INCOMING_DIR / f"batch_{index:02d}.csv"
        batch.to_csv(batch_file, index=False)

        add_manifest_record(
            batch_file,
            len(batch),
            "Simulated incoming batch",
        )

    pd.DataFrame(manifest_rows).to_csv(
        MANIFEST_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print(f"Исходный набор: {len(df)} записей")
    print(f"Начальная выборка: {len(initial)} записей")
    print(f"Всего новых записей: {len(incoming)}")
    print(f"Количество пакетов: {BATCH_COUNT}")
    print("\nРазмеры пакетов:")
    for index, batch in enumerate(batches, start=1):
        print(f"batch_{index:02d}.csv: {len(batch)} записей")

    print("\nРаспределение Churn в исходном наборе:")
    print(df["Churn"].value_counts().to_string())

    print("\nSHA-256 исходного файла:")
    print(calculate_sha256(RAW_FILE))

    print(f"\nМанифест сохранен: {MANIFEST_FILE}")


if __name__ == "__main__":
    main()
