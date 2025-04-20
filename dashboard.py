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
df['Tehsil'] = df['Tehsil'].str.title()

# Clean Amount column strictly
df['Amount'] = (
    df['Amount']
    .astype(str)
    .str.replace(",", "", regex=False)
    .str.replace(" ", "")
)
df = df[df['Amount'].str.fullmatch(r"\d+")]
df['Amount'] = pd.to_numeric(df['Amount'])

# Convert date
if 'Visit_Date_Time' in df.columns:
    df['Visit_Date_Time'] = pd.to_datetime(df['Visit_Date_Time'], errors='coerce')

# === PROJECT DISTRICTS ===
project_districts = [
    "Bahawalnagar", "Bahawalpur", "Bhakkar", "Dera Ghazi Khan", "Khushab",
    "Layyah", "Lodhran", "Mianwali", "Muzaffargarh", "Rahim Yar Khan", "Rajanpur"
]

# === SIDEBAR FILTER ===
st.sidebar.title("📍 Filter")

# Toggle: Show non-project districts?
show_all = st.sidebar.checkbox("🔓 Show Non-Project Districts", value=False)

if show_all:
    district_options = sorted(df['District'].dropna().unique())
else:
    district_options = sorted([d for d in df['District'].unique() if d in project_districts])

selected_district = st.sidebar.selectbox("Select District", ["All"] + district_options)

# === FILTERED DATAFRAME ===
if selected_district == "All":
    filtered_df = df[df['District'].isin(district_options)]
else:
    filtered_df = df[df['District'] == selected_district]

# === TITLE ===
st.markdown("""
    <div style="background-color:#0A5275;padding:15px;border-radius:10px">
    <h2 style="color:white;text-align:center;">📊 District Data Dashboard</h2>
    </div>
    """, unsafe_allow_html=True)

# === SUMMARY STATS ===
st.subheader("📈 Summary Stats")

col1, col2, col3 = st.columns(3)
col4, col5 = st.columns(2)

with col1:
    st.metric("👩‍🦰 Unique Mother CNICs", filtered_df['MotherCNIC'].nunique())

with col2:
    st.metric("📋 Total Visits", len(filtered_df))

with col3:
    st.metric("🏙️ Unique Districts", filtered_df['District'].nunique())

with col4:
    st.metric("🏞️ Unique Tehsils", filtered_df['Tehsil'].nunique())

with col5:
    st.metric("💸 Total Amount", f"{filtered_df['Amount'].sum():,.0f}")

# === VISUALS ===
st.subheader("📊 Visualizations")

# 1. District-wise totals (only when viewing all)
if selected_district == "All":
    st.markdown("#### 💰 Total Payments by District")
    df_district_amount = filtered_df.groupby('District')['Amount'].sum().reset_index()
    fig_dist = px.bar(df_district_amount, x='District', y='Amount', title="Total Amount by District")
    st.plotly_chart(fig_dist, use_container_width=True)

# 2. StageCode bar chart
st.markdown("#### 🧮 Visits by StageCode")
stage_chart = (
    filtered_df.groupby('StageCode')
    .size()
    .reset_index(name="Visit Count")
    .sort_values("Visit Count", ascending=False)
)
fig_stage = px.bar(stage_chart, x='StageCode', y='Visit Count', title="Visits by StageCode")
st.plotly_chart(fig_stage, use_container_width=True)

# 3. Time trend
if 'Visit_Date_Time' in filtered_df.columns:
    st.markdown("#### 📈 Visit Trend Over Time")
    trend = (
        filtered_df.groupby(filtered_df['Visit_Date_Time'].dt.date)
        .size()
        .reset_index(name="Visits")
    )
    fig_trend = px.line(trend, x='Visit_Date_Time', y='Visits', title="Visits Over Time")
    st.plotly_chart(fig_trend, use_container_width=True)

# === TABLE & DOWNLOAD ===
st.subheader("📄 Data Table")
st.dataframe(filtered_df)

output_file = f"{selected_district.replace(' ', '_') if selected_district != 'All' else 'All_Districts'}.xlsx"
filtered_df.to_excel(output_file, index=False)

with open(output_file, "rb") as file:
    st.download_button(
        label="📥 Download Data",
        data=file,
        file_name=output_file,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
