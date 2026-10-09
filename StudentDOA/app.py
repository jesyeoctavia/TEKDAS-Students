"""Dashboard Student Dropout Analysis: data, filter, dan machine learning."""
from pathlib import Path
import json

import joblib
import pandas as pd
import streamlit as st

from Data_Prev import CATEGORICAL_COLUMNS, FEATURE_COLUMNS, NUMERIC_COLUMNS, TARGET, load_data

BASE_DIR = Path(__file__).resolve().parent
LABELS = {"Dropout": "Berhenti", "Enrolled": "Masih terdaftar", "Graduate": "Lulus"}

st.set_page_config(page_title="Student Dropout Analysis", page_icon="🎓", layout="wide")
st.title("🎓 Student Dropout Analysis")
st.caption("Jelajahi data, pahami alur analisis, dan lihat demonstrasi klasifikasi status mahasiswa.")


@st.cache_data
def get_data():
    return load_data()


df = get_data()
counts = df[TARGET].value_counts()
total = len(df)

st.subheader("Alur analisis data")
steps = st.columns(5)
for col, number, title, detail in zip(steps, range(1, 6),
        ["Data Kaggle", "Pemeriksaan", "Pembersihan", "Pemodelan", "Interpretasi"],
        ["CSV mahasiswa", "Cek kolom, tipe, dan nilai kosong",
         "Rapikan nilai grade dan siapkan fitur", "Random Forest, split 80/20",
         "Evaluasi dan telaah pola" ]):
    col.markdown(f"**{number}. {title}**")
    col.caption(detail)
st.info("Model memakai informasi pendaftaran dan semester pertama untuk memprediksi status akhir. Data semester kedua tidak menjadi fitur model, agar evaluasi tidak memakai informasi masa depan.")

with st.expander("Apa yang dilakukan setiap tahap?", expanded=False):
    st.markdown("""
    1. **Data Kaggle:** membaca `dataset_StudentDOA.csv` dengan pemisah titik koma.
    2. **Pemeriksaan:** memastikan kolom yang diperlukan tersedia, melihat distribusi target dan nilai kosong.
    3. **Pembersihan:** mengubah format angka pada kolom nilai semester menjadi numerik. Kolom kode kategori diperlakukan sebagai kategori, bukan besaran.
    4. **Pemodelan:** membagi data secara stratified menjadi 80% latih dan 20% uji, lalu melatih Random Forest.
    5. **Interpretasi:** menampilkan metrik uji dan kepentingan fitur. Ini demo pembelajaran; prediksi bukan keputusan otomatis tentang mahasiswa.
    """)

a, b, c, d = st.columns(4)
a.metric("Jumlah mahasiswa", f"{total:,}")
b.metric("Jumlah kolom", str(df.shape[1]))
c.metric("Status akhir", str(df[TARGET].nunique()))
d.metric("Nilai kosong", f"{int(df.isna().sum().sum()):,}")

tab_overview, tab_explore, tab_model = st.tabs(["Ringkasan", "Filter & jelajahi data", "Machine Learning"])

