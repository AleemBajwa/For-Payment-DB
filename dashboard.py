import streamlit as st
import pandas as pd

# === Load Google Sheet CSV ===
csv_url = "https://docs.google.com/spreadsheets/d/1Y3EITLOqTCHQkkaOTB7BJb2qIxBaA-mWqLlNs7JXtdA/export?format=csv"
df = pd.read_csv(csv_url)

# === Show raw structure ===
st.subheader("🧾 Raw Data Preview")
st.dataframe(df.head())

st.write("🧠 Shape:", df.shape)
st.write("📋 Columns:", df.columns.tolist())

# === Clean headers ===
df.columns = df.columns.str.strip()
df = df[df['Sr'].astype(str).str.lower() != 'sr']

# === Clean all text columns ===
for col in df.select_dtypes(include='object').columns:
    df[col] = df[col].str.strip()

# === Normalize District/Tehsil ===
df['District'] = df['District'].str.title()
df['Tehsil'] = df['Tehsil'].str.title()

# === Amount Column Debug ===
st.subheader("💸 Amount Column Preview")
st.write(df['Amount'].unique()[:50])

# === Convert Amount Safely ===
df['Amount'] = (
    df['Amount']
    .astype(str)
    .str.replace(",", "", regex=False)
    .str.replace(" ", "")
)
df['Amount_clean'] = pd.to_numeric(df['Amount'], errors='coerce')

# === SHOW RAW STATS ===
st.subheader("📊 Verified Stats (No Filtering)")
st.write("🧮 Unique Mother CNICs:", df['MotherCNIC'].nunique())
st.write("📑 Total Visits (Rows):", len(df))
st.write("🏙️ Unique Districts:", df['District'].nunique())
st.write("🏞️ Unique Tehsils:", df['Tehsil'].nunique())
st.write("💰 Total Amount (Cleaned):", f"{df['Amount_clean'].sum():,.0f}")
