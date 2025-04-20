import streamlit as st
import pandas as pd
import plotly.express as px
import os

# === Load the Excel file ===
data_file = "For_Payment_DB.xlsx"  # EXACT match with your uploaded file
df = pd.read_excel(data_file)

# === Sidebar: Select District ===
st.sidebar.title("📍 Filters")
districts = df['District'].dropna().unique()
selected_district = st.sidebar.selectbox("Select a District", sorted(districts))

# === Filter Data ===
filtered_df = df[df['District'] == selected_district]

# === Page Header ===
st.markdown("""
    <div style="background-color:#0A5275;padding:15px;border-radius:10px">
    <h2 style="color:white;text-align:center;">📊 District Data Dashboard</h2>
    </div>
    """, unsafe_allow_html=True)

# === Summary ===
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
