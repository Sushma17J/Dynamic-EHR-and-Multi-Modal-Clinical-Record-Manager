
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

# --------------------------------
# PAGE CONFIGURATION
# --------------------------------

st.set_page_config(
    page_title="Healthcare EHR",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------
# API CONFIGURATION
# --------------------------------

API_URL = st.secrets["API_URL"].rstrip("/")
API_KEY = st.secrets["API_KEY"]

HEADERS = {
    "X-API-Key": API_KEY
}


def api_get(endpoint):
    response = requests.get(
        f"{API_URL}{endpoint}",
        headers=HEADERS,
        timeout=30
    )
    response.raise_for_status()
    return response.json()


def api_post(endpoint, data):
    response = requests.post(
        f"{API_URL}{endpoint}",
        headers=HEADERS,
        json=data,
        timeout=30
    )
    response.raise_for_status()
    return response.json()


# --------------------------------
# CUSTOM CSS
# --------------------------------

st.markdown("""
<style>

.stApp {
    background-color: #0B1120;
    color: #E5E7EB;
}

[data-testid="stSidebar"] {
    background-color: #111B2E;
    border-right: 1px solid #25334A;
}

[data-testid="stSidebar"] h1 {
    color: #FFFFFF;
}

h1, h2, h3 {
    color: #F8FAFC;
}

p, label {
    color: #CBD5E1;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1450px;
}

[data-testid="stMetric"] {
    background: linear-gradient(135deg, #17263D, #142B3B);
    border: 1px solid #29445A;
    padding: 22px;
    border-radius: 15px;
}

[data-testid="stMetricLabel"] {
    color: #A7B8CC;
}

[data-testid="stMetricValue"] {
    color: #5EEAD4;
}

div.stButton > button {
    background: linear-gradient(90deg, #0D9488, #14B8A6);
    color: white;
    border: none;
    border-radius: 9px;
    padding: 9px 20px;
    font-weight: 600;
}

div.stButton > button:hover {
    background: #0F766E;
    color: white;
}

div[data-testid="stForm"] {
    background-color: #142238;
    padding: 22px;
    border: 1px solid #29445A;
    border-radius: 15px;
}

[data-testid="stDataFrame"] {
    border: 1px solid #29445A;
    border-radius: 10px;
}

hr {
    border-color: #26374D;
}

</style>
""", unsafe_allow_html=True)


# --------------------------------
# SIDEBAR
# --------------------------------

with st.sidebar:

    st.markdown("# 🏥 MediTrack")
    st.caption("Electronic Health Record System")

    st.divider()

    page = st.radio(
        "MAIN MENU",
        [
            "Dashboard",
            "Patients",
            "Vital Signs",
            "Medications",
            "Clinical Records",
            "Medical Documents"
        ],
        label_visibility="visible"
    )

    st.divider()

    st.markdown("### System Status")
    st.success("Application interface active")
    st.caption("Powered by FastAPI + MongoDB")


# --------------------------------
# HEADER
# --------------------------------

st.markdown(
    "<h1>Healthcare Management</h1>",
    unsafe_allow_html=True
)

st.caption(
    "Centralized Electronic Health Record Management Platform"
)

st.divider()


# --------------------------------
# LOAD PATIENTS
# --------------------------------

def load_patients():
    try:
        return api_get("/patients")
    except requests.RequestException as e:
        st.error(f"Unable to load patients: {e}")
        return []


# --------------------------------
# DASHBOARD
# --------------------------------

if page == "Dashboard":

    st.subheader("Dashboard Overview")
    st.caption("Live statistics from your healthcare database")

    try:
        stats = api_get("/dashboard/stats")

        patients_count = stats.get("total_patients", 0)
        records_count = stats.get("total_clinical_records", 0)
        documents_count = stats.get("total_medical_documents", 0)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "👥 Total Patients",
                patients_count
            )

        with col2:
            st.metric(
                "📋 Clinical Records",
                records_count
            )

        with col3:
            st.metric(
                "📁 Medical Documents",
                documents_count
            )

        st.divider()

        st.subheader("Patient Overview")

        patient_data = load_patients()

        if patient_data:

            df = pd.DataFrame(patient_data)

            if "patient_id" in df.columns and "name" in df.columns:

                display_columns = [
                    col for col in
                    ["patient_id", "name", "age", "gender"]
                    if col in df.columns
                ]

                st.dataframe(
                    df[display_columns].head(10),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Patient information is available, but some display fields are missing.")

        else:
            st.info("No patient records available.")

    except requests.RequestException as e:
        st.error(f"Dashboard API error: {e}")


# --------------------------------
# PATIENTS
# --------------------------------

elif page == "Patients":

    st.subheader("Patient Directory")
    st.caption("View registered patient information")

    patient_data = load_patients()

    if patient_data:

        df = pd.DataFrame(patient_data)

        st.metric("Registered Patients", len(patient_data))

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇ Download Patient Data",
            data=df.to_csv(index=False),
            file_name="patient_records.csv",
            mime="text/csv"
        )

    else:
        st.info("No patient records found.")


