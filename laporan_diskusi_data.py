from pathlib import Path
import csv
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "laporan_diskusi_data_csv.pdf"
FILES = [
    ("simulation/customers.csv", "Profil pelanggan dan label churn."),
    ("simulation/orders.csv", "Rincian transaksi, produk, pembayaran, pengiriman, retur, dan rating."),
    ("simulation/monthly_revenue.csv", "Agregat pesanan dan pendapatan per bulan."),
    ("simulation/product_summary.csv", "Ringkasan performa per produk."),
    ("simulation/customer_ml_dataset.csv", "Dataset pelanggan hasil rekayasa fitur untuk pemodelan churn."),
    ("simulation/customer_train.csv", "Subset untuk melatih model churn."),
    ("simulation/customer_test.csv", "Subset untuk mengevaluasi model churn."),
]

def inspect(rel):
    with (ROOT / rel).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        cols = next(reader)
        count = sum(1 for _ in reader)
    return count, cols

S = getSampleStyleSheet()
S.add(ParagraphStyle(name="TitleX", parent=S["Title"], fontSize=23, leading=28, textColor=colors.HexColor("#16324F"), alignment=TA_CENTER))
S.add(ParagraphStyle(name="HeadX", parent=S["Heading1"], fontSize=15, leading=19, textColor=colors.HexColor("#16324F"), spaceAfter=8))
S.add(ParagraphStyle(name="BodyX", parent=S["BodyText"], fontSize=9, leading=13, spaceAfter=5))
S.add(ParagraphStyle(name="CellX", parent=S["BodyText"], fontSize=7.2, leading=9.2))
S.add(ParagraphStyle(name="ListX", parent=S["BodyText"], fontSize=8.1, leading=11, wordWrap="CJK"))
S.add(ParagraphStyle(name="THX", parent=S["BodyText"], fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=colors.white))

def P(text, style="BodyX"):
    return Paragraph(text, S[style])

def footer(c, d):
    c.saveState()
    c.setStrokeColor(colors.HexColor("#D7E0E8"))
    c.line(1.7*cm, 1.35*cm, A4[0]-1.7*cm, 1.35*cm)
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#607080"))
    c.drawString(1.7*cm, .95*cm, "Rangkuman diskusi data CSV")
    c.drawRightString(A4[0]-1.7*cm, .95*cm, f"Halaman {d.page}")
    c.restoreState()

info = [(rel, desc, *inspect(rel)) for rel, desc in FILES]
doc = SimpleDocTemplate(str(OUT), pagesize=A4, rightMargin=1.7*cm, leftMargin=1.7*cm, topMargin=1.5*cm, bottomMargin=1.8*cm, title="Rangkuman Diskusi Data CSV", author="OpenAI")
story = [Spacer(1, 1.1*cm), P("Rangkuman Diskusi<br/>Data CSV", "TitleX"), P("Isi, ukuran, dan kolom dataset pelanggan dan penjualan", "BodyX"), Spacer(1, .35*cm), P("Laporan ini merangkum pembahasan tujuh file CSV di folder <b>simulation</b>: empat file sumber/ringkasan penjualan dan tiga file pelanggan untuk pemodelan churn.")]
rows = [[P("File", "THX"), P("Baris", "THX"), P("Kolom", "THX"), P("Isi", "THX")]]
for rel, desc, n, cols in info:
    rows.append([P("<b>"+escape(Path(rel).name)+"</b>", "CellX"), P(f"{n:,}", "CellX"), P(str(len(cols)), "CellX"), P(escape(desc), "CellX")])
t = Table(rows, colWidths=[4.2*cm, 1.5*cm, 1.4*cm, 8.7*cm], repeatRows=1)
t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#16324F")),("GRID",(0,0),(-1,-1),.35,colors.HexColor("#C7D2DC")),("VALIGN",(0,0),(-1,-1),"TOP"),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F3F7FA")]),("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
story += [Spacer(1,.25*cm), t, Spacer(1,.2*cm), P("Baris yang ditampilkan adalah jumlah baris data, tidak termasuk header. Penulisan <i>customer_ml_dataset.scv</i> dipahami sebagai <b>customer_ml_dataset.csv</b>, sesuai nama file yang tersedia.")]
story += [PageBreak(), P("Kolom per file", "HeadX"), P("Empat CSV penjualan memiliki skema yang berbeda sesuai tingkat detailnya.")]
for rel, desc, n, cols in info[:4]:
    story.append(KeepTogether([P(f"<b>{escape(Path(rel).name)}</b> — {n:,} baris × {len(cols)} kolom"), P(escape(desc), "CellX"), P("<b>Kolom:</b> "+", ".join(escape(c) for c in cols), "ListX"), Spacer(1,.18*cm)]))
story += [PageBreak(), P("Kolom dataset pelanggan", "HeadX"), P("Tiga file pelanggan memiliki 23 kolom yang sama. Dataset lengkap berisi 8.000 baris; pembagian train dan test berisi 6.400 dan 1.600 baris.")]
for rel, desc, n, cols in info[4:]:
    story.append(KeepTogether([P(f"<b>{escape(Path(rel).name)}</b> — {n:,} baris × {len(cols)} kolom"), P(escape(desc), "CellX"), P("<b>Kolom:</b> "+", ".join(escape(c) for c in cols), "ListX"), Spacer(1,.22*cm)]))
story.append(P("<b>Kolom penting:</b> <i>customer_id</i> adalah ID pelanggan; kolom profil dan preferensi menjelaskan karakteristik pelanggan; kolom aktivitas seperti <i>total_orders</i>, <i>total_spend_usd</i>, dan <i>days_since_last_purchase</i> merangkum perilaku belanja; kolom tenure dan rasio merupakan fitur turunan; <i>churned</i> adalah label churn."))
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT)
