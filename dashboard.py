import streamlit as st
import pandas as pd
import plotly.express as px
import os

# === Load Data ===
data_file = r"D:\PHCIP\Planning\Dataset\20250414\For Payment DB.xlsx"
df = pd.read_excel(data_file)

# === Sidebar: Filter by District ===
st.sidebar.title("📍 Filters")
districts = df['District'].dropna().unique()
selected_district = st.sidebar.selectbox("Select a District", sorted(districts))

# === Filter Data ===
filtered_df = df[df['District'] == selected_district]

# === Branding Header ===
st.markdown("""
    <div style="background-color:#0A5275;padding:10px;border-radius:10px">
    <h2 style="color:white;text-align:center;">📊 District Data Dashboard</h2>
    </div>
    """, unsafe_allow_html=True)

# === Stats Section ===
st.subheader(f"📍 Statistics for: `{selected_district}`")
st.write(f"Total Records: **{len(filtered_df)}**")

# === Charts ===
col1, col2 = st.columns(2)

with col1:
    # Visit count by Tehsil
    fig1 = px.bar(filtered_df, x='Tehsil', title='Visits by Tehsil')
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    # Total amount per Tehsil
    if 'Amount' in filtered_df.columns:
        df_amount = filtered_df.groupby('Tehsil')['Amount'].sum().reset_index()
        fig2 = px.pie(df_amount, values='Amount', names='Tehsil', title='Amount Distribution')
        st.plotly_chart(fig2, use_container_width=True)

# === Table Preview ===
with st.expander("📄 View Raw Data Table"):
    st.dataframe(filtered_df)

# === Download Section ===
output_file = f"{selected_district.replace(' ', '_')}.xlsx"
filtered_df.to_excel(output_file, index=False)

with open(output_file, "rb") as f:
    st.download_button(
        label="📥 Download District Data",
        data=f,
        file_name=output_file,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
