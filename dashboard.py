import streamlit as st
import pandas as pd
import plotly.express as px

# === Load data from Google Sheets ===
csv_url = "https://docs.google.com/spreadsheets/d/1Y3EITLOqTCHQkkaOTB7BJb2qIxBaA-mWqLlNs7JXtdA/export?format=csv"
df = pd.read_csv(csv_url)

# === CLEANING SECTION ===
df.dropna(how='all', inplace=True)                          # Drop blank rows
df.columns = df.columns.str.strip()                         # Clean header names
df = df[df['Sr'].astype(str).str.lower() != 'sr']           # Drop repeated headers inside data

# Strip whitespace in all text columns
for col in df.select_dtypes(include='object').columns:
    df[col] = df[col].str.strip()

# Normalize key location fields
df['District'] = df['District'].str.title()
df['Tehsil'] = df['Tehsil'].str.title()

# === Clean and strictly validate Amount column ===
df['Amount'] = (
    df['Amount']
    .astype(str)
    .str.replace(",", "", regex=False)
    .str.replace(" ", "")
)

# Only keep rows where Amount is a clean integer (strict match)
df = df[df['Amount'].str.fullmatch(r"\d+")]
df['Amount'] = pd.to_numeric(df['Amount'])

# === Drop any rows missing required data ===
df = df[df['District'].notna() & df['Tehsil'].notna()]

# === DASHBOARD HEADER ===
st.markdown("""
    <div style="background-color:#0A5275;padding:15px;border-radius:10px">
    <h2 style="color:white;text-align:center;">📊 District Data Dashboard</h2>
    </div>
    """, unsafe_allow_html=True)

# === SUMMARY STATS ===
st.subheader("📈 Overall Summary")

col1, col2, col3 = st.columns(3)
col4, col5 = st.columns(2)

with col1:
    st.metric("👩‍🦰 Unique Mothers (CNIC)", df['MotherCNIC'].nunique())

with col2:
    st.metric("📋 Total Visits", len(df))

with col3:
    st.metric("🏙️ Unique Districts", df['District'].nunique())

with col4:
    st.metric("🏞️ Unique Tehsils", df['Tehsil'].nunique())

with col5:
    total_amount = df['Amount'].sum()
    st.metric("💸 Total Amount", f"{total_amount:,.0f}")

# === SIDEBAR FILTER ===
st.sidebar.title("📍 Filter by District")
districts = sorted(df['District'].dropna().unique())
selected_district = st.sidebar.selectbox("Select a District", districts)

filtered_df = df[df['District'] == selected_district]

st.subheader(f"📍 Statistics for `{selected_district}`")
st.write(f"**Total Records:** {len(filtered_df)}")

# === CHARTS ===
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Visits by Tehsil")
    fig1 = px.bar(filtered_df, x='Tehsil', title='Visits by Tehsil')
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.markdown("#### Amount Distribution")
    if 'Amount' in filtered_df.columns:
        df_amount = filtered_df.groupby('Tehsil')['Amount'].sum().reset_index()
        fig2 = px.pie(df_amount, values='Amount', names='Tehsil', title='Total Amount by Tehsil')
        st.plotly_chart(fig2, use_container_width=True)

# === DATA TABLE + DOWNLOAD ===
with st.expander("📄 View Data Table"):
    st.dataframe(filtered_df)

output_file = f"{selected_district.replace(' ', '_')}.xlsx"
filtered_df.to_excel(output_file, index=False)

with open(output_file, "rb") as file:
    st.download_button(
        label="📥 Download District Data",
        data=file,
        file_name=output_file,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
