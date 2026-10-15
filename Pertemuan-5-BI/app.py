from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Coffee Shop Sales", layout="wide")
st.title("Dashboard Coffee Shop Sales")
st.caption("Januari-Juni 2023. Mata uang belum dinyatakan pada file.")

folder = Path(__file__).resolve().parent
file_data = folder / "data_prepared" / "coffee_sales_prepared.csv"


@st.cache_data
def load_data(path, modified_time):
    data = pd.read_csv(path)
    data["transaction_date"] = pd.to_datetime(data["transaction_date"])
    return data


if not file_data.exists():
    st.error("Jalankan audit. File coffee_sales_prepared.csv belum ada.")
    st.stop()

df = load_data(str(file_data), file_data.stat().st_mtime_ns)

# Filter gerai berlaku untuk seluruh grafik dan indikator.
st.sidebar.header("Filter data")
stores = sorted(df["store_location"].unique().tolist())
selected = st.sidebar.multiselect("Pilih gerai", stores, default=stores)
if not selected:
    st.info("Pilih minimal satu gerai.")
    st.stop()

data_filter = df[df["store_location"].isin(selected)].copy()
st.sidebar.caption("Semua grafik mengikuti pilihan gerai.")

# Bulan selalu mengikuti cakupan sumber, termasuk bulan tanpa catatan.
months = pd.period_range(
    df["transaction_date"].min().to_period("M"),
    df["transaction_date"].max().to_period("M"),
    freq="M",
).astype(str).tolist()

monthly = data_filter.groupby("month").agg(
    total_sales=("sales", "sum"),
    total_transactions=("transaction_id", "nunique"),
    total_units=("transaction_qty", "sum"),
).reindex(months)

previous = monthly["total_sales"].shift(1)
monthly["growth_pct"] = (
    (monthly["total_sales"] - previous) / previous * 100
).where(previous.notna() & previous.ne(0))
monthly["average_transaction_value"] = (
    monthly["total_sales"] / monthly["total_transactions"]
)
monthly = monthly.reset_index()
monthly = monthly.rename(columns={monthly.columns[0]: "month"})


def format_angka(value, decimals=2):
    return (f"{value:,.{decimals}f}".replace(",", "_")
            .replace(".", ",").replace("_", "."))


total_sales = data_filter["sales"].sum()
total_transactions = data_filter["transaction_id"].nunique()
average = total_sales / total_transactions if total_transactions else None
growth = monthly["growth_pct"].iloc[-1]
last_month = pd.Period(months[-1], freq="M")

st.subheader("Ringkasan penjualan")
st.caption(
    "Total, transaksi, dan rata-rata: seluruh periode. "
    f"Pertumbuhan: {last_month} terhadap {last_month - 1}."
)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total penjualan", format_angka(total_sales))
col2.metric("Transaksi tercatat", format_angka(total_transactions, 0))
col3.metric("Rata-rata nilai transaksi",
            format_angka(average) if average is not None else "Belum tersedia")
col4.metric(f"Pertumbuhan {last_month} terhadap {last_month - 1}",
            f"{format_angka(growth)}%" if pd.notna(growth) else "Belum tersedia")

st.subheader("Tren penjualan bulanan")
fig = px.line(monthly, x="month", y="total_sales", markers=True,
              labels={"month": "Bulan", "total_sales": "Nilai penjualan"})
fig.update_traces(line_color="#087F8C", connectgaps=False)
fig.update_layout(xaxis_type="category", yaxis_rangemode="tozero")
st.plotly_chart(fig, width="stretch", key="trend")

with st.expander("Lihat angka ringkasan bulanan"):
    table = monthly.rename(columns={
        "month": "Bulan",
        "total_sales": "Total penjualan",
        "total_transactions": "Transaksi tercatat",
        "total_units": "Unit terjual",
        "growth_pct": "Pertumbuhan (%)",
        "average_transaction_value": "Rata-rata nilai transaksi",
    })
    st.dataframe(
        table.style.format({
            "Total penjualan": "{:,.2f}",
            "Transaksi tercatat": "{:,.0f}",
            "Unit terjual": "{:,.0f}",
            "Pertumbuhan (%)": "{:,.2f}",
            "Rata-rata nilai transaksi": "{:,.2f}",
        }, na_rep="Belum tersedia", decimal=",", thousands="."),
        width="stretch", hide_index=True)

