import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import os

sns.set(style='dark')

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="E-Commerce Dashboard",
    layout="wide"
)

# =========================
# HELPER FUNCTIONS
# =========================

def load_data():
    # Mengambil direktori tempat file dashboard.py ini berada
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Menggabungkan direktori tersebut dengan nama file CSV
    file_path = os.path.join(current_dir, "main_data.csv")
    
    # Membaca CSV dari file_path yang sudah dinamis
    df = pd.read_csv(file_path)
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    df['month'] = df['order_purchase_timestamp'].dt.to_period('M')
    return df


def filter_data(df, start_date, end_date, status):
    df = df[
        (df["order_purchase_timestamp"].dt.date >= start_date) &
        (df["order_purchase_timestamp"].dt.date <= end_date)
    ]
    
    if status:
        df = df[df['order_status'].isin(status)]
    
    return df


def create_monthly_sales_df(df):
    monthly = df.groupby('month').agg({
        'total_price': 'sum',
        'order_id': 'nunique'
    }).rename(columns={'order_id': 'total_orders'})

    if not monthly.empty:
        monthly = monthly.sort_index()
        monthly['revenue_growth'] = monthly['total_price'].pct_change() * 100
        monthly.index = monthly.index.astype(str)

    return monthly


def create_rating_status_df(df):
    return df.groupby(['order_status', 'review_score']).size().reset_index(name='count')


def calculate_kpi(df):
    total_revenue = df['total_price'].sum()
    total_orders = df['order_id'].nunique()
    avg_rating = df['review_score'].mean()
    return total_revenue, total_orders, avg_rating


def create_insight(monthly_df):
    if monthly_df.empty:
        return None

    best_month = monthly_df['total_price'].idxmax()
    worst_month = monthly_df['total_price'].idxmin()
    last_growth = monthly_df['revenue_growth'].iloc[-1]

    return best_month, worst_month, last_growth


# =========================
# LOAD DATA
# =========================
@st.cache_data
def get_data():
    return load_data()

all_df = get_data()

# =========================
# SIDEBAR
# =========================
min_date = all_df["order_purchase_timestamp"].min().date()
max_date = all_df["order_purchase_timestamp"].max().date()

with st.sidebar:
    st.image("../logo.png")
    st.header("Filter Data")

    start_date, end_date = st.date_input(
        "Rentang Waktu",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    status_list = all_df['order_status'].dropna().unique()
    selected_status = st.multiselect(
        "Status Order",
        options=status_list,
        default=status_list
    )

# =========================
# FILTER DATA
# =========================
main_df = filter_data(all_df, start_date, end_date, selected_status)

monthly_sales_df = create_monthly_sales_df(main_df)
rating_status_df = create_rating_status_df(main_df)

# =========================
# HEADER
# =========================
st.title(":bar_chart: E-Commerce Performance Dashboard")
st.markdown("Analisis penjualan dan performa transaksi")
st.markdown("---")

# =========================
# KPI
# =========================
total_revenue, total_orders, avg_rating = calculate_kpi(main_df)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(":moneybag: Total Revenue", f"{total_revenue:,.0f}")

with col2:
    st.metric(":package: Total Orders", f"{total_orders:,}")

with col3:
    st.metric(":star: Avg Rating", f"{avg_rating:.2f}")

st.markdown("---")

# =========================
# CHART 1 (TREND)
# =========================
st.subheader(":chart_with_upwards_trend: Tren Penjualan & Order")

if monthly_sales_df.empty:
    st.warning("Tidak ada data pada rentang ini")
    st.stop()

fig1, ax1 = plt.subplots(figsize=(10, 5))

# --- Konfigurasi Sumbu Y Kiri (Revenue) ---
color1 = 'tab:blue'
ax1.plot(monthly_sales_df.index, monthly_sales_df['total_price'], marker='o', color=color1, label='Revenue')
ax1.set_xlabel("Bulan")
ax1.set_ylabel("Revenue", color=color1)
ax1.tick_params(axis='y', labelcolor=color1)

# Putar label sumbu X agar tidak menumpuk
ax1.set_xticks(range(len(monthly_sales_df.index)))
ax1.set_xticklabels(monthly_sales_df.index, rotation=45, ha='right')

# --- Konfigurasi Sumbu Y Kanan (Orders) ---
ax2 = ax1.twinx()
color2 = 'tab:orange'
ax2.plot(monthly_sales_df.index, monthly_sales_df['total_orders'], linestyle='--', marker='o', color=color2, label='Orders')
ax2.set_ylabel("Orders", color=color2)
ax2.tick_params(axis='y', labelcolor=color2)

# --- Menggabungkan Legenda ---
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')

# Pastikan layout rapi agar label di bawah tidak terpotong
fig1.tight_layout()
st.pyplot(fig1)

# =========================
# GROWTH INFO
# =========================
last_growth = monthly_sales_df['revenue_growth'].iloc[-1]

if pd.notna(last_growth):
    st.info(f":bar_chart: Pertumbuhan revenue bulan terakhir: {last_growth:.2f}%")

st.markdown("---")

# =========================
# CHART 2 (RATING)
# =========================
st.subheader(":star: Distribusi Rating vs Status Order")

if not rating_status_df.empty:
    fig2, ax = plt.subplots(figsize=(10, 5))

    sns.barplot(
        x='order_status',
        y='count',
        hue='review_score',
        data=rating_status_df,
        ax=ax,
        palette='viridis'
    )

    # Putar label x-axis menggunakan tick_params dari axes
    ax.tick_params(axis='x', rotation=45)
    
    fig2.tight_layout()
    st.pyplot(fig2)
else:
    st.warning("Tidak ada data rating")

st.markdown("---")

# =========================
# INSIGHT
# =========================
st.subheader(":bar_chart: Insight")

insight = create_insight(monthly_sales_df)

if insight:
    best_month, worst_month, growth = insight

    st.success(f" :chart_with_upwards_trend: Penjualan tertinggi terjadi pada bulan {best_month}")
    st.warning(f" :chart_with_downwards_trend: Penjualan terendah terjadi pada bulan {worst_month}")

# =========================
# DATA TABLE
# =========================
st.subheader(":page_facing_up: Data Summary")
st.dataframe(main_df)

# =========================
# FOOTER
# =========================
st.caption("Copyright © Naufal 2026")