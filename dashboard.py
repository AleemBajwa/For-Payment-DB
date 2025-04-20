import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

@st.cache_data
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1kqKFxObhH9l6tZzdPXINDVa8HdyZC8_73idCl5R0WVQ/export?format=csv"
    df = pd.read_csv(url)
    df.dropna(how='all', inplace=True)
    df.columns = df.columns.str.strip()
    df = df[df['VisitId'].astype(str).str.lower() != 'visitid']
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].str.strip()
    df['District'] = df['District'].str.title()
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    if 'Visit_Date_Time' in df.columns:
        df['Visit_Date_Time'] = pd.to_datetime(df['Visit_Date_Time'], format="%d-%b-%y", errors='coerce')
    return df

with st.spinner("Loading data..."):
    df = load_data()

project_districts = [
    "Bahawalnagar", "Bahawalpur", "Bhakkar", "Dera Ghazi Khan", "Khushab",
    "Layyah", "Lodhran", "Mianwali", "Muzaffargarh", "Rahim Yar Khan", "Rajanpur"
]

st.sidebar.title("📍 Filters")
show_all = st.sidebar.checkbox("🔓 Show Non-Project Districts", value=False)
district_options = sorted(df['District'].dropna().unique()) if show_all else sorted([d for d in df['District'].unique() if d in project_districts])
selected_district = st.sidebar.selectbox("Select District", ["All"] + district_options)

# === Clearable Date Filter ===
clear_date_filter = st.sidebar.checkbox("🗓️ Clear Date Filter", value=False)
valid_dates = df['Visit_Date_Time'].dropna()
has_valid_dates = not valid_dates.empty
start_date, end_date = None, None

