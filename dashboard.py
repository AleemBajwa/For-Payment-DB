import streamlit as st
import pandas as pd
import plotly.express as px

# === Load Google Sheets CSV ===
csv_url = "https://docs.google.com/spreadsheets/d/1Y3EITLOqTCHQkkaOTB7BJb2qIxBaA-mWqLlNs7JXtdA/export?format=csv"
df = pd.read_csv(csv_url)

# === Step 1: Initial view to understand structure ===
st.subheader("🔍 RAW DATA (first 5 rows)")
st.dataframe(df.head())

# === Step 2: Fix headers and repeated rows ===
df.columns = df.columns.str.strip()
df.dropna(how='all', inplace=True)

# Remove repeated headers inside the data (e.g., if "Sr" is repeated)
df = df[df['Sr'].astype(str) != 'Sr']

# Strip whitespace from object columns
for col in df.select_dtypes(include='object').columns:
    df[col] = df[col].str.strip()

# Convert Amount column to numeric
df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')

# Show all column names for inspection
st.subheader("🧠 Column Names")
st.write(df.columns.tolist())

# Show unique values in District and Tehsil to verify
st.subheader("📋 District Samples")
st.write(df['District'].unique())

st.subheader("📋 Tehsil Samples")
st.write(df['Tehsil'].unique())

# === Clean Data Preview ===
st.subheader("🧼 Cleaned Data Preview")
st.dataframe(df.head())

# === Reliable Stats Section ===
st.subheader("📈 Verified Summary Stats")

col1, col2, col3 = st.columns(3)
col4, col5 = st.columns(2)

with col1:
    st.metric("👩‍🦰 Unique Mothers (CNIC)", df['MotherCNIC'].nunique())

with col2:
    st.metric("📋 Total Visits (Rows)", len(df))

with col3:
    st.metric("🏙️ Unique Districts", df['District'].nunique())

with col4:
    st.metric("🏞️ Unique Tehsils", df['Tehsil'].nunique())

with col5:
    total_amount = df['Amount'].sum()
    st.metric("💸 Total Amount", f"{total_amount:,.0f}")