st.divider()
st.header("Perbandingan gerai dan kategori")
left, right = st.columns(2)

with left:
    st.subheader("Penjualan per gerai")
    sales_by_store = data_filter.groupby("store_location", as_index=False).agg(
        total_sales=("sales", "sum")
    ).sort_values("total_sales", ascending=False)
    fig_store = px.bar(
        sales_by_store, x="store_location", y="total_sales",
        color="store_location", text_auto=".2s",
        labels={"store_location": "Gerai", "total_sales": "Nilai penjualan"},
        color_discrete_sequence=["#087F8C", "#7656B5", "#D98B39"])
    fig_store.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig_store, width="stretch", key="stores")
    st.caption("Hanya gerai yang dipilih muncul pada grafik.")

with right:
    st.subheader("Kontribusi penjualan kategori")
    sales_by_category = data_filter.groupby(
        "product_category", as_index=False
    ).agg(total_sales=("sales", "sum")).sort_values(
        "total_sales", ascending=False
    )
    fig_category = px.pie(sales_by_category, names="product_category",
                          values="total_sales", hole=0.55)
    fig_category.update_traces(textinfo="none", hovertemplate=(
        "%{label}<br>Penjualan: %{value:,.2f}<br>"
        "Kontribusi: %{percent}<extra></extra>"
    ))
    fig_category.update_layout(height=400, legend_title_text="Kategori")
    st.plotly_chart(fig_category, width="stretch", key="categories")
    st.caption("Kontribusi terhadap total dalam pilihan gerai yang sama.")

st.header("Produk dan pola waktu transaksi")
left, right = st.columns(2)

with left:
    st.subheader("10 produk dengan penjualan tertinggi")
    top_products = data_filter.groupby(
        ["product_id", "product_detail"], as_index=False
    ).agg(total_sales=("sales", "sum")).nlargest(
        10, "total_sales"
    ).sort_values("total_sales", ascending=True)
    top_products["label"] = (top_products["product_detail"] + " ("
                             + top_products["product_id"].astype(str) + ")")
    fig_products = px.bar(
        top_products, x="total_sales", y="label", orientation="h",
        color_discrete_sequence=["#7656B5"],
        labels={"total_sales": "Nilai penjualan", "label": "Produk"})
    fig_products.update_layout(height=470, yaxis={
        "categoryorder": "array",
        "categoryarray": top_products["label"].tolist(),
    })
    st.plotly_chart(fig_products, width="stretch", key="products")
    st.caption("Peringkat nilai penjualan, bukan unit atau keuntungan.")

with right:
    st.subheader("Transaksi tercatat menurut jam")
    by_hour = data_filter.groupby("hour", as_index=False).agg(
        total_transactions=("transaction_id", "nunique")
    ).sort_values("hour")
    by_hour["label"] = by_hour["hour"].astype(int).astype(str).str.zfill(2) + ":00"
    fig_hour = px.bar(
        by_hour, x="label", y="total_transactions",
        color_discrete_sequence=["#D98B39"],
        labels={"label": "Jam", "total_transactions": "Transaksi tercatat"})
    fig_hour.update_layout(height=470, xaxis_type="category")
    st.plotly_chart(fig_hour, width="stretch", key="hours")
    st.caption("Akumulasi sepanjang periode, belum mengukur antrean layanan.")

st.caption(
    "Transaksi tercatat adalah transaction_id unik, bukan pelanggan unik. "
    "Rata-rata nilainya belum dipastikan sebagai seluruh isi struk pelanggan."
)

# =====================================================================
# TAMBAHAN FITUR EKSEKUTIF (hanya penambahan; kode di atas tidak diubah)
# Bagian ini tetap mengikuti filter gerai di sidebar (data_filter).
# =====================================================================
st.divider()
st.header("Eksplorasi lanjutan untuk eksekutif")
st.caption(
    "Bagian ini tetap mengikuti pilihan gerai di sidebar. "
    "Filter bulan dan kategori di sidebar hanya berlaku untuk bagian ini."
)

