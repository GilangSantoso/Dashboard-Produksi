import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu
from numerize.numerize import numerize
import plotly.graph_objects as go
from scipy import stats
import io
import openpyxl

# Konfigurasi halaman
st.set_page_config(page_title="Duta Beton Mandiri", page_icon="🚀", layout="wide")

# CSS Styling
st.markdown("""
    <style>
    /* Kartu untuk metrik */
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }

    /* Header teks */
    h1 {
        font-size: 40px !important;
        color: #333333;
    }

    /* Untuk table */
    .dataframe tbody tr th {
        background-color: #f9f9f9;
    }

    /* Warna dasar halaman */
    .main > div {
        background-color: #f8f9fa;
    }

    /* Gaya tombol */
    .stButton>button {
        background-color: #0d6efd;
        color: white;
        border-radius: 10px;
        padding: 0.5em 1em;
    }

    .stButton>button:hover {
        background-color: #0b5ed7;
    }

    /* Custom Info Box */
    .custom-info-green {
        background-color: #198754;
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 10px;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }

    .custom-info-red {
        background-color: #dc3545;
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 10px;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        width: 300px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <h1 style='text-align: center; font-size: 45px;'>
        Production Department
    </h1>
    """, unsafe_allow_html=True)
st.markdown("##")

# Fungsi untuk load dan preprocessing data
@st.cache_data
def load_data(file_path, sheet_name="Sheet1"):
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        df["TANGGAL"] = pd.to_datetime(df["TANGGAL"], errors='coerce')
        df["YEARS"] = df["TANGGAL"].dt.year
        df["MONTH"] = df["TANGGAL"].dt.month
        df["DAYS"] = df["TANGGAL"].dt.day
        return df
    except FileNotFoundError:
        st.error(f"File {file_path} tidak ditemukan. Pastikan file ada di direktori yang benar.")
        st.stop()
    except Exception as e:
        st.error(f"Terjadi kesalahan saat membaca file: {e}")
        st.stop()

# Load data untuk kedua halaman
df_production = load_data("Source/Production.xlsx")
df_used = load_data("Source/Used.xlsx")

# Dictionary bulan
month_dict = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}

# Fungsi untuk membuat opsi filter
def get_filter_options(df):
    years_list = sorted(df["YEARS"].dropna().astype(int).unique())
    months_list = [month_dict[m] for m in sorted(df["MONTH"].dropna().astype(int).unique())]
    mesin_list = sorted(df["MESIN"].dropna().unique())
    product_list = sorted(df["NAMA_PRODUCT"].dropna().unique())
    return years_list, months_list, mesin_list, product_list

# Fungsi untuk menampilkan filter sidebar
def display_filters(df, page_name):
    st.sidebar.markdown(f"### {page_name} Filters")
    
    min_date = df["TANGGAL"].min()
    max_date = df["TANGGAL"].max()
    
    if f"{page_name}_date_range" not in st.session_state:
        st.session_state[f"{page_name}_date_range"] = [min_date, max_date]
    
    if st.sidebar.button(f"🔄 Reset {page_name} Date Filter"):
        st.session_state[f"{page_name}_date_range"] = [min_date, max_date]
    
    start_date, end_date = st.sidebar.date_input(
        f"Select {page_name} Date Range",
        value=st.session_state[f"{page_name}_date_range"],
        min_value=min_date,
        max_value=max_date
    )
    st.session_state[f"{page_name}_date_range"] = [start_date, end_date]
    
    st.sidebar.header(f"{page_name} Filter Options")
    
    years_list, months_list, mesin_list, product_list = get_filter_options(df)
    
    select_all_years = st.sidebar.checkbox(f"Select All {page_name} Years", value=True, key=f"{page_name}_years")
    years = st.sidebar.multiselect(f"Select {page_name} Years", options=years_list, default=years_list if select_all_years else [], key=f"{page_name}_years_select")
    
    select_all_months = st.sidebar.checkbox(f"Select All {page_name} Months", value=True, key=f"{page_name}_months")
    month_selection = st.sidebar.multiselect(f"Select {page_name} Months", options=months_list, default=months_list if select_all_months else [], key=f"{page_name}_months_select")
    months = [k for k, v in month_dict.items() if v in month_selection]
    
    select_all_mesin = st.sidebar.checkbox(f"Select All {page_name} Machines", value=True, key=f"{page_name}_mesin")
    mesin = st.sidebar.multiselect(f"Select {page_name} Machine", options=mesin_list, default=mesin_list if select_all_mesin else [], key=f"{page_name}_mesin_select")
    
    select_all_product = st.sidebar.checkbox(f"Select All {page_name} Products", value=True, key=f"{page_name}_product")
    product = st.sidebar.multiselect(f"Select {page_name} Product", options=product_list, default=product_list if select_all_product else [], key=f"{page_name}_product_select")
    
    return years, months, mesin, product, start_date, end_date

