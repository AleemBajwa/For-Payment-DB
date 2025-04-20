import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

# === Cached Data Loader ===
@st.cache_data
def load_data():
    df = pd.read_csv("payment_data.csv")
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

    return df

# === Load Data ===
with st.spinner("Loading data..."):
    df = load_data()

# === DEBUGGING PREVIEW ===
st.subheader("🧪 Raw Data Debug")
st.write("Sample Data:", df.head(10))
st.write("Total Rows Loaded:", len(df))
st.write("Unique Districts:", df['District'].unique())
st.write("Amount Sample:", df['Amount'].head(5))
if 'Visit_Date_Time' in df.columns:
    st.write("Visit_Date_Time Sample:", df['Visit_Date_Time'].dropna().head(5))
else:
    st.error("❌ Visit_Date_Time column missing!")

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

# === Safe Date Filter ===
valid_dates = df['Visit_Date_Time'].dropna() if 'Visit_Date_Time' in df else pd.Series([], dtype='datetime64[ns]')
has_valid_dates = not valid_dates.empty

if has_valid_dates:
    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()
    date_range = st.sidebar.date_input(
        "📆 Filter by Visit Date",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    start_date, end_date = date_range if isinstance(date_range, tuple) else (min_date, max_date)

stage_options = sorted(df['StageCode'].dropna().unique().tolist())
selected_stage = st.sidebar.selectbox("🧮 Filter by StageCode", ["All"] + stage_options)

# === APPLY FILTERS ===
filtered_df = df.copy()

if selected_district != "All":
    filtered_df = filtered_df[filtered_df['District'] == selected_district]
else:
    filtered_df = filtered_df[filtered_df['District'].isin(district_options)]

if has_valid_dates:
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

# === DISTRICT CHARTS ===
if selected_district == "All":
    st.subheader("📊 District-wise Overview")

    df_district_amount = filtered_df.groupby('District')['Amount'].sum().reset_index()
    fig_amount = px.bar(df_district_amount, x='District', y='Amount', title="💸 Total Amount by District", text_auto=True)
    fig_amount.update_layout(showlegend=False, xaxis_tickangle=-45)
    st.plotly_chart(fig_amount, use_container_width=True)

    df_mothers = filtered_df.groupby('District')['MotherCNIC'].nunique().reset_index()
    df_mothers.columns = ['District', 'Unique Mothers']
    fig_mothers = px.bar(df_mothers, x='District', y='Unique Mothers', title="👩‍🍼 Total PLWs by District", text_auto=True)
    fig_mothers.update_layout(showlegend=False, xaxis_tickangle=-45)
    st.plotly_chart(fig_mothers, use_container_width=True)

# === STAGE CHART ===
st.subheader("🧮 Visits by StageCode")
stage_chart = (
    filtered_df.groupby('StageCode')
    .size()
    .reset_index(name="Visit Count")
    .sort_values("Visit Count", ascending=False)
)
fig_stage = px.bar(stage_chart, x='StageCode', y='Visit Count', title="Visits by StageCode", text_auto=True)
fig_stage.update_layout(showlegend=False)
st.plotly_chart(fig_stage, use_container_width=True)

# === VISIT TREND CHART ===
if has_valid_dates:
    st.subheader("📈 Visit Trend Over Time")
    trend_group = st.radio("Group Trend By", ["Daily", "Monthly", "Yearly"], horizontal=True)

    if trend_group == "Monthly":
        filtered_df['Trend'] = filtered_df['Visit_Date_Time'].dt.to_period('M').dt.to_timestamp()
    elif trend_group == "Yearly":
        filtered_df['Trend'] = filtered_df['Visit_Date_Time'].dt.to_period('Y').dt.to_timestamp()
    else:
        filtered_df['Trend'] = filtered_df['Visit_Date_Time'].dt.date

    trend_df = filtered_df.groupby('Trend').size().reset_index(name="Visits").sort_values('Trend')
    fig_trend = px.line(trend_df, x='Trend', y='Visits', title=f"Visits Over Time ({trend_group})", markers=True)
    st.plotly_chart(fig_trend, use_container_width=True)

# === AGE DISTRIBUTION ===
if 'DOB' in filtered_df.columns:
    st.subheader("👶 Age Group Distribution")
    dob_series = pd.to_datetime(filtered_df['DOB'], errors='coerce')
    today = pd.to_datetime("today")
    ages = ((today - dob_series).dt.days // 365).dropna().astype(int)

    def get_age_group(age):
        if age <= 17:
            return "0–17"
        elif age <= 25:
            return "18–25"
        elif age <= 35:
            return "26–35"
        elif age <= 40:
            return "36–40"
        elif age <= 49:
            return "41–49"
        else:
            return "50+"

    age_groups = ages.apply(get_age_group)
    age_group_counts = age_groups.value_counts().reindex(
        ["0–17", "18–25", "26–35", "36–40", "41–49", "50+"], fill_value=0).reset_index()
    age_group_counts.columns = ['Age Group', 'Count']

    fig_age = px.bar(age_group_counts, x='Age Group', y='Count', title="Age Group Distribution", text_auto=True)
    fig_age.update_layout(showlegend=False)
    st.plotly_chart(fig_age, use_container_width=True)

# === DATA TABLE & DOWNLOAD ===
st.subheader("📄 Data Table")
st.dataframe(filtered_df)

output_file = f"{selected_district.replace(' ', '_') if selected_district != 'All' else 'All_Districts'}_{date.today()}.xlsx"
filtered_df.to_excel(output_file, index=False)

with open(output_file, "rb") as file:
    st.download_button(
        label="📥 Download Filtered Data",
        data=file,
        file_name=output_file,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