# --- Fitur 2: filter bulan dan kategori ---
ex_all_categories = sorted(data_filter["product_category"].unique().tolist())
with st.sidebar:
    st.divider()
    st.subheader("Filter eksplorasi lanjutan")
    ex_months = st.multiselect("Pilih bulan", months, default=months,
                               key="ex_months")
    ex_cats = st.multiselect("Pilih kategori", ex_all_categories,
                             default=ex_all_categories, key="ex_cats")
    st.caption("Hanya berlaku untuk bagian Eksplorasi lanjutan untuk eksekutif.")
if not ex_months or not ex_cats:
    st.info("Pilih minimal satu bulan dan satu kategori.")
    st.stop()

ex_data = data_filter[
    data_filter["month"].isin(ex_months)
    & data_filter["product_category"].isin(ex_cats)
].copy()
if ex_data.empty:
    st.info("Tidak ada transaksi pada kombinasi filter ini.")
    st.stop()

# Pertumbuhan dihitung SEBELUM data dipotong per bulan, agar bulan
# pembanding tidak hilang (gerai dan kategori sama).
ex_cat_monthly = (
    data_filter[data_filter["product_category"].isin(ex_cats)]
    .groupby("month")["sales"].sum().reindex(months)
)
ex_last = max(ex_months)
ex_prev = str(pd.Period(ex_last, freq="M") - 1)
ex_cur_val = ex_cat_monthly.get(ex_last)
ex_prev_val = ex_cat_monthly.get(ex_prev)
ex_growth = None
if (ex_cur_val is not None and ex_prev_val is not None
        and pd.notna(ex_cur_val) and pd.notna(ex_prev_val) and ex_prev_val != 0):
    ex_growth = (ex_cur_val - ex_prev_val) / ex_prev_val * 100

ex_total = ex_data["sales"].sum()
ex_trx = ex_data["transaction_id"].nunique()
ex_avg = ex_total / ex_trx if ex_trx else None

st.subheader("Ringkasan sesuai filter bulan dan kategori")
ex_c1, ex_c2, ex_c3, ex_c4 = st.columns(4)
ex_c1.metric("Total penjualan", format_angka(ex_total))
ex_c2.metric("Transaksi tercatat", format_angka(ex_trx, 0))
ex_c3.metric("Rata-rata nilai transaksi",
             format_angka(ex_avg) if ex_avg is not None else "Belum tersedia")
ex_c4.metric(f"Pertumbuhan {ex_last} terhadap {ex_prev}",
             f"{format_angka(ex_growth)}%" if ex_growth is not None
             else "Belum tersedia")
st.caption(
    "Total, transaksi, dan rata-rata: bulan dan kategori terpilih. "
    "Pertumbuhan: bulan terpilih terakhir terhadap bulan sebelumnya pada "
    "gerai dan kategori yang sama, termasuk jika bulan sebelumnya tidak dipilih."
)

# Ringkasan per produk, dipakai oleh pencarian, peringkat, dan unduhan.
ex_prod = ex_data.groupby(["product_id", "product_detail"], as_index=False).agg(
    total_sales=("sales", "sum"),
    total_units=("transaction_qty", "sum"),
    total_transactions=("transaction_id", "nunique"),
    price_min=("unit_price", "min"),
    price_max=("unit_price", "max"),
)
ex_prod["rank"] = ex_prod["total_sales"].rank(
    ascending=False, method="min").astype(int)
ex_prod["share_pct"] = ex_prod["total_sales"] / ex_prod["total_sales"].sum() * 100
ex_prod["price_varies"] = ex_prod["price_min"].ne(ex_prod["price_max"])
ex_prod = ex_prod.sort_values("total_sales", ascending=False)

