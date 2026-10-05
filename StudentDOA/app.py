"""Streamlit dashboard for the StudentDOA dataset."""
from pathlib import Path

import pandas as pd
import streamlit as st
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

BASE = Path(__file__).resolve().parent
TARGET = "Target"
LABELS = {"Dropout": "Berhenti", "Enrolled": "Masih terdaftar", "Graduate": "Lulus"}
CATS = ["Marital status", "Application mode", "Course", "Daytime/evening attendance",
        "Previous qualification", "Nacionality", "Mother's qualification",
        "Father's qualification", "Mother's occupation", "Father's occupation",
        "Displaced", "Educational special needs", "Debtor", "Tuition fees up to date",
        "Gender", "Scholarship holder", "International"]
NUMS = ["Application order", "Age at enrollment", "Curricular units 1st sem (credited)",
        "Curricular units 1st sem (enrolled)", "Curricular units 1st sem (evaluations)",
        "Curricular units 1st sem (approved)", "Curricular units 1st sem (grade)",
        "Curricular units 1st sem (without evaluations)", "Unemployment rate", "Inflation rate", "GDP"]
FEATURES = CATS + NUMS

st.set_page_config(page_title="StudentDOA | Dashboard", page_icon="🎓", layout="wide")
st.title("🎓 Analisis Status Akademik Mahasiswa")
st.caption("Eksplorasi dataset StudentDOA dan demo klasifikasi status akhir mahasiswa.")


@st.cache_data
def load_data():
    # CSV ini menggunakan pemisah titik koma.
    df = pd.read_csv(BASE / "dataset_StudentDOA.csv", sep=";")
    # Pada dua kolom nilai, sebagian desimal rusak dan pemisah ribuan titik
    # tersisip setelah titik desimal, misalnya 13.666.666.666.666.600.
    # Gabungkan kembali bagian desimal: 13.666666666666600.
    grade_columns = [
        "Curricular units 1st sem (grade)",
        "Curricular units 2nd sem (grade)",
    ]
    def normalize_grade(value):
        if pd.isna(value):
            return value
        parts = str(value).split(".")
        if len(parts) > 2:
            return parts[0] + "." + "".join(parts[1:])
        return str(value)

    for column in grade_columns:
        if column in df.columns:
            df[column] = df[column].map(normalize_grade)
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


@st.cache_resource
def fit_model(df):
    X, y = df[FEATURES], df[TARGET].astype(str)
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=.2, random_state=42, stratify=y
    )
    prep = ColumnTransformer([
        ("num", SimpleImputer(strategy="median"), NUMS),
        ("cat", Pipeline([
            ("fill", SimpleImputer(strategy="most_frequent")),
            ("encode", OneHotEncoder(handle_unknown="ignore")),
        ]), CATS),
    ])
    model = Pipeline([
        ("prep", prep),
        ("rf", RandomForestClassifier(
            n_estimators=250, class_weight="balanced", random_state=42,
            min_samples_leaf=2, n_jobs=-1,
        )),
    ])
    model.fit(Xtr, ytr)
    pred = model.predict(Xte)
    classes = sorted(y.unique())
    return model, {
        "accuracy": accuracy_score(yte, pred),
        "f1": f1_score(yte, pred, average="macro"),
        "classes": classes,
        "matrix": confusion_matrix(yte, pred, labels=classes),
    }


try:
    df = load_data()
except FileNotFoundError:
    st.error(f"Dataset tidak ditemukan di {BASE / 'dataset_StudentDOA.csv'}")
    st.stop()

missing = sorted(set(FEATURES + [TARGET]) - set(df.columns))
if missing:
    st.error("Kolom berikut tidak ditemukan: " + ", ".join(missing))
    st.stop()

model, metrics = fit_model(df)
counts = df[TARGET].value_counts()
tot = len(df)

a, b, c, d = st.columns(4)
a.metric("Mahasiswa", f"{tot:,}")
b.metric("Kolom", str(df.shape[1]))
c.metric("Kelas status", str(df[TARGET].nunique()))
d.metric("Nilai kosong", f"{int(df.isna().sum().sum()):,}")

tab1, tab2, tab3 = st.tabs(["Ringkasan", "Jelajahi data", "Demo prediksi"])

