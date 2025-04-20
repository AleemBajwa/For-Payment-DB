import streamlit as st
import pandas as pd
import plotly.express as px
import os

# === Load the Excel file ===
data_file = "For_Payment_DB.xlsx"
df = pd.read_excel(data_file, header=1)  # Skip first row; use second row as header

# === Clean-up and drop fully empty rows ===
df.dropna(how='all', inplace=True)

# === Fix column name spacing if needed ===
df.columns = df.columns.str.strip()

# === Dashboard Title ===
st.markdown("""
    <div style="background-color:#0A5275;padding:15px;border-radius:10px">
    <h2 style="color:white;text-align:center;">📊 District Data Dashboard</h2>
    </div>
    """, unsafe_allow_html=True)

# === Summary Stats (Global) ===
st.subheader("📈 Overall Summary")

col1, col2, col3 = st.columns(3)
col4, col5 = st.columns(2)

with col1:
    unique_cnic = df['MotherCNIC'].nunique(dropna=True)
    st.metric("👩‍🦰 Unique Mothers (CNIC)", unique_cnic)

with col2:
    total_visits = len(df)
    st.metric("📋 Total Visits", total_visits)

with col3:
    unique_districts = df['District'].nunique(dropna=True)
    st.metric("🏙️ Unique Districts", unique_districts)

with col4:
    unique_tehsils = df['Tehsil'].nunique(dropna=True)
    st.metric("🏞️ Unique Tehsils", unique_tehsils)

with col5:
    total_amount = df['Amount'].sum(skipna=True) if 'Amount' in df.columns else 0
    st.metric("💸 Total Amount", f"{total_amount:,.0f}")

# === Sidebar: District Filter ===
st.sidebar.title("📍 Filters")
districts = df['District'].dropna().unique()
selected_district = st.sidebar.selectbox("Select a District", sorted(districts))

# === Filtered Data ===
filtered_df = df[df['District'] == selected_district]

# === District Stats ===
st.subheader(f"📍 Statistics for `{selected_district}`")
st.write(f"**Total Records:** {len(filtered_df)}")

# === Charts ===
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

# === Expandable Table ===
with st.expander("📄 View Full Table"):
    st.dataframe(filtered_df)

# === Download Button ===
output_file = f"{selected_district.replace(' ', '_')}.xlsx"
filtered_df.to_excel(output_file, index=False)

with open(output_file, "rb") as file:
    st.download_button(
        label="📥 Download Excel File",
        data=file,
        file_name=output_file,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
