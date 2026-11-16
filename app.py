
import streamlit as st
import requests
import pandas as pd
import plotly.express as px

from datetime import date


# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="MediTrack | Healthcare Management",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = st.secrets["API_URL"].rstrip("/")
API_KEY = st.secrets["API_KEY"]

HEADERS = {
    "X-API-Key": API_KEY
}


# ============================================================
# 2. CUSTOM CSS
# ============================================================

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
    padding: 20px;
    border-radius: 14px;
    border: 1px solid #263750;
}

.metric-label {
    color: #94A3B8;
    font-size: 14px;
}

.metric-value {
    color: #2DD4BF;
    font-size: 28px;
    font-weight: bold;
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

div[data-testid="stMetric"] {
    background: #17243A;
    border: 1px solid #263750;
    padding: 14px;
    border-radius: 12px;
}

div[data-testid="stMetricLabel"] {
    color: #94A3B8;
}

hr {
    border-color: #263750;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# 3. API FUNCTIONS
# ============================================================

def api_get(endpoint):

    try:
        response = requests.get(
            f"{API_URL}{endpoint}",
            headers=HEADERS,
            timeout=30
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as error:

        st.error(f"API Error: {error}")

        if getattr(error, "response", None) is not None:
            st.error(error.response.text)

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

    except requests.exceptions.RequestException as error:

        st.error(f"API Error: {error}")

        if getattr(error, "response", None) is not None:
            st.error(error.response.text)

        return None


def get_patient_list():

    result = api_get("/patients")

    if result is None:
        return []

    if isinstance(result, dict):
        result = result.get("patients", [])

    return result if isinstance(result, list) else []


def get_patient_options():

    patients = get_patient_list()

    options = {}

    for patient in patients:

        patient_id = patient.get("patient_id")

        if patient_id:

            name = patient.get("name", "Unknown")

            options[f"{patient_id} - {name}"] = patient_id

    return options


def display_table(data):

    if data is None:
        return

    if isinstance(data, dict):
        data = data.get("records", [])

    if not isinstance(data, list) or not data:
        st.info("No records available.")
        return

    df = pd.DataFrame(data)

    for column in ["_id", "file_path"]:
        if column in df.columns:
            df = df.drop(columns=[column])

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 4. SIDEBAR NAVIGATION
# ============================================================

st.sidebar.markdown("# 🏥 MediTrack")

st.sidebar.caption(
    "Centralized Healthcare Management Platform"
)

st.sidebar.divider()

page = st.sidebar.radio(
    "MAIN MENU",
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

st.sidebar.caption("Electronic Health Record System")


# ============================================================
# 5. DASHBOARD - PATIENT CENTRIC
# ============================================================

if page == "Dashboard":

    st.title("Healthcare Management")

    st.caption(
        "Patient-Centric Electronic Health Record Dashboard"
    )

    patient_options = get_patient_options()

    if not patient_options:

        st.warning(
            "No patients registered. Go to Patients and register a new patient."
        )

        if st.button("Register New Patient"):

            st.session_state["selected_page"] = "Patients"
            st.rerun()

    else:

        # Patient selection

        st.subheader("Select Patient")

        selected_patient = st.selectbox(
            "Patient ID",
            list(patient_options.keys()),
            key="dashboard_patient"
        )

        patient_id = patient_options[selected_patient]

        st.divider()

        # Fetch patient information

        patient = api_get(
            f"/patients/{patient_id}"
        )

        vitals = api_get(
            f"/vitals/history/{patient_id}"
        )

        medications = api_get(
            f"/medications/{patient_id}"
        )

        records = api_get(
            f"/records/{patient_id}"
        )

        documents = api_get(
            f"/documents/{patient_id}"
        )

        if patient is not None:

            # ------------------------------------------------
            # PATIENT PROFILE
            # ------------------------------------------------

            st.subheader("👤 Patient Profile")

            col1, col2, col3 = st.columns(3)

            with col1:

                st.markdown("**Patient ID**")

                st.write(
                    patient.get("patient_id", "-")
                )

                st.markdown("**Full Name**")

                st.write(
                    patient.get("name", "-")
                )

            with col2:

                st.markdown("**Age**")

                st.write(
                    patient.get("age", "-")
                )

                st.markdown("**Gender**")

                st.write(
                    patient.get("gender", "-")
                )

            with col3:

                st.markdown("**Phone Number**")

                st.write(
                    patient.get("phone", "-")
                )

                st.markdown("**Email**")

                st.write(
                    patient.get("email", "-")
                )

            # Medical history

            medical_history = patient.get(
                "medical_history", {}
            )

            if isinstance(medical_history, dict):

                col1, col2 = st.columns(2)

                with col1:

                    st.markdown("**Allergies**")

                    allergies = medical_history.get(
                        "allergies", []
                    )

                    st.write(
                        ", ".join(allergies)
                        if allergies else "None recorded"
                    )

                with col2:

                    st.markdown("**Medical Conditions**")

                    conditions = medical_history.get(
                        "conditions", []
                    )

                    st.write(
                        ", ".join(conditions)
                        if conditions else "None recorded"
                    )

            st.divider()

            # ------------------------------------------------
            # HEALTHCARE SUMMARY
            # ------------------------------------------------

            st.subheader("Healthcare Overview")

            vital_count = (
                len(vitals)
                if isinstance(vitals, list) else 0
            )

            medication_count = (
                len(medications)
                if isinstance(medications, list) else 0
            )

            record_count = (
                len(records)
                if isinstance(records, list) else 0
            )

            document_count = (
                len(documents)
                if isinstance(documents, list) else 0
            )

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Vital Readings",
                    vital_count
                )

            with col2:
                st.metric(
                    "Medications",
                    medication_count
                )

            with col3:
                st.metric(
                    "Clinical Records",
                    record_count
                )

            with col4:
                st.metric(
                    "Medical Documents",
                    document_count
                )

            st.divider()

            # ------------------------------------------------
            # VITAL SIGNS OVERVIEW
            # ------------------------------------------------

            st.subheader("❤️ Vital Signs Overview")

            if isinstance(vitals, list) and vitals:

                latest = max(
                    vitals,
                    key=lambda item: str(
                        item.get("recorded_at", "")
                    )
                )

                col1, col2, col3, col4 = st.columns(4)

                with col1:

                    st.metric(
                        "Heart Rate",
                        f"{latest.get('heart_rate', '-')} bpm"
                    )

                with col2:

                    st.metric(
                        "Temperature",
                        f"{latest.get('temperature', '-')} °C"
                    )

                with col3:

                    st.metric(
                        "SpO2",
                        f"{latest.get('spo2', '-')}%"
                    )

                with col4:

                    blood_pressure = (
                        f"{latest.get('systolic', '-')}/"
                        f"{latest.get('diastolic', '-')}"
                    )

                    st.metric(
                        "Blood Pressure",
                        blood_pressure
                    )

                vital_df = pd.DataFrame(vitals)

                if "heart_rate" in vital_df.columns:

                    st.plotly_chart(
                        px.line(
                            vital_df,
                            x="recorded_at",
                            y="heart_rate",
                            markers=True,
                            title="Heart Rate Trend"
                        ),
                        use_container_width=True
                    )

                if "temperature" in vital_df.columns:

                    st.plotly_chart(
                        px.line(
                            vital_df,
                            x="recorded_at",
                            y="temperature",
                            markers=True,
                            title="Temperature Trend"
                        ),
                        use_container_width=True
                    )

                with st.expander("View Complete Vital History"):

                    st.dataframe(
                        vital_df,
                        use_container_width=True,
                        hide_index=True
                    )

            else:

                st.info(
                    "No vital readings recorded for this patient."
                )

            st.divider()

            # ------------------------------------------------
            # MEDICATION OVERVIEW
            # ------------------------------------------------

            st.subheader("💊 Medication Overview")

            if isinstance(medications, list) and medications:

                medication_df = pd.DataFrame(medications)

                st.dataframe(
                    medication_df,
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.info(
                    "No medication records available."
                )

            st.divider()

            # ------------------------------------------------
            # CLINICAL RECORD OVERVIEW
            # ------------------------------------------------

            st.subheader("🩺 Clinical Records Overview")

            if isinstance(records, list) and records:

                records_df = pd.DataFrame(records)

                st.dataframe(
                    records_df,
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.info(
                    "No clinical records available."
                )

            st.divider()

            # ------------------------------------------------
            # MEDICAL DOCUMENT OVERVIEW
            # ------------------------------------------------

            st.subheader("📁 Medical Documents Overview")

            if isinstance(documents, list) and documents:

                documents_df = pd.DataFrame(documents)

                for column in ["_id", "file_path"]:
                    if column in documents_df.columns:
                        documents_df = documents_df.drop(
                            columns=[column]
                        )

                st.dataframe(
                    documents_df,
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.info(
                    "No medical documents uploaded."
                )


# ============================================================
# 6. PATIENT REGISTRATION AND DIRECTORY
# ============================================================

elif page == "Patients":

    st.title("Patient Management")

    st.caption(
        "Register new patients and view registered patient information"
    )

    tab1, tab2 = st.tabs(
        [
            "➕ Register New Patient",
            "📋 Patient Directory"
        ]
    )

    # --------------------------------------------------------
    # REGISTRATION
    # --------------------------------------------------------

    with tab1:

        st.subheader("New Patient Registration")

        with st.form("patient_registration_form"):

            col1, col2 = st.columns(2)

            with col1:

                patient_id = st.text_input(
                    "Patient ID *",
                    placeholder="Example: P021"
                )

                name = st.text_input(
                    "Full Name *",
                    placeholder="Enter full name"
                )

                age = st.number_input(
                    "Age",
                    min_value=0,
                    max_value=120,
                    value=22
                )

            with col2:

                gender = st.selectbox(
                    "Gender",
                    ["Select", "Male", "Female", "Other"]
                )

                phone = st.text_input(
                    "Phone Number"
                )

                email = st.text_input(
                    "Email Address"
                )

            st.divider()

            st.subheader("Medical History")

            allergies = st.text_input(
                "Allergies",
                placeholder="Separate multiple allergies with commas"
            )

            conditions = st.text_area(
                "Existing Medical Conditions",
                placeholder="Enter medical conditions"
            )

            submitted = st.form_submit_button(
                "Register Patient",
                use_container_width=True
            )

            if submitted:

                if not patient_id.strip():

                    st.error("Patient ID is required.")

                elif not name.strip():

                    st.error("Full name is required.")

                elif gender == "Select":

                    st.error("Please select gender.")

                else:

                    patient_data = {

                        "patient_id": patient_id.strip(),

                        "name": name.strip(),

                        "age": age,

                        "gender": gender,

                        "phone": phone.strip(),

                        "email": email.strip(),

                        "medical_history": {

                            "allergies": [
                                item.strip()
                                for item in allergies.split(",")
                                if item.strip()
                            ],

                            "conditions": [
                                item.strip()
                                for item in conditions.split(",")
                                if item.strip()
                            ]
                        },

                        "vitals": [],

                        "medications": []
                    }

                    result = api_post(
                        "/patients/register",
                        patient_data
                    )

                    if result is not None:

                        st.success(
                            f"Patient {patient_id} registered successfully!"
                        )

                        st.json(result)

    # --------------------------------------------------------
    # PATIENT DIRECTORY
    # --------------------------------------------------------

    with tab2:

        st.subheader("Registered Patients")

        if st.button("🔄 Refresh Patient List"):

            st.rerun()

        patients = get_patient_list()

        if patients:

            df = pd.DataFrame(patients)

            if "_id" in df.columns:
                df = df.drop(columns=["_id"])

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            csv = pd.DataFrame(patients).to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                "Download Patient Data (CSV)",
                csv,
                "patient_data.csv",
                "text/csv"
            )

        else:

            st.info("No patients registered yet.")


# ============================================================
# 7. VITAL SIGNS
# ============================================================

elif page == "Vital Signs":

    st.title("Vital Signs Monitoring")

    st.caption(
        "Record and monitor patient vital measurements"
    )

    options = get_patient_options()

    if not options:

        st.warning("Register a patient first.")

    else:

        selected = st.selectbox(
            "Select Patient",
            list(options.keys()),
            key="vitals_patient"
        )

        patient_id = options[selected]

        st.subheader("Add Vital Signs")

        with st.form("vitals_form"):

            col1, col2 = st.columns(2)

            with col1:

                heart_rate = st.number_input(
                    "Heart Rate (bpm)",
                    1, 300, 72
                )

                temperature = st.number_input(
                    "Temperature (°C)",
                    25.0, 45.0, 37.0, 0.1
                )

                spo2 = st.number_input(
                    "SpO2 (%)",
                    1, 100, 98
                )

            with col2:

                systolic = st.number_input(
                    "Systolic BP",
                    1, 300, 120
                )

                diastolic = st.number_input(
                    "Diastolic BP",
                    1, 200, 80
                )

            submitted = st.form_submit_button(
                "Save Vital Signs"
            )

            if submitted:

                if systolic <= diastolic:

                    st.error(
                        "Systolic pressure must be greater than diastolic pressure."
                    )

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

                        st.success(
                            "Vital signs saved successfully!"
                        )

                        st.rerun()

        st.divider()

        st.subheader("Vital Signs History")

        history = api_get(
            f"/vitals/history/{patient_id}"
        )

        if isinstance(history, list) and history:

            vital_df = pd.DataFrame(history)

            st.dataframe(
                vital_df,
                use_container_width=True,
                hide_index=True
            )

            if "heart_rate" in vital_df.columns:

                st.plotly_chart(
                    px.line(
                        vital_df,
                        x="recorded_at",
                        y="heart_rate",
                        title="Heart Rate History",
                        markers=True
                    ),
                    use_container_width=True
                )

        else:

            st.info("No vital history available.")


# ============================================================
# 8. MEDICATION MANAGEMENT
# ============================================================

elif page == "Medication Management":

    st.title("Medication Management")

    st.caption(
        "Add and view patient medication information"
    )

    options = get_patient_options()

    if not options:

        st.warning("Register a patient first.")

    else:

        selected = st.selectbox(
            "Select Patient",
            list(options.keys()),
            key="med_patient"
        )

        patient_id = options[selected]

        st.subheader("Add Medication")

        with st.form("medication_form"):

            medication_name = st.text_input(
                "Medication Name"
            )

            dosage = st.text_input(
                "Dosage",
                placeholder="Example: 500 mg"
            )

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

            submitted = st.form_submit_button(
                "Save Medication"
            )

            if submitted:

                if (
                    not medication_name.strip()
                    or not dosage.strip()
                    or not frequency.strip()
                ):

                    st.error(
                        "Please complete all medication details."
                    )

                elif end_date < start_date:

                    st.error(
                        "End date cannot be earlier than start date."
                    )

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

                        st.success(
                            "Medication added successfully!"
                        )

                        st.rerun()

        st.divider()

        st.subheader("Medication History")

        medications = api_get(
            f"/medications/{patient_id}"
        )

        display_table(medications)


# ============================================================
# 9. CLINICAL RECORDS
# ============================================================

elif page == "Clinical Records":

    st.title("Clinical Records")

    st.caption(
        "Maintain patient diagnoses, symptoms, and treatment notes"
    )

    options = get_patient_options()

    if not options:

        st.warning("Register a patient first.")

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

            doctor_name = st.text_input(
                "Doctor / Clinician Name"
            )

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

            diagnosis = st.text_input(
                "Diagnosis"
            )

            symptoms = st.text_area(
                "Symptoms"
            )

            treatment = st.text_area(
                "Treatment / Advice"
            )

            notes = st.text_area(
                "Additional Clinical Notes"
            )

            submitted = st.form_submit_button(
                "Save Clinical Record"
            )

            if submitted:

                if (
                    not diagnosis.strip()
                    and not symptoms.strip()
                    and not notes.strip()
                ):

                    st.error(
                        "Enter a diagnosis, symptoms, or clinical notes."
                    )

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

                        st.success(
                            "Clinical record saved successfully!"
                        )

                        st.rerun()

        st.divider()

        st.subheader("Clinical History")

        records = api_get(
            f"/records/{patient_id}"
        )

        display_table(records)


# ============================================================
# 10. MEDICAL DOCUMENTS
# ============================================================

elif page == "Medical Documents":

    st.title("Medical Documents")

    st.caption(
        "Upload and manage patient medical documents"
    )

    options = get_patient_options()

    if not options:

        st.warning("Register a patient first.")

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

            st.write(
                "Selected file:",
                uploaded_file.name
            )

            file_size = uploaded_file.size / (1024 * 1024)

            st.write(
                f"File size: {file_size:.2f} MB"
            )

            if uploaded_file.size > 5 * 1024 * 1024:

                st.error(
                    "File size must not exceed 5 MB."
                )

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

                    st.success(
                        "Medical document uploaded successfully!"
                    )

                    st.rerun()

                except requests.exceptions.RequestException as error:

                    st.error(
                        f"Document upload failed: {error}"
                    )

                    if getattr(error, "response", None) is not None:

                        st.error(error.response.text)

        st.divider()

        st.subheader("Uploaded Documents")

        documents = api_get(
            f"/documents/{patient_id}"
        )

        display_table(documents)


# ============================================================
# END OF APPLICATION
# ============================================================
