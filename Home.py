import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu
from numerize.numerize import numerize
import time
import plotly.graph_objects as go
import scipy.stats as stats
import io
from pandas import ExcelWriter

st.set_page_config(page_title="Duta Beton Mandiri", page_icon="🚀", layout="wide")

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

    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <h1 style='text-align: center; font-size: 45px;'>
        Production Department
    </h1>
    """, unsafe_allow_html=True)
st.markdown("##")

# Fungsi untuk load dan preprocessing data dengan cache
@st.cache_data
def load_data():
    df = pd.read_csv("Source/datalatihanbuatdashboard.csv")

    # Konversi kolom tanggal
    df["TANGGAL"] = pd.to_datetime(df["TANGGAL"], errors='coerce')

    # Generate kolom year, month, and day
    df["YEARS"] = df["TANGGAL"].dt.year
    df["MONTH"] = df["TANGGAL"].dt.month
    df["DAYS"] = df["TANGGAL"].dt.day

    # Bersihin dan ubah persen jadi float
    df['PERSENTASE REJECT'] = df['PERSENTASE REJECT'].astype(str).str.replace('%', '', regex=False)
    df['PERSENTASE REJECT'] = pd.to_numeric(df['PERSENTASE REJECT'], errors='coerce')

    return df

df = load_data()

# Memastikan kolom TANGGAL jadi datetime
df["TANGGAL"] = pd.to_datetime(df["TANGGAL"], errors='coerce')

# Memastikan kolom YEAR, MONTH, DAYS ada
df["YEARS"] = df["TANGGAL"].dt.year
df["MONTH"] = df["TANGGAL"].dt.month
df["DAYS"] = df["TANGGAL"].dt.day

df['PERSENTASE REJECT'] = df['PERSENTASE REJECT'].astype(str).str.replace('%', '', regex=False)
df['PERSENTASE REJECT'] = pd.to_numeric(df['PERSENTASE REJECT'], errors='coerce')

month_dict = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}

years_list = sorted(df["YEARS"].dropna().astype(int).unique())
months_list = [month_dict[m] for m in sorted(df["MONTH"].dropna().astype(int).unique())]
mesin_list = sorted(df["MESIN"].dropna().unique())
product_list = sorted(df["NAMA_PRODUCT"].dropna().unique())

# Sidebar logo
st.sidebar.image("data/dbm.png", caption="PT Duta Beton Mandiri")

# Date filter section
st.sidebar.markdown("### Filter by Date")

min_date = df["TANGGAL"].min()
max_date = df["TANGGAL"].max()

# Session state untuk reset tombol
if "date_range" not in st.session_state:
    st.session_state.date_range = [min_date, max_date]

# Reset button
if st.sidebar.button("🔄 Reset Date Filter"):
    st.session_state.date_range = [min_date, max_date]

# Date input (pakai session_state)
start_date, end_date = st.sidebar.date_input(
    "Select Date Range",
    value=st.session_state.date_range,
    min_value=min_date,
    max_value=max_date
)

# Simpan ke session_state
st.session_state.date_range = [start_date, end_date]

# Header filter
st.sidebar.header("Please filter")

# Select All Checkbox for Years
select_all_years = st.sidebar.checkbox("Select All Years", value=True)
years = st.sidebar.multiselect("Select Years", options=years_list, default=years_list if select_all_years else [])

# Select All Checkbox for Months
select_all_months = st.sidebar.checkbox("Select All Months", value=True)
month_selection = st.sidebar.multiselect("Select Months", options=months_list, default=months_list if select_all_months else [])
selected_months = [k for k, v in month_dict.items() if v in month_selection]

# Select All Checkbox for Machines
select_all_mesin = st.sidebar.checkbox("Select All Machines", value=True)
mesin = st.sidebar.multiselect("Select Machine", options=mesin_list, default=mesin_list if select_all_mesin else [])

# Select All Checkbox for Products
select_all_product = st.sidebar.checkbox("Select All Products", value=True)
product = st.sidebar.multiselect("Select Product", options=product_list, default=product_list if select_all_product else [])

if not years or not selected_months or not mesin or not product:
    st.warning("🔴🔴🔴FILTERNYA JANGAN DIKOSONGIN BROK🔴🔴🔴")
    st.stop()

# Filter dataframe
df_selection = df[
    (df["YEARS"].isin(years)) &
    (df["MONTH"].isin(selected_months)) &
    (df["MESIN"].isin(mesin)) &
    (df["NAMA_PRODUCT"].isin(product)) &
    (df["TANGGAL"] >= pd.to_datetime(start_date)) &
    (df["TANGGAL"] <= pd.to_datetime(end_date))
]

with st.expander("📁 Export Filtered Data"):
    st.markdown("Please download the filter results in the format you need:")

    # Download as CSV
    st.download_button(
        label="⬇️ Download CSV",
        data=df_selection.to_csv(index=False),
        file_name="filtered_data.csv",
        mime="text/csv",
        key="download_csv"
    )

    # Download as Excel
    output = io.BytesIO()
    with ExcelWriter(output, engine='xlsxwriter') as writer:
        df_selection.to_excel(writer, index=False, sheet_name='FilteredData')
    processed_data = output.getvalue()

    st.download_button(
        label="⬇️ Download Excel",
        data=processed_data,
        file_name='filtered_data.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        key="download_excel"
    )

if df_selection.empty:
    st.warning("No data found for the selected filter combination.")
    st.stop()

# Home Page
def Home():
    with st.expander("Tabular"):
        show_data = st.multiselect('Filter Columns: ', df_selection.columns, default=[])
        if show_data:
            st.dataframe(df_selection[show_data])
        else:
            st.dataframe(df_selection)

# Metric calculations
total_finishgood = float(df_selection["ACTUAL QTY"].sum())
production_mean = float(df_selection["ACTUAL QTY"].mean())
total_reject = float(df_selection["REJECT"].sum())
reject_mean = float(df_selection["REJECT"].mean())
persentase_reject = float(df_selection["PERSENTASE REJECT"].mean())

# Produk dengan 1x produksi terbanyak (bukan total)
max_single_qty_row = df_selection.loc[df_selection["ACTUAL QTY"].idxmax()]
max_single_product = max_single_qty_row["NAMA_PRODUCT"]
max_single_qty = max_single_qty_row["ACTUAL QTY"]

# Produk dengan 1x produksi paling sedikit
min_single_qty_row = df_selection.loc[df_selection["ACTUAL QTY"].idxmin()]
min_single_product = min_single_qty_row["NAMA_PRODUCT"]
min_single_qty = min_single_qty_row["ACTUAL QTY"]

# Produk dengan ACTUAL QTY terbanyak
max_actual_qty_product = df_selection.groupby("NAMA_PRODUCT")["ACTUAL QTY"].sum().idxmax()
max_actual_qty_value = df_selection.groupby("NAMA_PRODUCT")["ACTUAL QTY"].sum().max()

# Produk dengan REJECT terbanyak
max_reject_product = df_selection.groupby("NAMA_PRODUCT")["REJECT"].sum().idxmax()
max_reject_value = df_selection.groupby("NAMA_PRODUCT")["REJECT"].sum().max()

# Produk dengan ACTUAL QTY terendah
min_actual_qty_product = df_selection.groupby("NAMA_PRODUCT")["ACTUAL QTY"].sum().idxmin()
min_actual_qty_value = df_selection.groupby("NAMA_PRODUCT")["ACTUAL QTY"].sum().min()

# Produk dengan REJECT terendah
min_reject_product = df_selection.groupby("NAMA_PRODUCT")["REJECT"].sum().idxmin()
min_reject_value = df_selection.groupby("NAMA_PRODUCT")["REJECT"].sum().min()

# Hitung DPU
total_unit_all = total_finishgood + total_reject
dpu = (total_reject / total_unit_all) * 100 if total_unit_all != 0 else 0

def calculate_dpmo_sigma(defect, total_unit, opp_per_unit):
    dpmo = (defect / (total_unit * opp_per_unit)) * 1_000_000
    sigma = stats.norm.ppf(1 - dpmo / 1_000_000) + 1.5
    return dpmo, sigma

# Hitung DPMO dan Sigma Level
total_unit_all = total_finishgood + total_reject
dpmo, sigma = calculate_dpmo_sigma(defect=total_reject, total_unit=total_unit_all, opp_per_unit=5)

# Penerapan
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total QC Passed", f"{total_finishgood:,.0f}")
col2.metric("Total Reject", f"{total_reject:,.0f}")
col3.metric("Avg QC Passed/Day", f"{production_mean:,.0f}")
col4.metric("Avg Reject/Day", f"{reject_mean:,.0f}")

col5, col6, col7, col8 = st.columns(4)
col5.metric("Avg Total Output/Day", f"{(production_mean + reject_mean):,.0f}")
col6.metric("DPU (%)", f"{dpu:.2f}%")
col7.metric("DPMO", f"{dpmo:,.0f}")
col8.metric("Sigma Level", f"{sigma:.2f}")

st.divider()

col9, col10, col11, col12 = st.columns(4)
with col9:
    st.markdown(f"""
        <div style="background-color:#008fff; padding: 10px; border-radius: 8px; color: white;">
            📌 <b>Products with the Most Production</b>
        </div>
    """, unsafe_allow_html=True)
    st.metric(max_actual_qty_product, f"{max_actual_qty_value:,.0f} Pcs")

with col10:
    st.markdown(f"""
        <div style="background-color:#008fff; padding: 10px; border-radius: 8px; color: white;">
            📌 <b>Products with the Less Production</b>
        </div>
    """, unsafe_allow_html=True)
    st.metric(min_reject_product, f"{min_reject_value:,.0f} Pcs")

with col11:
    st.markdown(f"""
        <div style="background-color:#008fff; padding: 10px; border-radius: 8px; color: white;">
            📌 <b>Products with the Most Reject</b>
        </div>
    """, unsafe_allow_html=True)
    st.metric(max_reject_product, f"{max_reject_value:,.0f} Pcs")

with col12:
    st.markdown(f"""
        <div style="background-color:#008fff; padding: 10px; border-radius: 8px; color: white;">
            📌 <b>Products with the Less Reject</b>
        </div>
    """, unsafe_allow_html=True)
    st.metric(min_reject_product, f"{min_reject_value:,.0f} Pcs")

st.divider()

col13, col14 = st.columns(2, gap='large')
with col13:
    st.markdown("""
        <div style="background-color:#198754; padding: 10px 16px; border-radius: 10px; color: white; font-weight: bold;">
            ⬆ Highest Single-Day Output
        </div>
    """, unsafe_allow_html=True)
    st.metric(label=f"{max_single_product}", value=f"{max_single_qty:,.0f} Pcs")

with col14:
    st.markdown("""
        <div style="background-color:#dc3545; padding: 10px 16px; border-radius: 10px; color: white; font-weight: bold;">
            ⬇ Lowest Single-Day Output
        </div>
    """, unsafe_allow_html=True)
    st.metric(label=f"{min_single_product}", value=f"{min_single_qty:,.0f} Pcs")

st.markdown("""---""")

# Graphs
def graphs():
    # Menghitung jumlah total dan kontribusi persen per produk
    distribusi_produk = df_selection.groupby("NAMA_PRODUCT")[["ACTUAL QTY"]].sum()
    distribusi_produk["PERCENT"] = distribusi_produk["ACTUAL QTY"] / distribusi_produk["ACTUAL QTY"].sum()

    # Memisahkan data yang >= 1% dan < 1%
    hasil_utama = distribusi_produk[distribusi_produk["PERCENT"] >= 0.01]
    hasil_lainnya = distribusi_produk[distribusi_produk["PERCENT"] < 0.01]

    # Menggabungkan yang < 1% menjadi satu kategori "Lainnya"
    if not hasil_lainnya.empty:
        total_lainnya = hasil_lainnya["ACTUAL QTY"].sum()
        hasil_utama.loc["Lainnya"] = [total_lainnya, total_lainnya / distribusi_produk["ACTUAL QTY"].sum()]

    # Sort by ACTUAL_QTY
    hasil_utama = hasil_utama.sort_values(by="ACTUAL QTY", ascending=False)

    # Membuat pie chart
    fig_produksi = px.pie(
        hasil_utama,
        values="ACTUAL QTY",
        names=hasil_utama.index,
        title="<b> Production Distribution per Product </b>",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig_produksi.update_layout(template="plotly_white")

    # Group dan sort data dari terbesar ke terkecil untuk Pareto
    reject_mesin = df_selection.groupby("MESIN")[["REJECT"]].sum().sort_values(by="REJECT", ascending=False)

    # Menghitung cumulative percentage
    reject_mesin["CUMSUM"] = reject_mesin["REJECT"].cumsum()
    reject_mesin["CUMPCT"] = 100 * reject_mesin["CUMSUM"] / reject_mesin["REJECT"].sum()

    # Pareto Chart berdasarkan Nomer Mesin
    fig_paretomachine = go.Figure()

    # Bar chart
    fig_paretomachine.add_trace(
        go.Bar(
            x=reject_mesin.index,
            y=reject_mesin["REJECT"],
            name="Reject Qty",
            marker=dict(color="#0083b8"),
            yaxis="y1"
        )
    )

    # Line chart cumulative %
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

    # Pareto Chart berdasarkan Nama Product
    reject_produk = df_selection.groupby("NAMA_PRODUCT")[["REJECT"]].sum().sort_values(by="REJECT", ascending=False)
    reject_produk["CUMSUM"] = reject_produk["REJECT"].cumsum()
    reject_produk["CUMPCT"] = 100 * reject_produk["CUMSUM"] / reject_produk["REJECT"].sum()

    fig_paretoproduct = go.Figure()

    # Bar chart
    fig_paretoproduct.add_trace(
         go.Bar(
            x=reject_produk.index,
            y=reject_produk["REJECT"],
             name="Reject Qty",
            marker=dict(color="#d62728"),
             yaxis="y1"
        )
    )

    # Line chart cumulative % produk
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

    # Layout
    fig_paretoproduct.update_layout(
        title="<b>Pareto Chart: Reject per Product</b>",
        yaxis=dict(
            title="Number of Reject",
            showgrid=False
        ),
        yaxis2=dict(
            title="Cumulative %",
            overlaying="y",
            side="right",
            showgrid=False,
            range=[0, 110]
        ),
        xaxis=dict(title="Product Name"),
        legend=dict(x=0.7, y=1.1),
        template="plotly_white",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    
    # Layout
    fig_paretomachine.update_layout(
        title="<b>Pareto Chart: Reject per Machine</b>",
        yaxis=dict(
            title="Number of Reject",
            showgrid=False
        ),
        yaxis2=dict(
            title="Cumulative %",
            overlaying="y",
            side="right",
            showgrid=False,
            range=[0, 110]
        ),
        xaxis=dict(title="Machine"),
        legend=dict(x=0.7, y=1.1),
        template="plotly_white",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    # Line chart for REJECT growth by date
    reject_trend = df_selection.groupby("TANGGAL")["REJECT"].sum().reset_index()
    fig_reject_trend = px.line(
        reject_trend,
        x="TANGGAL",
        y="REJECT",
        title="<b>Trend of Reject per Month</b>",
        markers=True,
        color_discrete_sequence=["#ff0000"]
    )
    fig_reject_trend.update_layout(
        xaxis_title="Date",
        yaxis_title="Number of Reject",
        plot_bgcolor="rgba(0,0,0,0)",
        template="plotly_white"
    )

    # Bar chart ACTUAL_QTY per NAMA_PRODUCT
    fig_bar_produk = px.bar(
        df_selection.groupby("NAMA_PRODUCT")["ACTUAL QTY"].sum().sort_values(ascending=True),
        x="ACTUAL QTY",
        y=df_selection.groupby("NAMA_PRODUCT")["ACTUAL QTY"].sum().sort_values(ascending=True).index,
        orientation="h",
        title="<b>Production Amount per Product</b>",
        color_discrete_sequence=["#00cc96"],
        template="plotly_white"
    )

    fig_bar_produk.update_layout(
        xaxis_title="Number of Production",
        yaxis_title="Product Name",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    # Menampilkan pareto dan pie chart di baris pertama
    col_left, col_right = st.columns(2)
    col_left.plotly_chart(fig_paretomachine, use_container_width=True)
    col_right.plotly_chart(fig_produksi, use_container_width=True)

    st.plotly_chart(fig_paretoproduct, use_container_width=True)

    st.plotly_chart(fig_bar_produk, use_container_width=True)

    st.plotly_chart(fig_reject_trend, use_container_width=True)

# Progress bar
def Progressbar():
    st.markdown("""<style> .stProgress > div > div > div > div { background-image: linear-gradient(to right, #99ff99 , #ffff00); } </style>""", unsafe_allow_html=True)

    target = df_selection["WO QTY"].sum()
    current = df_selection["ACTUAL QTY"].sum()
    percent = round((current / target * 100)) if target else 0
    
    mybar = st.progress(percent)

    if percent >= 100:
        st.subheader("🎉 Target Done!")
    else:
        st.write(f"You have {percent}% of {int(target):,} Pcs")

# Sidebar navigation
def fix_sidebar_style():
    st.markdown("""
        <style>
        /* Melebarkan sidebar agar teks tidak turun */
        section[data-testid="stSidebar"] {
            width: 300px !important;
        }

        /* Melebarkan menu title agar teks tidak turun */
        .css-1wvake5 > div {
            white-space: nowrap;
        }
        </style>
    """, unsafe_allow_html=True)

def DailyReport():
    st.subheader("📅 Daily Report")
    daily_data = df_selection.groupby("TANGGAL")[["ACTUAL QTY", "REJECT"]].sum().reset_index()
    daily_data["REJECT %"] = daily_data["REJECT"] / (daily_data["ACTUAL QTY"] + daily_data["REJECT"]) * 100

    st.dataframe(daily_data)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.line(
            daily_data,
            x="TANGGAL",
            y=["ACTUAL QTY", "REJECT"],
            title="Daily Production vs Reject",
            markers=True,
            color_discrete_sequence=["#00cc96", "#ff4d4d"]
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig_reject = px.bar(
            daily_data,
            x="TANGGAL",
            y="REJECT %",
            title="Daily Reject Percentage",
            color="REJECT %",
            color_continuous_scale="reds"
        )
        st.plotly_chart(fig_reject, use_container_width=True)

def MonthlyReport():
    st.subheader("📊 Monthly Report")
    monthly_data = df_selection.groupby(["YEARS", "MONTH"])[["ACTUAL QTY", "REJECT"]].sum().reset_index()
    monthly_data["REJECT %"] = monthly_data["REJECT"] / (monthly_data["ACTUAL QTY"] + monthly_data["REJECT"]) * 100
    monthly_data["MONTH_NAME"] = monthly_data["MONTH"].map(month_dict)

    st.dataframe(monthly_data)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            monthly_data,
            x="MONTH_NAME",
            y=["ACTUAL QTY", "REJECT"],
            barmode="group",
            title="Monthly Production vs Reject",
            color_discrete_sequence=["#00cc96", "#ff4d4d"]
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig_reject_pct = px.line(
            monthly_data,
            x="MONTH_NAME",
            y="REJECT %",
            markers=True,
            title="Monthly Reject Percentage",
            color_discrete_sequence=["#ffa500"]
        )
        st.plotly_chart(fig_reject_pct, use_container_width=True)

    # Pie chart untuk total reject kontribusi per bulan
    fig_pie = px.pie(
        monthly_data,
        names="MONTH_NAME",
        values="REJECT",
        title="Reject Contribution by Month",
        color_discrete_sequence=px.colors.sequential.Reds
    )
    st.plotly_chart(fig_pie, use_container_width=True)

def sideBar():
    fix_sidebar_style()
    with st.sidebar:
        selected = option_menu(
            menu_title="Main Menu",
            options=['Home', 'Progress', 'Daily Report', 'Monthly Report'],
            icons=['house', 'eye'],
            menu_icon="cast",
            default_index=0
        )
    st.subheader(f"Page: {selected}")
    if selected == "Home":
        Home()
        graphs()
    elif selected == "Progress":
        Progressbar()
    elif selected == "Daily Report":
        DailyReport()
    elif selected == "Monthly Report":
        MonthlyReport()

sideBar()

# Hide default Streamlit branding
hide_st_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)
