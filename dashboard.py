import streamlit as st
import pandas as pd
import plotly.express as px
import os

# === Load Excel File (make sure actual header row is used) ===
data_file = "For_Payment_DB.xlsx"
df = pd.read_excel(data_file, header=0)  # Assumes first row is the correct header

# === Clean headers ===
df.dropna(how='all', inplace=True)
df.columns = df.columns.str.strip()  # Remove extra spaces from headers

# === Dashboard Title ===
st.markdown("""
    <div style="background-color:#0A5275;padding:15px;border-radius:10px">
    <h2 style="color:white;text-align:center;">📊 District Data Dashboard</h2>
    </div>
    """, unsafe_allow_html=True)

# === Summary Stats ===
st.subheader("📈 Overall Summary")

col1, col2, col3 = st.columns(3)
col4, col5 = st.columns(2)

with col1:
    st.metric("👩‍🦰 Unique Mothers (CNIC)", df['MotherCNIC'].nunique(dropna=True))

with col2:
    st.metric("📋 Total Visits", len(df))

with col3:
    st.metric("🏙️ Unique Districts", df['District'].nunique(dropna=True))

with col4:
    st.metric("🏞️ Unique Tehsils", df['Tehsil'].nunique(dropna=True))

with col5:
    total_amount = df['Amount'].sum(skipna=True) if 'Amount' in df.columns else 0
    st.metric("💸 Total Amount", f"{total_amount:,.0f}")

# === Sidebar Filter ===
st.sidebar.title("📍 Filter by District")
districts = df['District'].dropna().unique()
selected_district = st.sidebar.selectbox("Select a District", sorted(districts))

# === Filtered Data ===
filtered_df = df[df['District'] == selected_district]

st.subheader(f"📍 Data for `{selected_district}`")
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
with st.expander("📄 View Data Table"):
    st.dataframe(filtered_df)

# === Download Button ===
output_file = f"{selected_district.replace(' ', '_')}.xlsx"
filtered_df.to_excel(output_file, index=False)

with open(output_file, "rb") as file:
    st.download_button(
        label="📥 Download District Data",
        data=file,
        file_name=output_file,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