if has_valid_dates and not clear_date_filter:
    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()
    date_range = st.sidebar.date_input(
        "Filter by Visit Date",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    start_date, end_date = date_range if isinstance(date_range, tuple) else (min_date, max_date)

stage_options = sorted(df['StageCode'].dropna().unique().tolist())
selected_stage = st.sidebar.selectbox("🧮 Filter by StageCode", ["All"] + stage_options)

filtered_df = df.copy()
if selected_district != "All":
    filtered_df = filtered_df[filtered_df['District'] == selected_district]
else:
    filtered_df = filtered_df[filtered_df['District'].isin(district_options)]

if has_valid_dates and not clear_date_filter:
    filtered_df = filtered_df[
        (filtered_df['Visit_Date_Time'].dt.date >= start_date) &
        (filtered_df['Visit_Date_Time'].dt.date <= end_date)
    ]

if selected_stage != "All":
    filtered_df = filtered_df[filtered_df['StageCode'] == selected_stage]

# === Header ===
st.markdown("""
    <div style="background-color:#0A5275;padding:15px;border-radius:10px">
    <h2 style="color:white;text-align:center;">📊 District Data Dashboard</h2>
    </div>
    """, unsafe_allow_html=True)

# === Summary ===
st.subheader("📈 Summary Stats")
col1, col2, col3 = st.columns(3)
col4, col5 = st.columns(2)
with col1:
    st.metric("👩‍🦰 Unique Mother CNICs", f"{filtered_df['MotherCNIC'].nunique():,}")
with col2:
    st.metric("📋 Total Visits", f"{len(filtered_df):,}")
with col3:
    st.metric("🏙️ Unique Districts", f"{filtered_df['District'].nunique():,}")
with col4:
    st.metric("💸 Total Amount", f"{filtered_df['Amount'].sum():,.0f}")
with col5:
    if 'Registration_Facility' in filtered_df.columns:
        st.metric("🏥 Unique Facilities", f"{filtered_df['Registration_Facility'].nunique():,}")

# === Format helper ===
label_format = dict(texttemplate="%{text:,.0f}", textposition="auto")

# === Charts ===
if selected_district == "All":
    st.subheader("📊 District-wise Overview")
    district_amt = filtered_df.groupby('District')['Amount'].sum().reset_index()
    fig1 = px.bar(district_amt, x='District', y='Amount', text='Amount',
                  color='District', title="💸 Total Amount by District",
                  color_discrete_sequence=px.colors.qualitative.Set2)
    fig1.update_traces(texttemplate="%{text:,.0f}")
    fig1.update_layout(showlegend=False, xaxis_tickangle=90)
    st.plotly_chart(fig1, use_container_width=True)

    district_cnic = filtered_df.groupby('District')['MotherCNIC'].nunique().reset_index()
    fig2 = px.bar(district_cnic, x='District', y='MotherCNIC', text='MotherCNIC',
                  color='District', title="👩‍🍼 Total PLWs by District",
                  color_discrete_sequence=px.colors.qualitative.Pastel)
    fig2.update_traces(texttemplate="%{text:,.0f}")
    fig2.update_layout(showlegend=False, xaxis_tickangle=90)
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("🧮 Visits by StageCode")
stage = filtered_df.groupby('StageCode').size().reset_index(name='Count')
fig3 = px.bar(stage, x='StageCode', y='Count', text='Count',
              color='StageCode', title="Visits by StageCode",
              color_discrete_sequence=px.colors.qualitative.Set3)
fig3.update_traces(**label_format)
fig3.update_layout(showlegend=False)
st.plotly_chart(fig3, use_container_width=True)

if 'Visit_Date_Time' in filtered_df:
    st.subheader("📈 Visit Trend Over Time")
    trend_type = st.radio("Group By", ["Daily", "Monthly", "Yearly"], horizontal=True)
    if trend_type == "Monthly":
        filtered_df['Trend'] = filtered_df['Visit_Date_Time'].dt.to_period('M').dt.to_timestamp()
    elif trend_type == "Yearly":
        filtered_df['Trend'] = filtered_df['Visit_Date_Time'].dt.to_period('Y').dt.to_timestamp()
    else:
        filtered_df['Trend'] = filtered_df['Visit_Date_Time'].dt.date
    trend = filtered_df.groupby('Trend').size().reset_index(name="Visits")
    fig4 = px.line(trend, x='Trend', y='Visits', title=f"Visits Over Time ({trend_type})", markers=True)
    st.plotly_chart(fig4, use_container_width=True)

if 'DOB' in filtered_df:
    st.subheader("👶 Age Group Distribution")
    ages = ((pd.to_datetime("today") - pd.to_datetime(filtered_df['DOB'], errors='coerce')).dt.days // 365).dropna().astype(int)
    def age_group(a):
        if a <= 17: return "0–17"
        elif a <= 25: return "18–25"
        elif a <= 35: return "26–35"
        elif a <= 40: return "36–40"
        elif a <= 49: return "41–49"
        return "50+"
    age_groups = ages.apply(age_group)
    age_df = age_groups.value_counts().reindex(["0–17", "18–25", "26–35", "36–40", "41–49", "50+"], fill_value=0).reset_index()
    age_df.columns = ['Age Group', 'Count']
    fig5 = px.bar(age_df, x='Age Group', y='Count', text='Count',
                  color='Age Group', title="Age Group Distribution",
                  color_discrete_sequence=px.colors.qualitative.Bold)
    fig5.update_traces(**label_format)
    fig5.update_layout(showlegend=False)
    st.plotly_chart(fig5, use_container_width=True)

if selected_district != "All" and 'Registration_Facility' in filtered_df:
    st.subheader("🏥 Registration Facility Stats")
    visits = filtered_df['Registration_Facility'].value_counts().reset_index().head(10)
    visits.columns = ['Registration Facility', 'Visits']
    fig6 = px.bar(visits, x='Visits', y='Registration Facility',
                  orientation='h', text='Visits', title="Top 10 Facilities by Visits",
                  color='Registration Facility', color_discrete_sequence=px.colors.qualitative.Prism)
    fig6.update_traces(**label_format)
    fig6.update_layout(showlegend=False, margin=dict(l=150))
    st.plotly_chart(fig6, use_container_width=True)

    amounts = filtered_df.groupby('Registration_Facility')['Amount'].sum().reset_index()
    amounts = amounts.sort_values('Amount', ascending=False).head(10)
    fig7 = px.bar(amounts, x='Amount', y='Registration_Facility',
                  orientation='h', text='Amount', title="Top 10 Facilities by Amount",
                  color='Registration_Facility', color_discrete_sequence=px.colors.qualitative.Alphabet)
    fig7.update_traces(texttemplate="%{text:,.0f}", textposition="auto")
    fig7.update_layout(showlegend=False, margin=dict(l=150))
    st.plotly_chart(fig7, use_container_width=True)

if selected_district != "All":
    st.subheader("📄 Data Table")
    st.dataframe(filtered_df.head(100))
    if not filtered_df.empty:
        file_name = f"{selected_district.replace(' ', '_')}_{date.today()}.xlsx"
        filtered_df.to_excel(file_name, index=False)
        with open(file_name, "rb") as f:
            st.download_button("📥 Download Filtered Data", f, file_name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