with tab_overview:
    left, right = st.columns(2)
    with left:
        st.subheader("Distribusi status akhir")
        chart = counts.rename(index=LABELS).rename_axis("Status").to_frame("Mahasiswa")
        st.bar_chart(chart)
        st.dataframe(pd.DataFrame({
            "Status": [LABELS.get(str(x), str(x)) for x in counts.index],
            "Label data": counts.index,
            "Jumlah": counts.values,
            "Persentase": (counts.values / total * 100).round(1),
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

with tab_explore:
    st.subheader("Gunakan filter untuk memilih mahasiswa")
    f1, f2, f3 = st.columns(3)
    status_options = list(counts.index)
    selected_status = f1.multiselect("Status akhir", status_options, default=status_options,
                                     format_func=lambda x: f"{LABELS.get(str(x), x)} ({x})")
    age_min, age_max = int(df["Age at enrollment"].min()), int(df["Age at enrollment"].max())
    age_range = f2.slider("Rentang usia saat masuk", age_min, age_max, (age_min, age_max))
    course_options = sorted(df["Course"].dropna().unique().tolist())
    selected_courses = f3.multiselect("Kode program studi (Course)", course_options, default=course_options)
    f4, f5 = st.columns(2)
    debtor = f4.selectbox("Status utang", ["Semua", "Tidak berutang (0)", "Berutang (1)"])
    scholarship = f5.selectbox("Penerima beasiswa", ["Semua", "Tidak (0)", "Ya (1)"])

    view = df[df[TARGET].isin(selected_status)
              & df["Age at enrollment"].between(*age_range)
              & df["Course"].isin(selected_courses)]
    if debtor != "Semua":
        view = view[view["Debtor"] == (1 if debtor.startswith("Berutang") else 0)]
    if scholarship != "Semua":
        view = view[view["Scholarship holder"] == (1 if scholarship.startswith("Ya") else 0)]
    st.write(f"Menampilkan **{len(view):,}** dari **{total:,}** mahasiswa.")
    st.dataframe(view, use_container_width=True, height=420)
    st.download_button("Unduh hasil filter CSV", view.to_csv(index=False).encode("utf-8-sig"),
                       "studentdoa_filtered.csv", "text/csv")

with tab_model:
    st.subheader("Prediksi dan evaluasi model")
    model_path = BASE_DIR / "student_status_pipeline.pkl"
    metrics_path = BASE_DIR / "model_metrics.json"
    fi_path = BASE_DIR / "feature_importance.csv"
    if not model_path.exists() or not metrics_path.exists():
        st.warning("Artefak model belum tersedia. Jalankan `python Data_Prev.py`, lalu `python Ml_model.py` dari folder StudentDOA, kemudian muat ulang halaman.")
    else:
        model = joblib.load(model_path)
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        p, q = st.columns(2)
        p.metric("Accuracy data uji", f"{metrics['accuracy']:.1%}")
        q.metric("Macro F1 data uji", f"{metrics['macro_f1']:.3f}")
        st.caption("Evaluasi memakai data uji terpisah (20%), pembagian stratified, dan random state 42.")
        cm = pd.DataFrame(metrics["confusion_matrix"],
                          index=[f"Aktual: {LABELS.get(x, x)}" for x in metrics["labels"]],
                          columns=[f"Prediksi: {LABELS.get(x, x)}" for x in metrics["labels"]])
        st.markdown("**Confusion matrix (data uji)**")
        st.dataframe(cm, use_container_width=True)
        if fi_path.exists():
            st.markdown("**Fitur yang paling berpengaruh menurut model**")
            fi = pd.read_csv(fi_path).head(15).set_index("feature")
            st.bar_chart(fi["importance"])
        st.markdown("**Contoh prediksi dari satu baris data historis**")
        idx = st.selectbox("Pilih nomor baris", range(total),
                           format_func=lambda i: f"Baris {i + 1} · usia {df.iloc[i]['Age at enrollment']} · aktual: {LABELS.get(str(df.iloc[i][TARGET]), df.iloc[i][TARGET])}")
        row = df.iloc[[idx]]
        probs = model.predict_proba(row[FEATURE_COLUMNS])[0]
        classes = model.named_steps["model"].classes_
        order = sorted(range(len(probs)), key=lambda i: probs[i], reverse=True)
        best = str(classes[order[0]])
        st.metric("Prediksi model", LABELS.get(best, best))
        prob_df = pd.DataFrame({"Status": [LABELS.get(str(classes[i]), str(classes[i])) for i in order],
                                "Peluang (%)": [round(float(probs[i]) * 100, 1) for i in order]})
        st.bar_chart(prob_df.set_index("Status"))
        actual = str(row.iloc[0][TARGET])
        st.caption(f"Status aktual pada data historis: **{LABELS.get(actual, actual)}**. Ini bukan prediksi bagi mahasiswa baru.")

st.divider()
st.caption("Status target merupakan hasil akhir yang tercatat. Hubungan yang ditemukan model tidak membuktikan sebab-akibat.")