# Fungsi untuk filter DataFrame
def filter_dataframe(df, years, months, mesin, product, start_date, end_date):
    return df[
        (df["YEARS"].isin(years)) &
        (df["MONTH"].isin(months)) &
        (df["MESIN"].isin(mesin)) &
        (df["NAMA_PRODUCT"].isin(product)) &
        (df["TANGGAL"] >= pd.to_datetime(start_date)) &
        (df["TANGGAL"] <= pd.to_datetime(end_date))
    ]

# Fungsi untuk ekspor data
def export_data(df, page_name):
    with st.expander(f"📁 Export {page_name} Filtered Data"):
        st.markdown(f"Download hasil filter {page_name} dalam format yang Anda inginkan:")
        
        st.download_button(
            label="⬇️ Download CSV",
            data=df.to_csv(index=False),
            file_name=f"{page_name.lower()}_filtered_data.csv",
            mime="text/csv",
            key=f"download_csv_{page_name}"
        )
        
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        st.download_button(
            label="⬇️ Download Excel",
            data=buffer,
            file_name=f"{page_name.lower()}_filtered_data.xlsx",
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            key=f"download_excel_{page_name}"
        )

# Fungsi untuk progress bar (khusus Production)
def progress_bar(df, page_name):
    st.markdown("""<style> .stProgress > div > div > div > div { background-image: linear-gradient(to right, #99ff99 , #ffff00); } </style>""", unsafe_allow_html=True)
    target = df["TARGET_QTY"].sum() if "TARGET_QTY" in df.columns else 0
    current = df["ACTUAL_QTY"].sum()
    percent = round((current / target * 100)) if target else 0
    mybar = st.progress(percent)
    if percent >= 100:
        st.subheader(f"🎉 {page_name} Target Done!")
    else:
        st.write(f"{page_name} Progress: {percent}% of {int(target):,} Pcs")

