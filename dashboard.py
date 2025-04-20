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

clear_date_filter = st.sidebar.checkbox("🗓️ Clear Date Filter", value=False)
valid_dates = df['Visit_Date_Time'].dropna()
start_date, end_date = None, None

if not clear_date_filter and not valid_dates.empty:
    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()
    date_range = st.sidebar.date_input("Filter by Visit Date", (min_date, max_date), min_value=min_date, max_value=max_date)
    start_date, end_date = date_range if isinstance(date_range, tuple) else (min_date, max_date)

stage_options = sorted(df['StageCode'].dropna().unique().tolist())
selected_stage = st.sidebar.selectbox("🧮 Filter by StageCode", ["All"] + stage_options)

filtered_df = df.copy()
if selected_district != "All":
    filtered_df = filtered_df[filtered_df['District'] == selected_district]
else:
    filtered_df = filtered_df[filtered_df['District'].isin(project_districts)]

if start_date and end_date:
    filtered_df = filtered_df[
        (filtered_df['Visit_Date_Time'].dt.date >= start_date) &
        (filtered_df['Visit_Date_Time'].dt.date <= end_date)
    ]

if selected_stage != "All":
    filtered_df = filtered_df[filtered_df['StageCode'] == selected_stage]

st.markdown("""
    <div style="background-color:#0A5275;padding:15px;border-radius:10px">
    <h2 style="color:white;text-align:center;">📊 District Data Dashboard</h2>
    </div>
    """, unsafe_allow_html=True)

# Summary
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

label_format = dict(texttemplate="%{text:,.0f}", textposition="auto")

if selected_district == "All":
    st.subheader("📊 District-wise Overview")
    amt_df = filtered_df.groupby('District')['Amount'].sum().reset_index()
    fig_amt = px.bar(amt_df, x='District', y='Amount', text='Amount',
                     color='District', title="💸 Total Amount by District",
                     color_discrete_sequence=px.colors.qualitative.Set2)
    fig_amt.update_traces(texttemplate="%{text:,.0f}")
    fig_amt.update_layout(showlegend=False, xaxis_tickangle=90)
    st.plotly_chart(fig_amt, use_container_width=True)

    cnic_df = filtered_df.groupby('District')['MotherCNIC'].nunique().reset_index()
    fig_cnic = px.bar(cnic_df, x='District', y='MotherCNIC', text='MotherCNIC',
                      color='District', title="👩‍🍼 Total PLWs by District",
                      color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_cnic.update_traces(texttemplate="%{text:,.0f}")
    fig_cnic.update_layout(showlegend=False, xaxis_tickangle=90)
    st.plotly_chart(fig_cnic, use_container_width=True)

st.subheader("🧮 Visits by StageCode")
stage = filtered_df.groupby('StageCode').size().reset_index(name='Count')
fig_stage = px.bar(stage, x='StageCode', y='Count', text='Count',
                   color='StageCode', title="Visits by StageCode",
                   color_discrete_sequence=px.colors.qualitative.Set3)
fig_stage.update_traces(**label_format)
fig_stage.update_layout(showlegend=False)
st.plotly_chart(fig_stage, use_container_width=True)

if 'Visit_Date_Time' in filtered_df:
    st.subheader("📈 Visit Trend Over Time")
    group_by = st.radio("Group Trend By", ["Daily", "Monthly", "Yearly"], horizontal=True)
    if group_by == "Monthly":
        filtered_df['Trend'] = filtered_df['Visit_Date_Time'].dt.to_period('M').dt.to_timestamp()
    elif group_by == "Yearly":
        filtered_df['Trend'] = filtered_df['Visit_Date_Time'].dt.to_period('Y').dt.to_timestamp()
    else:
        filtered_df['Trend'] = filtered_df['Visit_Date_Time'].dt.date
    trend = filtered_df.groupby('Trend').size().reset_index(name="Visits")
    fig_trend = px.line(trend, x='Trend', y='Visits', title=f"Visits Over Time ({group_by})", markers=True)
    st.plotly_chart(fig_trend, use_container_width=True)

if 'DOB' in filtered_df:
    st.subheader("👶 Age Group Distribution")
    ages = ((pd.to_datetime("today") - pd.to_datetime(filtered_df['DOB'], errors='coerce')).dt.days // 365).dropna().astype(int)
    def age_bucket(age):
        if age <= 17: return "0–17"
        elif age <= 25: return "18–25"
        elif age <= 35: return "26–35"
        elif age <= 40: return "36–40"
        elif age <= 49: return "41–49"
        else: return "50+"
    age_df = ages.apply(age_bucket).value_counts().reindex(["0–17", "18–25", "26–35", "36–40", "41–49", "50+"], fill_value=0).reset_index()
    age_df.columns = ['Age Group', 'Count']
    fig_age = px.bar(age_df, x='Age Group', y='Count', text='Count',
                     color='Age Group', title="Age Group Distribution",
                     color_discrete_sequence=px.colors.qualitative.Bold)
    fig_age.update_traces(**label_format)
    fig_age.update_layout(showlegend=False)
    st.plotly_chart(fig_age, use_container_width=True)

# Top 10 Facility Charts (Visible for All districts)
if selected_district == "All" and 'Registration_Facility' in df.columns:
    st.subheader("🏥 Top 10 Facilities (All Districts)")
    overall_df = df[df['District'].isin(project_districts)]
    if start_date and end_date:
        overall_df = overall_df[
            (overall_df['Visit_Date_Time'].dt.date >= start_date) &
            (overall_df['Visit_Date_Time'].dt.date <= end_date)
        ]
    if selected_stage != "All":
        overall_df = overall_df[overall_df['StageCode'] == selected_stage]

    top_visits = overall_df['Registration_Facility'].value_counts().reset_index().head(10)
    top_visits.columns = ['Registration Facility', 'Visits']
    fig_v = px.bar(top_visits, x='Visits', y='Registration Facility',
                   orientation='h', text='Visits', title="Top 10 Facilities by Visits",
                   color='Registration Facility', color_discrete_sequence=px.colors.qualitative.Prism)
    fig_v.update_traces(**label_format)
    fig_v.update_layout(showlegend=False, margin=dict(l=150))
    st.plotly_chart(fig_v, use_container_width=True)

    top_amt = overall_df.groupby('Registration_Facility')['Amount'].sum().reset_index()
    top_amt = top_amt.sort_values('Amount', ascending=False).head(10)
    fig_a = px.bar(top_amt, x='Amount', y='Registration_Facility',
                   orientation='h', text='Amount', title="Top 10 Facilities by Amount",
                   color='Registration_Facility', color_discrete_sequence=px.colors.qualitative.Alphabet)
    fig_a.update_traces(texttemplate="%{text:,.0f}")
    fig_a.update_layout(showlegend=False, margin=dict(l=150))
    st.plotly_chart(fig_a, use_container_width=True)

# Download Section
if selected_district != "All":
    st.subheader("📄 Data Table")
    st.dataframe(filtered_df.head(100))
    if not filtered_df.empty:
        fname = f"{selected_district.replace(' ', '_')}_{date.today()}.xlsx"
        filtered_df.to_excel(fname, index=False)
        with open(fname, "rb") as f:
            st.download_button("📥 Download Filtered Data", f, fname, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