# --------------------------------
# VITAL SIGNS
# --------------------------------

elif page == "Vital Signs":

    st.subheader("Vital Signs Monitoring")
    st.caption("Record and monitor patient health measurements")

    patient_data = load_patients()

    if not patient_data:

        st.warning("No patients found. Register patients before adding vital readings.")

    else:

        patient_options = {
            f"{p.get('patient_id', '')} - {p.get('name', 'Unknown')}":
            p.get("patient_id")
            for p in patient_data
            if p.get("patient_id")
        }

        selected_patient = st.selectbox(
            "Select Patient",
            list(patient_options.keys())
        )

        patient_id = patient_options[selected_patient]

        st.divider()

        st.markdown("### Add New Vital Reading")

        with st.form("vital_form"):

            col1, col2 = st.columns(2)

            with col1:
                heart_rate = st.number_input(
                    "Heart Rate (bpm)",
                    min_value=1,
                    max_value=300,
                    value=72
                )

                temperature = st.number_input(
                    "Temperature (°C)",
                    min_value=25.0,
                    max_value=45.0,
                    value=37.0,
                    step=0.1
                )

            with col2:
                spo2 = st.number_input(
                    "SpO2 (%)",
                    min_value=1,
                    max_value=100,
                    value=98
                )

                systolic = st.number_input(
                    "Systolic Blood Pressure (mmHg)",
                    min_value=1,
                    max_value=300,
                    value=120
                )

                diastolic = st.number_input(
                    "Diastolic Blood Pressure (mmHg)",
                    min_value=1,
                    max_value=200,
                    value=80
                )

            submitted = st.form_submit_button(
                "➕ Save Vital Reading",
                use_container_width=True
            )

            if submitted:

                if systolic <= diastolic:
                    st.error("Please check the blood pressure values.")
                else:

                    vital_data = {
                        "heart_rate": heart_rate,
                        "temperature": temperature,
                        "spo2": spo2,
                        "blood_pressure": {
                            "systolic": systolic,
                            "diastolic": diastolic
                        }
                    }

                    try:
                        result = api_post(
                            f"/vitals/{patient_id}",
                            vital_data
                        )

                        st.success(result.get(
                            "message",
                            "Vital reading saved successfully!"
                        ))

                        st.rerun()

                    except requests.RequestException as e:
                        st.error(f"Could not save vital reading: {e}")

        st.divider()

        # VITAL HISTORY

        st.markdown("### Vital Signs History")

        try:

            history = api_get(
                f"/vitals/history/{patient_id}"
            )

            if history:

                history_df = pd.DataFrame(history)

                if "recorded_at" in history_df.columns:
                    history_df["recorded_at"] = pd.to_datetime(
                        history_df["recorded_at"],
                        errors="coerce",
                        utc=True
                    )

                    history_df = history_df.sort_values(
                        "recorded_at"
                    )

                st.dataframe(
                    history_df,
                    use_container_width=True,
                    hide_index=True
                )

                # Heart rate chart
                if "heart_rate" in history_df.columns:

                    st.markdown("#### ❤️ Heart Rate Trend")

                    fig = px.line(
                        history_df,
                        x="recorded_at",
                        y="heart_rate",
                        markers=True,
                        title="Heart Rate Over Time",
                        labels={
                            "recorded_at": "Recorded Time",
                            "heart_rate": "Heart Rate (bpm)"
                        }
                    )

                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="#0B1120",
                        plot_bgcolor="#142238"
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True
                    )

                # Other vital charts
                chart_options = {
                    "temperature": "Temperature (°C)",
                    "spo2": "SpO2 (%)",
                    "systolic": "Systolic Pressure (mmHg)",
                    "diastolic": "Diastolic Pressure (mmHg)"
                }

                for column, label in chart_options.items():

                    if column in history_df.columns:

                        with st.expander(f"View {label} trend"):

                            fig = px.line(
                                history_df,
                                x="recorded_at",
                                y=column,
                                markers=True,
                                labels={
                                    "recorded_at": "Recorded Time",
                                    column: label
                                }
                            )

                            fig.update_layout(
                                template="plotly_dark",
                                paper_bgcolor="#0B1120",
                                plot_bgcolor="#142238"
                            )

                            st.plotly_chart(
                                fig,
                                use_container_width=True
                            )

            else:
                st.info("No vital readings recorded for this patient yet.")

        except requests.RequestException as e:
            st.error(f"Could not load vital history: {e}")


# --------------------------------
# OTHER MODULES
# --------------------------------

elif page == "Medications":

    st.subheader("Medication Management")
    st.info("Medication management will be implemented in the next step.")

elif page == "Clinical Records":

    st.subheader("Clinical Records")
    st.info("Clinical record management will be implemented in the next step.")

elif page == "Medical Documents":

    st.subheader("Medical Documents")
    st.info("Medical document management will be implemented in the next step.")

