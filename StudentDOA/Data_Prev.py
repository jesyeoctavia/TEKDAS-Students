"""Pemeriksaan, pembersihan ringan, dan pembagian data StudentDOA.

Jalankan dari folder ini dengan: python Data_Prev.py
"""
from pathlib import Path
import json

import pandas as pd
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "dataset_StudentDOA.csv"
TARGET = "Target"

# Informasi semester kedua tidak digunakan untuk prediksi awal agar tidak
# membocorkan informasi yang baru tersedia setelah semester kedua selesai.
CATEGORICAL_COLUMNS = [
    "Marital status", "Application mode", "Course", "Daytime/evening attendance",
    "Previous qualification", "Nacionality", "Mother's qualification",
    "Father's qualification", "Mother's occupation", "Father's occupation",
    "Displaced", "Educational special needs", "Debtor", "Tuition fees up to date",
    "Gender", "Scholarship holder", "International",
]
NUMERIC_COLUMNS = [
    "Application order", "Age at enrollment",
    "Curricular units 1st sem (credited)", "Curricular units 1st sem (enrolled)",
    "Curricular units 1st sem (evaluations)", "Curricular units 1st sem (approved)",
    "Curricular units 1st sem (grade)",
    "Curricular units 1st sem (without evaluations)",
    "Unemployment rate", "Inflation rate", "GDP",
]
FEATURE_COLUMNS = CATEGORICAL_COLUMNS + NUMERIC_COLUMNS
GRADE_COLUMNS = ["Curricular units 1st sem (grade)", "Curricular units 2nd sem (grade)"]


def normalize_grade(value):
    """Perbaiki nilai grade yang desimalnya tertulis dengan banyak titik."""
    if pd.isna(value):
        return value
    value = str(value).strip()
    parts = value.split(".")
    if len(parts) > 2:
        value = parts[0] + "." + "".join(parts[1:])
    return pd.to_numeric(value, errors="coerce")


def load_data(path: Path = DATA_FILE) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";")
    required = set(FEATURE_COLUMNS + [TARGET])
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError("Kolom wajib tidak ditemukan: " + ", ".join(missing))
    for column in GRADE_COLUMNS:
        if column in df.columns:
            df[column] = df[column].map(normalize_grade)
    return df


def main():
    df = load_data()
    train, test = train_test_split(
        df, test_size=0.20, random_state=42, stratify=df[TARGET]
    )
    df.to_csv(BASE_DIR / "student_clean.csv", index=False)
    train.to_csv(BASE_DIR / "student_train.csv", index=False)
    test.to_csv(BASE_DIR / "student_test.csv", index=False)
    summary = {
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
        "missing_cells": int(df.isna().sum().sum()),
        "target_counts": {str(k): int(v) for k, v in df[TARGET].value_counts().items()},
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "feature_count": len(FEATURE_COLUMNS),
        "features_use_first_semester_only": True,
        "grade_columns_normalized": [c for c in GRADE_COLUMNS if c in df.columns],
    }
    (BASE_DIR / "data_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("Pemeriksaan dan persiapan data selesai.")
    print(f"Data: {len(df):,} baris x {df.shape[1]} kolom")
    print(f"Train/test: {len(train):,}/{len(test):,}")
    print("Dibuat: student_clean.csv, student_train.csv, student_test.csv, data_summary.json")


if __name__ == "__main__":
    main()