with tab1:
    left, right = st.columns(2)
    with left:
        st.subheader("Distribusi status akhir")
        chart = counts.rename(index=LABELS).rename_axis("Status").to_frame("Mahasiswa")
        st.bar_chart(chart)
        st.dataframe(pd.DataFrame({
            "Label": counts.index,
            "Status": [LABELS.get(str(x), str(x)) for x in counts.index],
            "Jumlah": counts.values,
            "Persentase": (counts.values / tot * 100).round(1),
        }), hide_index=True, use_container_width=True)
    with right:
        st.subheader("Usia saat masuk menurut status")
        age = df.groupby(["Age at enrollment", TARGET]).size().unstack(fill_value=0)
        st.line_chart(age.rename(columns=LABELS))
        st.subheader("Rata-rata mata kuliah lulus")
        approved = ["Curricular units 1st sem (approved)", "Curricular units 2nd sem (approved)"]
        avg = df.groupby(TARGET)[approved].mean().rename(index=LABELS)
        avg.columns = ["Semester 1", "Semester 2"]
        st.bar_chart(avg)
    st.info("Setiap baris mewakili seorang mahasiswa. Dataset memuat informasi pendaftaran, demografi, kondisi keuangan, hasil akademik dua semester, dan status akhir.")

with tab2:
    st.subheader("Filter status dan lihat tabel")
    chosen = st.multiselect("Status", list(counts.index), default=list(counts.index),
                            format_func=lambda x: f"{LABELS.get(str(x), x)} ({x})")
    view = df[df[TARGET].isin(chosen)]
    st.write(f"{len(view):,} dari {tot:,} baris")
    numeric = ["Age at enrollment", "Curricular units 1st sem (approved)",
               "Curricular units 1st sem (grade)", "Curricular units 2nd sem (approved)",
               "Curricular units 2nd sem (grade)"]
    summary = view.groupby(TARGET)[numeric].mean().round(2)
    summary.index = [LABELS.get(str(x), str(x)) for x in summary.index]
    st.markdown("**Rata-rata usia dan capaian akademik**")
    st.dataframe(summary, use_container_width=True)
    st.dataframe(view, use_container_width=True, height=420)
    st.download_button("Unduh data terfilter CSV", view.to_csv(index=False).encode("utf-8-sig"),
                       "studentdoa_filtered.csv", "text/csv")

with tab3:
    st.subheader("Demo prediksi status akhir")
    st.warning("Model demo memakai informasi pendaftaran dan semester pertama. Hasilnya untuk pembelajaran, bukan keputusan otomatis tentang mahasiswa.")
    x, y = st.columns(2)
    x.metric("Accuracy data uji", f"{metrics['accuracy']:.1%}")
    y.metric("Macro F1 data uji", f"{metrics['f1']:.3f}")
    st.caption("Model Random Forest; split stratified 80/20, seed 42. Fitur semester kedua tidak digunakan.")
    idx = st.selectbox("Pilih rekaman historis", range(tot),
                       format_func=lambda i: f"Rekaman {i+1} · usia {df.iloc[i]['Age at enrollment']} · aktual: {LABELS.get(str(df.iloc[i][TARGET]), df.iloc[i][TARGET])}")
    row = df.iloc[[idx]]
    probs = model.predict_proba(row[FEATURES])[0]
    classes = model.named_steps["rf"].classes_
    order = sorted(range(len(probs)), key=lambda i: probs[i], reverse=True)
    best = str(classes[order[0]])
    st.metric("Prediksi model", LABELS.get(best, best))
    result = pd.DataFrame({"Status": [LABELS.get(str(classes[i]), str(classes[i])) for i in order],
                           "Label": [classes[i] for i in order],
                           "Peluang (%)": [round(float(probs[i])*100, 1) for i in order]})
    st.bar_chart(result.set_index("Status")[["Peluang (%)"]])
    st.dataframe(result, hide_index=True, use_container_width=True)
    actual = str(row.iloc[0][TARGET])
    st.caption(f"Status aktual rekaman ini: **{LABELS.get(actual, actual)}**. Ini data historis, bukan prediksi bagi mahasiswa baru.")
    with st.expander("Confusion matrix pada data uji"):
        labs = metrics["classes"]
        cm = pd.DataFrame(metrics["matrix"],
                          index=[f"Aktual: {LABELS.get(str(z), z)}" for z in labs],
                          columns=[f"Prediksi: {LABELS.get(str(z), z)}" for z in labs])
        st.dataframe(cm, use_container_width=True)

st.divider()
st.caption("Catatan: kolom kategori berupa kode angka diproses sebagai kategori. Karena data semester kedua tidak digunakan, demo ini menggambarkan prediksi setelah semester pertama.")