# --- Fitur 1: pencarian produk ---
st.divider()
st.subheader("Cari produk")
ex_query = st.text_input(
    "Ketik nama atau ID produk (contoh: latte, 39)", key="ex_query"
).strip()
if ex_query:
    ex_mask = (
        ex_prod["product_detail"].str.contains(ex_query, case=False, regex=False)
        | ex_prod["product_id"].astype(str).str.contains(ex_query, regex=False)
    )
    ex_found = ex_prod[ex_mask].copy()
    if ex_found.empty:
        st.warning("Produk tidak ditemukan pada gerai, bulan, dan kategori terpilih.")
    else:
        ex_found["product_id"] = ex_found["product_id"].astype(str)
        ex_found["rank"] = ex_found["rank"].astype(str)
        ex_found["price_varies"] = ex_found["price_varies"].map(
            {True: "Ya", False: "Tidak"})
        ex_show = ex_found.rename(columns={
            "product_detail": "Produk", "product_id": "ID",
            "rank": "Peringkat penjualan", "total_sales": "Penjualan",
            "share_pct": "Kontribusi (%)", "total_units": "Unit terjual",
            "total_transactions": "Transaksi tercatat",
            "price_min": "Harga terendah", "price_max": "Harga tertinggi",
            "price_varies": "Harga bervariasi",
        })[["Produk", "ID", "Peringkat penjualan", "Penjualan", "Kontribusi (%)",
            "Unit terjual", "Transaksi tercatat", "Harga terendah",
            "Harga tertinggi", "Harga bervariasi"]]
        st.dataframe(
            ex_show.style.format({
                "Penjualan": "{:,.2f}", "Kontribusi (%)": "{:,.2f}",
                "Unit terjual": "{:,.0f}", "Transaksi tercatat": "{:,.0f}",
                "Harga terendah": "{:,.2f}", "Harga tertinggi": "{:,.2f}",
            }, decimal=",", thousands="."),
            width="stretch", hide_index=True)
        st.caption(
            f"{len(ex_found)} produk cocok. Peringkat dan kontribusi dihitung "
            f"terhadap {len(ex_prod)} produk pada filter yang sama. "
            "Harga bervariasi dicatat sebagai informasi, belum tentu kesalahan."
        )
else:
    st.caption("Hasil pencarian muncul di sini setelah Anda mengetik.")

# --- Fitur 3: produk teratas dan terbawah ---
st.divider()
st.subheader("Produk teratas dan terbawah")
ex_o1, ex_o2, ex_o3 = st.columns(3)
ex_basis = ex_o1.radio("Dasar peringkat", ["Nilai penjualan", "Unit terjual"],
                       horizontal=True, key="ex_basis")
ex_dir = ex_o2.radio("Tampilkan", ["Teratas", "Terbawah"],
                     horizontal=True, key="ex_dir")
ex_n = ex_o3.slider("Jumlah produk", 3, 20, 10, key="ex_n")
ex_col = "total_sales" if ex_basis == "Nilai penjualan" else "total_units"
ex_rank_df = ex_prod.copy()
ex_rank_df["label"] = (ex_rank_df["product_detail"] + " ("
                       + ex_rank_df["product_id"].astype(str) + ")")
if ex_dir == "Teratas":
    ex_rank_df = ex_rank_df.nlargest(ex_n, ex_col).sort_values(
        ex_col, ascending=True)
    ex_color = "#7656B5"
else:
    ex_rank_df = ex_rank_df.nsmallest(ex_n, ex_col).sort_values(
        ex_col, ascending=False)
    ex_color = "#D98B39"
fig_rank = px.bar(
    ex_rank_df, x=ex_col, y="label", orientation="h",
    color_discrete_sequence=[ex_color],
    labels={ex_col: ex_basis, "label": "Produk"})
fig_rank.update_layout(height=max(320, 40 * len(ex_rank_df) + 120), yaxis={
    "categoryorder": "array",
    "categoryarray": ex_rank_df["label"].tolist(),
})
st.plotly_chart(fig_rank, width="stretch", key="ex_rank")
st.caption(
    f"{ex_dir} {len(ex_rank_df)} produk menurut {ex_basis.lower()} pada gerai, "
    "bulan, dan kategori terpilih. Produk dengan nilai tinggi belum tentu "
    "paling banyak terjual, dan data belum memuat biaya sehingga laba "
    "belum dapat dinilai."
)

