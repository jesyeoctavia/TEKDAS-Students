"""Membangun PDF laporan dari status implementasi proyek saat ini."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)


BASE_DIR = Path(__file__).resolve().parent
OUTPUT = BASE_DIR / "Laporan_Proyek_Adaptasi.pdf"


def p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def section(title: str, styles: dict) -> list:
    return [Spacer(1, 0.2 * cm), p(title, styles["Heading1"]), Spacer(1, 0.08 * cm)]


def table(rows: list[list[str]], widths: list[float], styles: dict) -> Table:
    rendered = [[p(cell, styles["Cell"]) for cell in row] for row in rows]
    result = Table(rendered, colWidths=widths, repeatRows=1, hAlign="LEFT")
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16324F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#B9C7D3")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F4F7F9")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return result


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#B9C7D3"))
    canvas.line(2 * cm, 1.45 * cm, A4[0] - 2 * cm, 1.45 * cm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#49657B"))
    canvas.drawString(2 * cm, 0.95 * cm, "Laporan Proyek Adaptasi | Teknologi Cerdas")
    canvas.drawRightString(A4[0] - 2 * cm, 0.95 * cm, f"Halaman {doc.page}")
    canvas.restoreState()


def build() -> None:
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4, rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=1.8 * cm, bottomMargin=2 * cm,
        title="Laporan Proyek Adaptasi - Teknologi Cerdas",
        author="Mahasiswa (belum diisi)",
    )
    base = getSampleStyleSheet()
    styles = {
        "Title": ParagraphStyle("Title", parent=base["Title"], fontName="Helvetica-Bold",
                                fontSize=23, leading=28, alignment=TA_CENTER,
                                textColor=colors.HexColor("#16324F"), spaceAfter=14),
        "Subtitle": ParagraphStyle("Subtitle", parent=base["Normal"], fontSize=11,
                                   leading=15, alignment=TA_CENTER, textColor=colors.HexColor("#49657B")),
        "Heading1": ParagraphStyle("Heading1", parent=base["Heading1"], fontName="Helvetica-Bold",
                                    fontSize=14, leading=17, textColor=colors.HexColor("#16324F"), spaceBefore=8),
        "Body": ParagraphStyle("Body", parent=base["BodyText"], fontSize=10, leading=14,
                               alignment=TA_JUSTIFY, spaceAfter=7),
        "Cell": ParagraphStyle("Cell", parent=base["BodyText"], fontSize=8.5, leading=11),
        "Note": ParagraphStyle("Note", parent=base["BodyText"], fontSize=9, leading=12,
                               textColor=colors.HexColor("#6B3B00"), backColor=colors.HexColor("#FFF4D6"),
                               borderColor=colors.HexColor("#E0B35B"), borderWidth=0.5, borderPadding=7),
        "Code": ParagraphStyle("Code", parent=base["Code"], fontName="Courier", fontSize=8.5,
                               leading=12, backColor=colors.HexColor("#F1F4F6"), borderPadding=7),
    }
    story = []
    story += [Spacer(1, 3.0 * cm), p("LAPORAN PROYEK ADAPTASI", styles["Title"]),
              p("Pipeline Data, Machine Learning, LLM Grounding, dan Dashboard", styles["Subtitle"]),
              Spacer(1, 1.1 * cm)]
    story.append(table([
        ["Item", "Keterangan"],
        ["Mata kuliah", "Teknologi Cerdas"],
        ["Track", "Adapt"],
        ["Lokasi proyek", "proyek_adaptasi/"],
        ["Penyusun", "Belum diisi"],
        ["Tanggal laporan", "21 September 2026"],
    ], [4.1 * cm, 11.9 * cm], styles))
    story += [Spacer(1, 1 * cm), p("Status dokumen: rancangan implementasi", styles["Heading1"]),
              p("Laporan ini dibuat berdasarkan pemeriksaan kode pada repository. Dataset mentah, konfigurasi dataset, dan artefak pelatihan belum tersedia; karena itu tidak ada angka performa atau klaim hasil eksperimen yang dicantumkan.", styles["Note"]), PageBreak()]

    story += section("1. Ringkasan Eksekutif", styles)
    story.append(p("Proyek ini menyediakan kerangka kerja aplikasi teknologi cerdas untuk masalah klasifikasi yang akan diadaptasi ke dataset baru. Alurnya mencakup validasi data, pembersihan dan pemisahan data, pelatihan baseline serta Random Forest, evaluasi model, penyimpanan artefak, dashboard Streamlit, dan analisis bahasa alami berbasis LLM lokal melalui Ollama.", styles["Body"]))
    story.append(p("Pada kondisi repository saat laporan ini dibuat, nama dataset, target, fitur, stakeholder, metrik utama, dan konteks aplikasi masih belum ditentukan. Dengan demikian, artefak ini berfungsi sebagai laporan desain dan checklist implementasi; bagian hasil wajib diperbarui setelah kontrak data diisi dan eksperimen dijalankan.", styles["Body"]))

    story += section("2. Ruang Lingkup dan Tujuan", styles)
    story.append(table([
        ["Komponen", "Peran dalam sistem"],
        ["Data", "CSV lokal pada data/raw/; diperiksa terhadap kontrak konfigurasi."],
        ["Data preparation", "Memilih kolom, menghapus duplikat, menghapus target kosong, dan menghasilkan split train/test."],
        ["Machine learning", "Membandingkan DummyClassifier (baseline) dengan RandomForestClassifier."],
        ["LLM", "Menyusun prompt grounded dari record, prediksi, dan metrik; pemanggilan Ollama bersifat opsional."],
        ["Aplikasi", "Dashboard Streamlit untuk data, BI, prediksi per baris, dan analisis grounded."],
    ], [3.6 * cm, 12.4 * cm], styles))

    story += section("3. Arsitektur Sistem", styles)
    story.append(p("Arsitektur yang diimplementasikan di kode adalah sebagai berikut.", styles["Body"]))
    story.append(p("CSV mentah -> validasi konfigurasi -> cleaning dan split -> pipeline preprocessing + model -> artefak model/metrics/prediksi -> dashboard Streamlit. Pada dashboard, record dan output ML menjadi evidence untuk prompt LLM -> Ollama -> analisis untuk pengguna.", styles["Code"]))
    story.append(p("Pemisahan preprocessing dan model dilakukan memakai sklearn Pipeline sehingga imputer dan encoder dipelajari dari data latih. Pendekatan ini membantu menghindari kebocoran informasi dari test set saat pelatihan.", styles["Body"]))

    story += section("4. Data dan Persiapan", styles)
    story.append(p("Kontrak data berada pada config.py. Konfigurasi saat ini masih berisi placeholder: DATA_FILENAME dan TARGET belum diisi, daftar fitur numerik/kategorikal kosong, dan TASK ditetapkan sebagai classification. Fungsi validate_config() menghentikan proses lebih awal apabila placeholder tersebut belum diganti.", styles["Body"]))
    story.append(table([
        ["Tahap", "Implementasi saat ini", "Catatan adaptasi"],
        ["Validasi", "Memastikan file, kolom wajib, data tidak kosong, dan minimal dua kelas target.", "Isi data dictionary dan semantik semua fitur."],
        ["Cleaning", "Memilih fitur/target/ID, menghapus baris duplikat dan target kosong.", "Tambahkan aturan nilai tidak valid/outlier sesuai domain."],
        ["Split", "train_test_split 80/20, random_state=42, stratified pada target.", "Ganti menjadi group/time split bila observasi tidak independen."],
        ["Kualitas", "Menyimpan data_quality.json: jumlah baris, duplikat, distribusi target, dan missing value.", "Interpretasikan laporan kualitas setelah dataset tersedia."],
    ], [2.5 * cm, 7.0 * cm, 6.5 * cm], styles))

    story += section("5. Metode Machine Learning", styles)
    story.append(p("Fitur numerik diimputasi menggunakan median. Fitur kategorikal diimputasi menggunakan nilai paling sering lalu di-one-hot encoding dengan handle_unknown='ignore'. Baseline memakai DummyClassifier(strategy='most_frequent'). Model utama memakai RandomForestClassifier dengan 300 trees, class_weight='balanced', random_state=42, dan n_jobs=-1.", styles["Body"]))
    story.append(p("Evaluasi yang telah disediakan adalah accuracy, macro F1, confusion matrix, dan classification report per kelas. Metrik utama belum ditetapkan; pemilihannya harus mengikuti biaya kesalahan stakeholder. Contohnya, recall relevan bila false negative mahal, sedangkan precision relevan bila tindak lanjut positif mahal.", styles["Body"]))

    story += section("6. Aplikasi dan Integrasi LLM", styles)
    story.append(p("Aplikasi Streamlit memverifikasi keberadaan dataset dan artefak sebelum menampilkan empat tab: Data, BI, ML, dan LLM. Tab Data menampilkan preview serta missing value. Tab ML menjalankan prediksi pada satu baris. Tab BI dan judul aplikasi masih placeholder sehingga perlu dirancang ulang agar sesuai pertanyaan stakeholder.", styles["Body"]))
    story.append(p("Prompt LLM mengirimkan JSON yang berisi record fitur, prediksi model, dan evaluasi model. Instruksi prompt membatasi model agar menggunakan evidence yang diberikan, membedakan bukti/inferensi/rekomendasi, menyatakan kekurangan bukti, dan membatasi rekomendasi hingga tiga tindakan. Ini adalah mekanisme grounding, tetapi tetap perlu diuji terhadap kasus nyata untuk mendeteksi klaim yang tidak didukung.", styles["Body"]))

    story += section("7. Hasil dan Status Verifikasi", styles)
    story.append(table([
        ["Artefak yang diharapkan", "Status saat diperiksa", "Implikasi"],
        ["data/raw/<dataset>.csv", "Belum ada (hanya .gitkeep)", "Profil data belum dapat dibuat."],
        ["data/processed/train.csv dan test.csv", "Belum ada", "Pipeline persiapan belum dijalankan."],
        ["artifacts/model.joblib", "Belum ada", "Prediksi dashboard belum dapat digunakan."],
        ["artifacts/metrics.json", "Belum ada", "Tidak ada metrik yang sah untuk dilaporkan."],
        ["artifacts/predictions.csv", "Belum ada", "Analisis error belum dapat dilakukan."],
    ], [5.0 * cm, 4.2 * cm, 6.8 * cm], styles))
    story.append(p("Kesimpulan performa belum dapat dibuat. Tabel eksperimen, confusion matrix, threshold analysis, dan evaluasi LLM harus diisi hanya dari artifacts yang dihasilkan pada run yang dapat direproduksi.", styles["Note"]))

    story += section("8. Reproduksibilitas", styles)
    story.append(p("Setelah kontrak data lengkap, jalankan perintah berikut dari folder proyek_adaptasi.", styles["Body"]))
    story.append(p("python -m pip install -r requirements.txt<br/>python data_prep.py<br/>python train.py<br/>python llm.py --prompt-only<br/>streamlit run app.py", styles["Code"]))
    story.append(p("Dependensi proyek merujuk requirements tingkat repository dan requirements simulation. Untuk reproduksibilitas yang lebih kuat, dokumentasikan versi Python, versi paket aktual, checksum dataset, tanggal akses data, seed, serta model Ollama yang digunakan.", styles["Body"]))

    story += section("9. Risiko, Etika, dan Keterbatasan", styles)
    story.append(p("Karena dataset belum ditentukan, risiko privasi, fairness, representativitas, dan lisensi belum dapat dinilai secara spesifik. Sebelum deployment, Data Card perlu menjelaskan sumber/izin, unit observasi, periode/wilayah, potensi bias sampling dan measurement, kolom sensitif, serta batas penggunaan. Keputusan penting tidak boleh diotomatisasi sepenuhnya; pengguna perlu dapat meninjau evidence, prediksi, dan keterbatasannya.", styles["Body"]))
    story.append(p("Keterbatasan teknis saat ini: scaffold hanya mendukung classification, split masih acak, model tidak menyimpan probabilitas/threshold analysis, dan UX/BI belum disesuaikan ke domain. LLM dapat tetap menghasilkan penjelasan yang tampak meyakinkan, sehingga evaluasi konsistensi evidence dan human override diperlukan.", styles["Body"]))

    story += section("10. Kesimpulan dan Tindak Lanjut", styles)
    story.append(p("Repository telah menyediakan fondasi end-to-end yang baik untuk proyek klasifikasi adaptif: pemisahan data, preprocessing dalam pipeline, baseline, model utama, dashboard, dan prompt grounded. Namun proyek belum dapat dinilai sebagai implementasi substansif karena konfigurasi dan data belum diisi serta eksperimen belum dijalankan.", styles["Body"]))
    story.append(p("Prioritas selanjutnya adalah: (1) memilih dataset berizin dan melengkapi Data Card; (2) mengisi config.py berdasarkan semantik data; (3) menyesuaikan cleaning, split, metrik, BI, dan prompt; (4) menjalankan eksperimen; dan (5) mengganti bagian status pada laporan ini dengan hasil terukur.", styles["Body"]))
    story += section("Lampiran: Berkas yang Ditinjau", styles)
    story.append(p("app.py, config.py, data_prep.py, train.py, llm.py, README.md, DATA_CARD.md, requirements.txt, serta struktur folder data/ dan artifacts/.", styles["Body"]))
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    build()
    print(f"PDF dibuat: {OUTPUT}")