# Fungsi untuk perhitungan metrik (khusus Production)
def calculate_metrics(df):
    total_finishgood = float(df["ACTUAL_QTY"].sum())
    production_mean = float(df["ACTUAL_QTY"].mean())
    total_reject = float(df["REJECT"].sum()) if "REJECT" in df.columns else 0
    reject_mean = float(df["REJECT"].mean()) if "REJECT" in df.columns else 0

    max_single_qty_row = df.loc[df["ACTUAL_QTY"].idxmax()]
    max_single_product = max_single_qty_row["NAMA_PRODUCT"]
    max_single_qty = max_single_qty_row["ACTUAL_QTY"]

    min_single_qty_row = df.loc[df["ACTUAL_QTY"].idxmin()]
    min_single_product = min_single_qty_row["NAMA_PRODUCT"]
    min_single_qty = min_single_qty_row["ACTUAL_QTY"]

    grouped_product = df.groupby("NAMA_PRODUCT")[["ACTUAL_QTY", "REJECT"]].sum() if "REJECT" in df.columns else df.groupby("NAMA_PRODUCT")[["ACTUAL_QTY"]].sum()
    max_actual_qty_product = grouped_product["ACTUAL_QTY"].idxmax()
    max_actual_qty_value = grouped_product["ACTUAL_QTY"].max()
    min_actual_qty_product = grouped_product["ACTUAL_QTY"].idxmin()
    min_actual_qty_value = grouped_product["ACTUAL_QTY"].min()

    if "REJECT" in df.columns:
        max_reject_product = grouped_product["REJECT"].idxmax()
        max_reject_value = grouped_product["REJECT"].max()
        min_reject_product = grouped_product["REJECT"].idxmin()
        min_reject_value = grouped_product["REJECT"].min()
    else:
        max_reject_product = min_reject_product = "N/A"
        max_reject_value = min_reject_value = 0

    total_unit_all = total_finishgood + total_reject
    dpu = (total_reject / total_unit_all) * 100 if total_unit_all != 0 and "REJECT" in df.columns else 0

    def calculate_dpmo_sigma(defect, total_unit, opp_per_unit):
        dpmo = (defect / (total_unit * opp_per_unit)) * 1_000_000 if total_unit * opp_per_unit != 0 else 0
        sigma = stats.norm.ppf(1 - dpmo / 1_000_000) + 1.5 if dpmo < 1_000_000 else 0
        return dpmo, sigma

    dpmo, sigma = calculate_dpmo_sigma(defect=total_reject, total_unit=total_unit_all, opp_per_unit=5) if "REJECT" in df.columns else (0, 0)

    return {
        "total_finishgood": total_finishgood,
        "production_mean": production_mean,
        "total_reject": total_reject,
        "reject_mean": reject_mean,
        "max_single_product": max_single_product,
        "max_single_qty": max_single_qty,
        "min_single_product": min_single_product,
        "min_single_qty": min_single_qty,
        "max_actual_qty_product": max_actual_qty_product,
        "max_actual_qty_value": max_actual_qty_value,
        "min_actual_qty_product": min_actual_qty_product,
        "min_actual_qty_value": min_actual_qty_value,
        "max_reject_product": max_reject_product,
        "max_reject_value": max_reject_value,
        "min_reject_product": min_reject_product,
        "min_reject_value": min_reject_value,
        "dpu": dpu,
        "dpmo": dpmo,
        "sigma": sigma
    }

# Fungsi untuk menampilkan metrik (khusus Production)
def display_metrics(metrics, page_name):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(f"{page_name} Total QC Passed", f"{metrics['total_finishgood']:,.0f}")
    col2.metric(f"{page_name} Total Reject", f"{metrics['total_reject']:,.0f}")
    col3.metric(f"{page_name} Avg QC Passed/Day", f"{metrics['production_mean']:,.0f}")
    col4.metric(f"{page_name} Avg Reject/Day", f"{metrics['reject_mean']:,.0f}")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric(f"{page_name} Avg Total Output/Day", f"{(metrics['production_mean'] + metrics['reject_mean']):,.0f}")
    col6.metric(f"{page_name} DPU (%)", f"{metrics['dpu']:.2f}%")
    col7.metric(f"{page_name} DPMO", f"{metrics['dpmo']:,.0f}")
    col8.metric(f"{page_name} Sigma Level", f"{metrics['sigma']:.2f}")

    st.divider()

    col9, col10, col11, col12 = st.columns(4)
    with col9:
        st.markdown(f"""
            <div style="background-color:#008fff; padding: 10px; border-radius: 8px; color: white;">
                📌 <b>{page_name} Products with the Most Production</b>
            </div>
        """, unsafe_allow_html=True)
        st.metric(metrics['max_actual_qty_product'], f"{metrics['max_actual_qty_value']:,.0f} Pcs")

    with col10:
        st.markdown(f"""
            <div style="background-color:#008fff; padding: 10px; border-radius: 8px; color: white;">
                📌 <b>{page_name} Products with the Less Production</b>
            </div>
        """, unsafe_allow_html=True)
        st.metric(metrics['min_actual_qty_product'], f"{metrics['min_actual_qty_value']:,.0f} Pcs")

    with col11:
        st.markdown(f"""
            <div style="background-color:#008fff; padding: 10px; border-radius: 8px; color: white;">
                📌 <b>{page_name} Products with the Most Reject</b>
            </div>
        """, unsafe_allow_html=True)
        st.metric(metrics['max_reject_product'], f"{metrics['max_reject_value']:,.0f} Pcs")

    with col12:
        st.markdown(f"""
            <div style="background-color:#008fff; padding: 10px; border-radius: 8px; color: white;">
                📌 <b>{page_name} Products with the Less Reject</b>
            </div>
        """, unsafe_allow_html=True)
        st.metric(metrics['min_reject_product'], f"{metrics['min_reject_value']:,.0f} Pcs")

    st.divider()

    col13, col14 = st.columns(2, gap='large')
    with col13:
        st.markdown(f"""
            <div style="background-color:#198754; padding: 10px 16px; border-radius: 10px; color: white; font-weight: bold;">
                ⬆ {page_name} Highest Single-Day Output
            </div>
        """, unsafe_allow_html=True)
        st.metric(label=f"{metrics['max_single_product']}", value=f"{metrics['max_single_qty']:,.0f} Pcs")

    with col14:
        st.markdown(f"""
            <div style="background-color:#dc3545; padding: 10px 16px; border-radius: 10px; color: white; font-weight: bold;">
                ⬇ {page_name} Lowest Single-Day Output
            </div>
        """, unsafe_allow_html=True)
        st.metric(label=f"{metrics['min_single_product']}", value=f"{metrics['min_single_qty']:,.0f} Pcs")  # Perbaikan: Ganti max_single_qty ke min_single_qty

    st.markdown("""---""")