# --- Fitur 5: drill-down kategori -> jenis -> produk ---
st.divider()
st.subheader("Telusuri kategori ke jenis ke produk")
st.caption("Pilih kategori, lalu jenis produk, untuk melihat tingkat detail berikutnya.")

ex_lvl1 = ex_data.groupby("product_category", as_index=False).agg(
    total_sales=("sales", "sum")).sort_values("total_sales", ascending=True)
fig_l1 = px.bar(ex_lvl1, x="total_sales", y="product_category", orientation="h",
                color_discrete_sequence=["#087F8C"], text_auto=",.0f",
                labels={"total_sales": "Nilai penjualan",
                        "product_category": "Kategori"})
fig_l1.update_layout(height=max(280, 36 * len(ex_lvl1) + 120))
st.plotly_chart(fig_l1, width="stretch", key="ex_l1")

ex_cat_choice = st.selectbox(
    "Kategori yang ditelusuri",
    ex_lvl1.sort_values("total_sales", ascending=False)["product_category"].tolist(),
    key="ex_cat_choice")
ex_in_cat = ex_data[ex_data["product_category"] == ex_cat_choice]
ex_lvl2 = ex_in_cat.groupby("product_type", as_index=False).agg(
    total_sales=("sales", "sum")).sort_values("total_sales", ascending=True)
fig_l2 = px.bar(ex_lvl2, x="total_sales", y="product_type", orientation="h",
                color_discrete_sequence=["#7656B5"], text_auto=",.0f",
                labels={"total_sales": "Nilai penjualan",
                        "product_type": "Jenis produk"})
fig_l2.update_layout(height=max(280, 36 * len(ex_lvl2) + 120))
st.plotly_chart(fig_l2, width="stretch", key="ex_l2")

ex_type_choice = st.selectbox(
    "Jenis produk yang ditelusuri",
    ex_lvl2.sort_values("total_sales", ascending=False)["product_type"].tolist(),
    key="ex_type_choice")
ex_lvl3 = ex_in_cat[ex_in_cat["product_type"] == ex_type_choice].groupby(
    ["product_id", "product_detail"], as_index=False).agg(
    total_sales=("sales", "sum")).sort_values("total_sales", ascending=True)
ex_lvl3["label"] = (ex_lvl3["product_detail"] + " ("
                    + ex_lvl3["product_id"].astype(str) + ")")
fig_l3 = px.bar(ex_lvl3, x="total_sales", y="label", orientation="h",
                color_discrete_sequence=["#D98B39"], text_auto=",.0f",
                labels={"total_sales": "Nilai penjualan", "label": "Produk"})
fig_l3.update_layout(height=max(280, 36 * len(ex_lvl3) + 120), yaxis={
    "categoryorder": "array", "categoryarray": ex_lvl3["label"].tolist()})
st.plotly_chart(fig_l3, width="stretch", key="ex_l3")
st.caption(
    f"Tingkat detail: {ex_cat_choice} > {ex_type_choice}. Seluruh angka "
    "mengikuti filter gerai, bulan, dan kategori di atas."
)

# --- Fitur 6: unduh data hasil filter ---
st.divider()
st.subheader("Unduh data hasil filter")
ex_d1, ex_d2 = st.columns(2)
ex_d1.download_button(
    "Unduh transaksi terfilter (CSV)",
    data=ex_data.to_csv(index=False, date_format="%Y-%m-%d %H:%M:%S"
                        ).encode("utf-8-sig"),
    file_name="coffee_sales_terfilter.csv", mime="text/csv", key="ex_dl_data")
ex_d2.download_button(
    "Unduh ringkasan produk (CSV)",
    data=ex_prod.to_csv(index=False).encode("utf-8-sig"),
    file_name="ringkasan_produk_terfilter.csv", mime="text/csv", key="ex_dl_prod")
st.caption(
    f"Berisi {format_angka(len(ex_data), 0)} baris sesuai filter gerai, bulan, "
    "dan kategori yang sedang aktif."
)