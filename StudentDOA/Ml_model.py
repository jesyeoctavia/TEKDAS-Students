"""Latih dan evaluasi model status mahasiswa.

Jalankan setelah Data_Prev.py: python Ml_model.py
"""
from pathlib import Path
import json

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from Data_Prev import CATEGORICAL_COLUMNS, FEATURE_COLUMNS, NUMERIC_COLUMNS, TARGET

BASE_DIR = Path(__file__).resolve().parent


def build_pipeline():
    prep = ColumnTransformer([
        ("num", SimpleImputer(strategy="median"), NUMERIC_COLUMNS),
        ("cat", Pipeline([
            ("fill", SimpleImputer(strategy="most_frequent")),
            ("encode", OneHotEncoder(handle_unknown="ignore")),
        ]), CATEGORICAL_COLUMNS),
    ])
    return Pipeline([
        ("prep", prep),
        ("model", RandomForestClassifier(
            n_estimators=300, min_samples_leaf=2, class_weight="balanced",
            random_state=42, n_jobs=-1,
        )),
    ])


def main():
    train_path, test_path = BASE_DIR / "student_train.csv", BASE_DIR / "student_test.csv"
    if not train_path.exists() or not test_path.exists():
        raise FileNotFoundError("Jalankan `python Data_Prev.py` terlebih dahulu.")
    train, test = pd.read_csv(train_path), pd.read_csv(test_path)
    model = build_pipeline()
    model.fit(train[FEATURE_COLUMNS], train[TARGET].astype(str))
    actual = test[TARGET].astype(str)
    predicted = model.predict(test[FEATURE_COLUMNS])
    labels = sorted(actual.unique())
    metrics = {
        "accuracy": float(accuracy_score(actual, predicted)),
        "macro_f1": float(f1_score(actual, predicted, average="macro")),
        "labels": labels,
        "confusion_matrix": confusion_matrix(actual, predicted, labels=labels).tolist(),
        "classification_report": classification_report(
            actual, predicted, labels=labels, output_dict=True, zero_division=0
        ),
        "test_rows": int(len(test)),
        "random_state": 42,
    }
    joblib.dump(model, BASE_DIR / "student_status_pipeline.pkl")
    fi = pd.DataFrame({
        "feature": model.named_steps["prep"].get_feature_names_out(),
        "importance": model.named_steps["model"].feature_importances_,
    }).sort_values("importance", ascending=False)
    fi.to_csv(BASE_DIR / "feature_importance.csv", index=False)
    (BASE_DIR / "model_metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    pred = test[[TARGET]].copy()
    pred["predicted_status"] = predicted
    pred.to_csv(BASE_DIR / "student_predictions.csv", index=False)
    print("Model Random Forest selesai dilatih.")
    print(f"Accuracy: {metrics['accuracy']:.3f} | Macro F1: {metrics['macro_f1']:.3f}")
    print("Dibuat: student_status_pipeline.pkl, feature_importance.csv,")
    print("        model_metrics.json, student_predictions.csv")


if __name__ == "__main__":
    main()