# Fungsi untuk visualisasi (khusus Production)
def display_graphs(df, page_name):
    distribusi_produk = df.groupby("NAMA_PRODUCT")[["ACTUAL_QTY"]].sum()
    distribusi_produk["PERCENT"] = distribusi_produk["ACTUAL_QTY"] / distribusi_produk["ACTUAL_QTY"].sum()

    hasil_utama = distribusi_produk[distribusi_produk["PERCENT"] >= 0.01]
    hasil_lainnya = distribusi_produk[distribusi_produk["PERCENT"] < 0.01]

    if not hasil_lainnya.empty:
        total_lainnya = hasil_lainnya["ACTUAL_QTY"].sum()
        hasil_utama.loc["Lainnya"] = [total_lainnya, total_lainnya / distribusi_produk["ACTUAL_QTY"].sum()]

    hasil_utama = hasil_utama.sort_values(by="ACTUAL_QTY", ascending=False)

    fig_produksi = px.pie(
        hasil_utama,
        values="ACTUAL_QTY",
        names=hasil_utama.index,
        title=f"<b>{page_name} Production Distribution per Product</b>",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_produksi.update_layout(template="plotly_white")

    if "REJECT" in df.columns:
        reject_mesin = df.groupby("MESIN")[["REJECT"]].sum().sort_values(by="REJECT", ascending=False)
        reject_mesin["CUMSUM"] = reject_mesin["REJECT"].cumsum()
        reject_mesin["CUMPCT"] = 100 * reject_mesin["CUMSUM"] / reject_mesin["REJECT"].sum()

        fig_paretomachine = go.Figure()

        fig_paretomachine.add_trace(
            go.Bar(
                x=reject_mesin.index,
                y=reject_mesin["REJECT"],
                name="Reject Qty",
                marker=dict(color="#0083b8"),
                yaxis="y1"
            )
        )
        fig_paretomachine.add_trace(
            go.Scatter(
                x=reject_mesin.index,
                y=reject_mesin["CUMPCT"],
                name="Cumulative %",
                yaxis="y2",
                marker=dict(color="orange"),
                mode="lines+markers"
            )
        )
        fig_paretomachine.update_layout(
            title=f"<b>{page_name} Pareto Chart: Reject per Machine</b>",
            yaxis=dict(title="Number of Reject", showgrid=False),
            yaxis2=dict(title="Cumulative %", overlaying="y", side="right", showgrid=False, range=[0, 110]),
            xaxis=dict(title="Machine"),
            legend=dict(x=0.7, y=1.1),
            template="plotly_white",
            plot_bgcolor="rgba(0,0,0,0)"
        )

        reject_produk = df.groupby("NAMA_PRODUCT")[["REJECT"]].sum().sort_values(by="REJECT", ascending=False)
        reject_produk["CUMSUM"] = reject_produk["REJECT"].cumsum()
        reject_produk["CUMPCT"] = 100 * reject_produk["CUMSUM"] / reject_produk["REJECT"].sum()

        fig_paretoproduct = go.Figure()
        fig_paretoproduct.add_trace(
            go.Bar(
                x=reject_produk.index,
                y=reject_produk["REJECT"],
                name="Reject Qty",
                marker=dict(color="#d62728"),
                yaxis="y1"
            )
        )
        fig_paretoproduct.add_trace(
            go.Scatter(
                x=reject_produk.index,
                y=reject_produk["CUMPCT"],
                name="Cumulative %",
                yaxis="y2",
                marker=dict(color="orange"),
                mode="lines+markers"
            )
        )
        fig_paretoproduct.update_layout(
            title=f"<b>{page_name} Pareto Chart: Reject per Product</b>",
            yaxis=dict(title="Number of Reject", showgrid=False),
            yaxis2=dict(title="Cumulative %", overlaying="y", side="right", showgrid=False, range=[0, 110]),
            xaxis=dict(title="Product Name"),
            legend=dict(x=0.7, y=1.1),
            template="plotly_white",
            plot_bgcolor="rgba(0,0,0,0)"
        )

        reject_trend = df.groupby("TANGGAL")["REJECT"].sum().reset_index()
        fig_reject_trend = px.line(
            reject_trend,
            x="TANGGAL",
            y="REJECT",
            title=f"<b>{page_name} Trend of Reject per Month</b>",
            markers=True,
            color_discrete_sequence=["#ff0000"]
        )
        fig_reject_trend.update_layout(
            xaxis_title="Date",
            yaxis_title="Number of Reject",
            plot_bgcolor="rgba(0,0,0,0)",
            template="plotly_white"
        )

    fig_bar_produk = px.bar(
        df.groupby("NAMA_PRODUCT")["ACTUAL_QTY"].sum().sort_values(ascending=True),
        x="ACTUAL_QTY",
        y=df.groupby("NAMA_PRODUCT")["ACTUAL_QTY"].sum().sort_values(ascending=True).index,
        orientation="h",
        title=f"<b>{page_name} Production Amount per Product</b>",
        color_discrete_sequence=["#00cc96"],
        template="plotly_white"
    )
    fig_bar_produk.update_layout(
        xaxis_title="Number of Production",
        yaxis_title="Product Name",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    col_left, col_right = st.columns(2)
    if "REJECT" in df.columns:
        col_left.plotly_chart(fig_paretomachine, use_container_width=True)
    col_right.plotly_chart(fig_produksi, use_container_width=True)
    if "REJECT" in df.columns:
        st.plotly_chart(fig_paretoproduct, use_container_width=True)
        st.plotly_chart(fig_reject_trend, use_container_width=True)
    st.plotly_chart(fig_bar_produk, use_container_width=True)

def calculate_metrics_used(df):
    # Daftar material yang ingin ditampilkan
    target_materials = ["ABU BATU", "STL 5/10", "PASIR LUMAJANG",
                        "SIRTU AYAK", "SEMEN", "CARBON BLACK",
                        "CARBON RED", "PIGMENT BLACK 777 HEINRICH JERMAN",
                        "PIGMENT RED 130 HEINRICH JERMAN", "CARBON TP 130 RED",
                        "PIGMENT BLACK 330 HEINRICH JERMAN", "PIGMENT TP 130 RED"]

    # Filter hanya baris dengan material tersebut (tanpa terpengaruh kapitalisasi)
    df = df[df["NAMA_MATERIAL"].str.upper().isin([m.upper() for m in target_materials])]

    grouped = df.groupby("NAMA_MATERIAL")["JUMLAH"].agg(["sum", "mean", "max", "min"]).reset_index()

    metrics = []

    for _, row in grouped.iterrows():
        metrics.append({
            "product": row["NAMA_MATERIAL"],
            "total": row["sum"],
            "mean": row["mean"],
            "max": row["max"],
            "min": row["min"]
        })

    return metrics


def display_metrics_used(metrics):
    st.subheader("Used Materials Metrics")

    for m in metrics:
        st.markdown(f"""
            <div style="background-color:#000000; padding: 20px; border-radius: 10px; margin-bottom: 10px;">
                <b>🔹 {m['product']}</b>
            </div>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("""
                <div style="background-color:#0d6efd; padding: 6px 12px; border-radius: 8px; color: white; font-weight: bold;">
                    Total Digunakan
                </div>
            """, unsafe_allow_html=True)
            st.metric(label="", value=f"{m['total']:,.2f} Kg")

        with col2:
            st.markdown("""
                <div style="background-color:#dba43d; padding: 6px 12px; border-radius: 8px; color: white; font-weight: bold;">
                    Rata-rata
                </div>
            """, unsafe_allow_html=True)
            st.metric(label="", value=f"{m['mean']:,.2f} Kg")

        with col3:
            st.markdown("""
                <div style="background-color:#dc3545; padding: 6px 12px; border-radius: 8px; color: white; font-weight: bold;">
                    Maksimum
                </div>
            """, unsafe_allow_html=True)
            st.metric(label="", value=f"{m['max']:,.2f} Kg")

        with col4:
            st.markdown("""
                <div style="background-color:#198754; padding: 6px 12px; border-radius: 8px; color: white; font-weight: bold;">
                    Minimum
                </div>
            """, unsafe_allow_html=True)
            st.metric(label="", value=f"{m['min']:,.2f} Kg")

        st.divider()

# Fungsi untuk halaman Production
def production_page():
    years, months, mesin, product, start_date, end_date = display_filters(df_production, "Production")
    
    if not years or not months or not mesin or not product:
        st.warning("Mohon lengkapi semua filter Production sebelum melanjutkan.")
        st.stop()
    
    df_production_selection = filter_dataframe(df_production, years, months, mesin, product, start_date, end_date)
    
    if df_production_selection.empty:
        st.warning("Tidak ada data Production yang sesuai dengan kombinasi filter yang dipilih. Silakan sesuaikan filter.")
        st.stop()
    
    with st.expander("Production Tabular"):
        show_data = st.multiselect('Filter Production Columns: ', df_production_selection.columns, default=[], key="production_columns")
        st.dataframe(df_production_selection[show_data] if show_data else df_production_selection)
    
    export_data(df_production_selection, "Production")
    progress_bar(df_production_selection, "Production")
    metrics = calculate_metrics(df_production_selection)
    display_metrics(metrics, "Production")
    display_graphs(df_production_selection, "Production")

#Fungsi untuk halaman Used
def used_page():
    years, months, mesin, product, start_date, end_date = display_filters(df_used, "Used")
    
    if not years or not months or not mesin or not product:
        st.warning("Mohon lengkapi semua filter Used sebelum melanjutkan.")
        st.stop()
    
    df_used_selection = filter_dataframe(df_used, years, months, mesin, product, start_date, end_date)
    
    if df_used_selection.empty:
        st.warning("Tidak ada data Used yang sesuai dengan kombinasi filter yang dipilih. Silakan sesuaikan filter.")
        st.stop()

    with st.expander("Used Tabular"):
        show_data = st.multiselect('Filter Used Columns: ', df_used_selection.columns, default=[], key="used_columns")
        st.dataframe(df_used_selection[show_data] if show_data else df_used_selection)
    
    export_data(df_used_selection, "Used")
    metrics = calculate_metrics_used(df_used_selection)
    display_metrics_used(metrics)


# Sidebar navigation
with st.sidebar:
    st.image("data/dbm.png", caption="PT Duta Beton Mandiri")
    selected = option_menu(
        menu_title="Main Menu",
        options=['Production', 'Used'],
        icons=['file-text', 'archive'],
        menu_icon="cast",
        default_index=0
    )

st.subheader(f"Page: {selected}")
if selected == "Production":
    production_page()
elif selected == "Used":
    used_page()

# Hide Streamlit branding
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

