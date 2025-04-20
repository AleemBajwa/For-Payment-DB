import streamlit as st
import pandas as pd
import plotly.express as px

# === Load data from Google Sheets ===
csv_url = "https://docs.google.com/spreadsheets/d/1Y3EITLOqTCHQkkaOTB7BJb2qIxBaA-mWqLlNs7JXtdA/export?format=csv"
df = pd.read_csv(csv_url)

# === CLEANING SECTION ===
df.dropna(how='all', inplace=True)
df.columns = df.columns.str.strip()
df = df[df['Sr'].astype(str).str.lower() != 'sr']

for col in df.select_dtypes(include='object').columns:
    df[col] = df[col].str.strip()

df['District'] = df['District'].str.title()

df['Amount'] = (
    df['Amount']
    .astype(str)
    .str.replace(",", "", regex=False)
    .str.replace(" ", "")
)
df = df[df['Amount'].str.fullmatch(r"\d+")]
df['Amount'] = pd.to_numeric(df['Amount'])

if 'Visit_Date_Time' in df.columns:
    df['Visit_Date_Time'] = pd.to_datetime(df['Visit_Date_Time'], errors='coerce')

# === PROJECT DISTRICTS ===
project_districts = [
    "Bahawalnagar", "Bahawalpur", "Bhakkar", "Dera Ghazi Khan", "Khushab",
    "Layyah", "Lodhran", "Mianwali", "Muzaffargarh", "Rahim Yar Khan", "Rajanpur"
]

# === SIDEBAR FILTERS ===
st.sidebar.title("📍 Filters")

show_all = st.sidebar.checkbox("🔓 Show Non-Project Districts", value=False)
district_options = sorted(df['District'].dropna().unique()) if show_all else sorted([d for d in df['District'].unique() if d in project_districts])
selected_district = st.sidebar.selectbox("Select District", ["All"] + district_options)

# Date range filter
min_date = df['Visit_Date_Time'].min()
max_date = df['Visit_Date_Time'].max()
date_range = st.sidebar.date_input(
    "📆 Filter by Visit Date",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

# StageCode filter
stage_options = sorted(df['StageCode'].dropna().unique().tolist())
selected_stage = st.sidebar.selectbox("🧮 Filter by StageCode", ["All"] + stage_options)

# === FILTERED DATA ===
filtered_df = df.copy()

if selected_district != "All":
    filtered_df = filtered_df[filtered_df['District'] == selected_district]
else:
    filtered_df = filtered_df[filtered_df['District'].isin(district_options)]

filtered_df = filtered_df[
    (filtered_df['Visit_Date_Time'].dt.date >= start_date) &
    (filtered_df['Visit_Date_Time'].dt.date <= end_date)
]

if selected_stage != "All":
    filtered_df = filtered_df[filtered_df['StageCode'] == selected_stage]

# === HEADER ===
st.markdown("""
    <div style="background-color:#0A5275;padding:15px;border-radius:10px">
    <h2 style="color:white;text-align:center;">📊 District Data Dashboard</h2>
    </div>
    """, unsafe_allow_html=True)

# === SUMMARY STATS ===
st.subheader("📈 Summary Stats")

col1, col2, col3 = st.columns(3)
col4 = st.columns(1)[0]

with col1:
    st.metric("👩‍🦰 Unique Mother CNICs", f"{filtered_df['MotherCNIC'].nunique():,}")
with col2:
    st.metric("📋 Total Visits", f"{len(filtered_df):,}")
with col3:
    st.metric("🏙️ Unique Districts", f"{filtered_df['District'].nunique():,}")
with col4:
    st.metric("💸 Total Amount", f"{filtered_df['Amount'].sum():,.0f}")

# === DISTRICT-WISE CHARTS ===
if selected_district == "All":
    st.subheader("📊 District-wise Overview")
    col1, col2 = st.columns(2)

    with col1:
        df_district_amount = filtered_df.groupby('District')['Amount'].sum().reset_index()
        df_district_amount['Amount'] = df_district_amount['Amount'].round(0)
        fig_amount = px.bar(
            df_district_amount,
            x='District',
            y='Amount',
            title="💸 Total Amount by District",
            labels={"Amount": "Total Amount"},
            text_auto='.2s'
        )
        st.plotly_chart(fig_amount, use_container_width=True)

    with col2:
        df_mothers = filtered_df.groupby('District')['MotherCNIC'].nunique().reset_index()
        df_mothers.columns = ['District', 'Unique Mothers']
        fig_mothers = px.bar(
            df_mothers,
            x='District',
            y='Unique Mothers',
            title="👩‍🍼 Total PLWs by District",
            labels={"Unique Mothers": "PLWs"},
            text_auto='.2s'
        )
        st.plotly_chart(fig_mothers, use_container_width=True)

# === STAGECODE CHART ===
st.subheader("🧮 Visits by StageCode")
stage_chart = (
    filtered_df.groupby('StageCode')
    .size()
    .reset_index(name="Visit Count")
    .sort_values("Visit Count", ascending=False)
)
fig_stage = px.bar(
    stage_chart,
    x='StageCode',
    y='Visit Count',
    title="Visits by StageCode",
    text_auto='.2s'
)
st.plotly_chart(fig_stage, use_container_width=True)

# === TREND CHART ===
if 'Visit_Date_Time' in filtered_df.columns:
    st.subheader("📈 Visit Trend Over Time")

    trend_group = st.radio("Group Trend By", ["Daily", "Monthly", "Yearly"], horizontal=True)

    if trend_group == "Monthly":
        filtered_df['Trend'] = filtered_df['Visit_Date_Time'].dt.to_period('M').dt.to_timestamp()
    elif trend_group == "Yearly":
        filtered_df['Trend'] = filtered_df['Visit_Date_Time'].dt.to_period('Y').dt.to_timestamp()
    else:
        filtered_df['Trend'] = filtered_df['Visit_Date_Time'].dt.date

    trend_df = (
        filtered_df.groupby('Trend')
        .size()
        .reset_index(name="Visits")
        .sort_values('Trend')
    )

    fig_trend = px.line(
        trend_df,
        x='Trend',
        y='Visits',
        title=f"Visits Over Time ({trend_group})",
        markers=True
    )
    st.plotly_chart(fig_trend, use_container_width=True)

# === AGE HISTOGRAM FROM DOB ===
if 'DOB' in filtered_df.columns:
    st.subheader("👶 Age Distribution Histogram")

    dob_series = pd.to_datetime(filtered_df['DOB'], errors='coerce')
    today = pd.to_datetime("today")

    ages = ((today - dob_series).dt.days // 365).dropna().astype(int)
    filtered_df['Age'] = ages

    fig_age_hist = px.histogram(
        ages,
        nbins=15,
        title="Participant Age Distribution",
        labels={'value': 'Age', 'count': 'Number of Records'},
        text_auto='.2s'
    )
    st.plotly_chart(fig_age_hist, use_container_width=True)

# === TABLE & DOWNLOAD ===
st.subheader("📄 Data Table")
st.dataframe(filtered_df)

output_file = f"{selected_district.replace(' ', '_') if selected_district != 'All' else 'All_Districts'}_{start_date}_{end_date}.xlsx"
filtered_df.to_excel(output_file, index=False)

with open(output_file, "rb") as file:
    st.download_button(
        label="📥 Download Filtered Data",
        data=file,
        file_name=output_file,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
