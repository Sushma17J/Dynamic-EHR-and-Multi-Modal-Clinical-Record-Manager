import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import date

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="MediTrack | Healthcare Management",
    page_icon="🏥",
    layout="wide"
)

API_URL = st.secrets["API_URL"].rstrip("/")
API_KEY = st.secrets["API_KEY"]

HEADERS = {"X-API-Key": API_KEY}

# --------------------------------------------------
# CUSTOM DESIGN
# --------------------------------------------------

st.markdown("""
<style>
.stApp {
    background-color: #0B1120;
    color: #E5E7EB;
}
[data-testid="stSidebar"] {
    background-color: #111B2E;
}
[data-testid="stSidebar"] * {
    color: #E5E7EB;
}
h1, h2, h3 {
    color: #F8FAFC;
}
.metric-card {
    background: #17243A;
    padding: 22px;
    border-radius: 14px;
    border: 1px solid #263750;
}
.metric-label {
    color: #94A3B8;
    font-size: 14px;
}
.metric-value {
    color: #2DD4BF;
    font-size: 30px;
    font-weight: bold;
}
.section-card {
    background: #17243A;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #263750;
    margin-bottom: 12px;
}
.stButton > button {
    background-color: #0D9488;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
}
.stButton > button:hover {
    background-color: #0F766E;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# API FUNCTIONS
# --------------------------------------------------

def api_get(endpoint):
    try:
        response = requests.get(
            f"{API_URL}{endpoint}",
            headers=HEADERS,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return None


def api_post(endpoint, data):
    try:
        response = requests.post(
            f"{API_URL}{endpoint}",
            headers=HEADERS,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        if getattr(e, "response", None) is not None:
            st.error(e.response.text)
        return None


def get_patient_list():
    result = api_get("/patients")

    if result is None:
        return []

    if isinstance(result, dict):
        result = result.get("patients", [])

    return result if isinstance(result, list) else []


def patient_options():
    patients = get_patient_list()
    options = {}

    for patient in patients:
        patient_id = patient.get("patient_id")
        if patient_id:
            name = patient.get("name", "Unknown")
            options[f"{patient_id} - {name}"] = patient_id

    return options


def show_records(data):
    if data is None:
        return

    if isinstance(data, dict):
        data = data.get("records", data.get("medications",
                    data.get("documents", [])))

    if not data:
        st.info("No records found.")
        return

    df = pd.DataFrame(data)

    for column in ["_id", "file_path"]:
        if column in df.columns:
            df = df.drop(columns=[column])

    st.dataframe(df, use_container_width=True, hide_index=True)


# --------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------

st.sidebar.markdown("# 🏥 MediTrack")
st.sidebar.caption("Healthcare Management Platform")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Patients",
        "Vital Signs",
        "Medication Management",
        "Clinical Records",
        "Medical Documents"
    ]
)

st.sidebar.divider()
st.sidebar.caption("Centralized Electronic Health Records")


# ==================================================
# DASHBOARD
# ==================================================

if page == "Dashboard":

    st.title("Healthcare Management")
    st.caption("Centralized Electronic Health Record Management Platform")

    stats = api_get("/dashboard/stats")

    if stats:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Patients</div>
                <div class="metric-value">{stats.get('total_patients', 0)}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Clinical Records</div>
                <div class="metric-value">{stats.get('total_clinical_records', 0)}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Medical Documents</div>
                <div class="metric-value">{stats.get('total_medical_documents', 0)}</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    st.subheader("Patient Overview")

    patients = get_patient_list()
    show_records(patients)


# ==================================================
# PATIENTS
# ==================================================

elif page == "Patients":

    st.title("Patient Management")
    st.caption("View registered patient information")

    patients = get_patient_list()
    show_records(patients)

    if patients:
        df = pd.DataFrame(patients)
        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Patient Data (CSV)",
            csv,
            "patient_data.csv",
            "text/csv"
        )


# ==================================================
# VITAL SIGNS
# ==================================================

elif page == "Vital Signs":

    st.title("Vital Signs Monitoring")
    st.caption("Record and monitor patient vital measurements")

    options = patient_options()

    if not options:
        st.warning("No patients available. Register a patient first.")
    else:
        selected = st.selectbox("Select Patient", list(options.keys()))
        patient_id = options[selected]

        st.subheader("Add Vital Signs")

        with st.form("vitals_form"):

            col1, col2 = st.columns(2)

            with col1:
                heart_rate = st.number_input(
                    "Heart Rate (bpm)", 1, 300, 72
                )
                temperature = st.number_input(
                    "Temperature (°C)", 25.0, 45.0, 37.0, 0.1
                )
                spo2 = st.number_input(
                    "SpO2 (%)", 1, 100, 98
                )

            with col2:
                systolic = st.number_input(
                    "Systolic BP", 1, 300, 120
                )
                diastolic = st.number_input(
                    "Diastolic BP", 1, 200, 80
                )

            submitted = st.form_submit_button("Save Vital Signs")

            if submitted:
                if systolic <= diastolic:
                    st.error("Systolic pressure must be greater than diastolic pressure.")
                else:
                    payload = {
                        "heart_rate": heart_rate,
                        "temperature": temperature,
                        "spo2": spo2,
                        "blood_pressure": {
                            "systolic": systolic,
                            "diastolic": diastolic
                        }
                    }

                    result = api_post(
                        f"/vitals/{patient_id}",
                        payload
                    )

                    if result is not None:
                        st.success("Vital signs saved successfully!")
                        st.rerun()

        st.divider()
        st.subheader("Vital Signs History")

        history = api_get(f"/vitals/history/{patient_id}")

        if history:
            df = pd.DataFrame(history)
            st.dataframe(df, use_container_width=True, hide_index=True)

            if "heart_rate" in df.columns:
                st.subheader("Heart Rate Trend")
                st.plotly_chart(
                    px.line(
                        df,
                        y="heart_rate",
                        title="Heart Rate History",
                        markers=True
                    ),
                    use_container_width=True
                )


# ==================================================
# MEDICATION MANAGEMENT
# ==================================================

elif page == "Medication Management":

    st.title("Medication Management")
    st.caption("Add and view patient medication information")

    options = patient_options()

    if not options:
        st.warning("No patients available. Register a patient first.")
    else:
        selected = st.selectbox(
            "Select Patient",
            list(options.keys()),
            key="med_patient"
        )
        patient_id = options[selected]

        st.subheader("Add Medication")

        with st.form("medication_form"):

            medication_name = st.text_input("Medication Name")
            dosage = st.text_input("Dosage", placeholder="Example: 500 mg")
            frequency = st.text_input(
                "Frequency",
                placeholder="Example: Twice daily"
            )

            col1, col2 = st.columns(2)

            with col1:
                start_date = st.date_input(
                    "Start Date",
                    value=date.today()
                )

            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=date.today()
                )

            status = st.selectbox(
                "Medication Status",
                ["Active", "Completed", "Discontinued"]
            )

            submitted = st.form_submit_button("Save Medication")

            if submitted:
                if not medication_name.strip() or not dosage.strip() or not frequency.strip():
                    st.error("Please fill in the medication name, dosage, and frequency.")
                elif end_date < start_date:
                    st.error("End date cannot be earlier than start date.")
                else:
                    payload = {
                        "medication_name": medication_name.strip(),
                        "dosage": dosage.strip(),
                        "frequency": frequency.strip(),
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "status": status
                    }

                    result = api_post(
                        f"/medications/{patient_id}",
                        payload
                    )

                    if result is not None:
                        st.success("Medication added successfully!")
                        st.rerun()

        st.divider()
        st.subheader("Medication History")

        medications = api_get(f"/medications/{patient_id}")
        show_records(medications)


# ==================================================
# CLINICAL RECORDS
# ==================================================

elif page == "Clinical Records":

    st.title("Clinical Records")
    st.caption("Maintain patient diagnoses, symptoms, and treatment notes")

    options = patient_options()

    if not options:
        st.warning("No patients available. Register a patient first.")
    else:
        selected = st.selectbox(
            "Select Patient",
            list(options.keys()),
            key="clinical_patient"
        )
        patient_id = options[selected]

        st.subheader("Add Clinical Record")

        with st.form("clinical_form"):

            record_date = st.date_input(
                "Record Date",
                value=date.today()
            )

            doctor_name = st.text_input("Doctor / Clinician Name")
            record_type = st.selectbox(
                "Record Type",
                [
                    "Consultation",
                    "Diagnosis",
                    "Follow-up",
                    "Treatment",
                    "Other"
                ]
            )

            diagnosis = st.text_input("Diagnosis")
            symptoms = st.text_area("Symptoms")
            treatment = st.text_area("Treatment / Advice")
            notes = st.text_area("Additional Clinical Notes")

            submitted = st.form_submit_button("Save Clinical Record")

            if submitted:
                if not diagnosis.strip() and not symptoms.strip() and not notes.strip():
                    st.error("Enter at least a diagnosis, symptoms, or clinical notes.")
                else:
                    payload = {
                        "record_date": record_date.isoformat(),
                        "doctor_name": doctor_name.strip(),
                        "record_type": record_type,
                        "diagnosis": diagnosis.strip(),
                        "symptoms": symptoms.strip(),
                        "treatment": treatment.strip(),
                        "notes": notes.strip()
                    }

                    result = api_post(
                        f"/records/{patient_id}",
                        payload
                    )

                    if result is not None:
                        st.success("Clinical record saved successfully!")
                        st.rerun()

        st.divider()
        st.subheader("Clinical History")

        records = api_get(f"/records/{patient_id}")
        show_records(records)


# ==================================================
# MEDICAL DOCUMENTS
# ==================================================

elif page == "Medical Documents":

    st.title("Medical Documents")
    st.caption("Upload and manage patient medical document information")

    options = patient_options()

    if not options:
        st.warning("No patients available. Register a patient first.")
    else:
        selected = st.selectbox(
            "Select Patient",
            list(options.keys()),
            key="document_patient"
        )
        patient_id = options[selected]

        st.subheader("Upload Medical Document")

        uploaded_file = st.file_uploader(
            "Choose a PDF, JPG, or PNG file",
            type=["pdf", "jpg", "jpeg", "png"]
        )

        if uploaded_file:
            st.write("Selected file:", uploaded_file.name)
            st.write(
                f"File size: {uploaded_file.size / (1024 * 1024):.2f} MB"
            )

            if uploaded_file.size > 5 * 1024 * 1024:
                st.error("File size must not exceed 5 MB.")
            elif st.button("Upload Document"):
                try:
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type
                        )
                    }

                    response = requests.post(
                        f"{API_URL}/documents/upload/{patient_id}",
                        headers=HEADERS,
                        files=files,
                        timeout=60
                    )

                    response.raise_for_status()
                    st.success("Medical document uploaded successfully!")
                    st.rerun()

                except requests.exceptions.RequestException as e:
                    st.error(f"Upload failed: {e}")
                    if getattr(e, "response", None) is not None:
                        st.error(e.response.text)

        st.divider()
        st.subheader("Uploaded Documents")

        documents = api_get(f"/documents/{patient_id}")
        show_records(documents)

