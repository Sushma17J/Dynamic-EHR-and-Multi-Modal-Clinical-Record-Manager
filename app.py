
import streamlit as st
import requests
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Healthcare EHR System",
    page_icon="🏥",
    layout="wide"
)

# API configuration
API_URL = st.secrets["API_URL"].rstrip("/")

st.title("🏥 Healthcare EHR Management System")
st.caption("Dynamic Electronic Health Record Management System")

st.divider()

# Sidebar
st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Select Module",
    [
        "Dashboard",
        "Patients",
        "Vital Signs",
        "Medications",
        "Clinical Records",
        "Medical Documents"
    ]
)

# Dashboard
if page == "Dashboard":

    st.header("Dashboard Overview")

    try:
        response = requests.get(
            f"{API_URL}/dashboard/stats",
            timeout=20
        )
        response.raise_for_status()
        stats = response.json()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Patients", stats.get("total_patients", 0))

        with col2:
            st.metric("Clinical Records", stats.get("total_records", 0))

        with col3:
            st.metric("Medical Documents", stats.get("total_documents", 0))

    except requests.RequestException as e:
        st.error(f"Could not connect to the API: {e}")

# Patients
elif page == "Patients":
    st.header("Patient Directory")

    try:
        response = requests.get(f"{API_URL}/patients", timeout=20)
        response.raise_for_status()

        patients = response.json()

        if patients:
            df = pd.DataFrame(patients)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No patients found.")

    except requests.RequestException as e:
        st.error(f"Could not load patients: {e}")

# Other modules - coming next
else:
    st.header(page)
    st.info("This module will be added in the next development step.")
