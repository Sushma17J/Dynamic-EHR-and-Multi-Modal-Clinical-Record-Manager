
import os
import uuid
import secrets
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.security import APIKeyHeader
from motor.motor_asyncio import AsyncIOMotorClient

# API KEY SECURITY
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    raise RuntimeError("API_KEY is missing. Set your API key first.")

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False
)


async def verify_api_key(api_key: str = Depends(api_key_header)):
    if not api_key or not secrets.compare_digest(api_key, API_KEY):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )


# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL")

if not MONGO_URL:
    raise RuntimeError("MONGO_URL is missing. Run your MongoDB connection cell first.")

client = AsyncIOMotorClient(MONGO_URL)
db = client["healthcare_ehr"]

patients = db["patients"]
clinical_records = db["clinical_records"]
medical_documents = db["medical_documents"]

# FastAPI application
app = FastAPI(
    title="Healthcare EHR API",
    description="Dynamic Electronic Health Record Management System",
    version="1.0",
    dependencies=[Depends(verify_api_key)]
)

# Local document storage
UPLOAD_DIR = Path("/content/ehr_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def serialize(document):
    """Convert MongoDB ObjectId into a string."""
    if document and "_id" in document:
        document["_id"] = str(document["_id"])
    return document


@app.get("/")
async def home():
    return {"message": "Healthcare EHR API is running!"}


@app.get("/health")
async def health_check():
    await client.admin.command("ping")
    return {"status": "connected", "database": "healthcare_ehr"}


# 1. Patient APIs

@app.post("/patients/register")
async def register_patient(patient: dict):
    if not patient.get("patient_id") or not patient.get("name"):
        raise HTTPException(
            status_code=400,
            detail="patient_id and name are required"
        )

    existing = await patients.find_one(
        {"patient_id": patient["patient_id"]}
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Patient ID already exists"
        )

    patient["created_at"] = datetime.now(timezone.utc)

    result = await patients.insert_one(patient)

    return {
        "message": "Patient registered successfully",
        "id": str(result.inserted_id)
    }


@app.get("/patients")
async def get_patients():
    result = await patients.find(
        {},
        {"_id": 0}
    ).to_list(length=1000)

    return result


@app.get("/patients/{patient_id}")
async def get_patient(patient_id: str):
    patient = await patients.find_one(
        {"patient_id": patient_id},
        {"_id": 0}
    )

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return patient


# 2. Vital APIs

@app.post("/vitals/{patient_id}")
async def add_vitals(patient_id: str, vital: dict):
    patient = await patients.find_one(
        {"patient_id": patient_id}
    )

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    required = ["heart_rate", "temperature", "spo2", "blood_pressure"]

    if not all(field in vital for field in required):
        raise HTTPException(
            status_code=400,
            detail="All vital fields are required"
        )

    vital["recorded_at"] = datetime.now(timezone.utc)

    await patients.update_one(
        {"patient_id": patient_id},
        {"$push": {"vitals": vital}}
    )

    return {"message": "Vital reading added successfully"}


@app.get("/vitals/history/{patient_id}")
async def get_vital_history(patient_id: str):
    pipeline = [
        {"$match": {"patient_id": patient_id}},
        {"$unwind": "$vitals"},
        {
            "$project": {
                "_id": 0,
                "patient_id": 1,
                "recorded_at": "$vitals.recorded_at",
                "heart_rate": "$vitals.heart_rate",
                "temperature": "$vitals.temperature",
                "spo2": "$vitals.spo2",
                "systolic": "$vitals.blood_pressure.systolic",
                "diastolic": "$vitals.blood_pressure.diastolic"
            }
        },
        {"$sort": {"recorded_at": 1}}
    ]

    result = await patients.aggregate(pipeline).to_list(length=1000)

    return result


# 3. Medication APIs

@app.post("/medications/{patient_id}")
async def add_medication(patient_id: str, medication: dict):
    patient = await patients.find_one(
        {"patient_id": patient_id}
    )

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    medication["added_at"] = datetime.now(timezone.utc)

    await patients.update_one(
        {"patient_id": patient_id},
        {"$push": {"medications": medication}}
    )

    return {"message": "Medication added successfully"}


@app.get("/medications/{patient_id}")
async def get_medications(patient_id: str):
    patient = await patients.find_one(
        {"patient_id": patient_id},
        {"_id": 0, "medications": 1}
    )

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    return patient.get("medications", [])


# 4. Clinical record APIs

@app.post("/records/{patient_id}")
async def add_clinical_record(patient_id: str, record: dict):
    patient = await patients.find_one(
        {"patient_id": patient_id}
    )

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    record["patient_id"] = patient_id
    record["created_at"] = datetime.now(timezone.utc)

    result = await clinical_records.insert_one(record)

    return {
        "message": "Clinical record added successfully",
        "id": str(result.inserted_id)
    }


@app.get("/records/{patient_id}")
async def get_clinical_records(patient_id: str):
    result = await clinical_records.find(
        {"patient_id": patient_id},
        {"_id": 0}
    ).to_list(length=1000)

    return result


# 5. Medical document upload API

@app.post("/documents/upload/{patient_id}")
async def upload_document(
    patient_id: str,
    file: UploadFile = File(...)
):
    patient = await patients.find_one(
        {"patient_id": patient_id}
    )

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    allowed_types = [
        "application/pdf",
        "image/jpeg",
        "image/png"
    ]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, JPEG and PNG files are allowed"
        )

    content = await file.read()

    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size must be 5 MB or less"
        )

    extension = Path(file.filename or "").suffix.lower()

    if extension not in [".pdf", ".jpg", ".jpeg", ".png"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid file extension"
        )

    document_id = str(uuid.uuid4())
    saved_filename = document_id + extension
    file_path = UPLOAD_DIR / saved_filename

    with open(file_path, "wb") as output:
        output.write(content)

    document = {
        "document_id": document_id,
        "patient_id": patient_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "file_path": str(file_path),
        "uploaded_at": datetime.now(timezone.utc)
    }

    await medical_documents.insert_one(document)

    return {
        "message": "Document uploaded successfully",
        "document_id": document_id
    }


@app.get("/documents/{patient_id}")
async def get_documents(patient_id: str):
    result = await medical_documents.find(
        {"patient_id": patient_id},
        {"_id": 0}
    ).to_list(length=1000)

    return result


# 6. Dashboard statistics

@app.get("/dashboard/stats")
async def dashboard_stats():
    total_patients = await patients.count_documents({})
    total_records = await clinical_records.count_documents({})
    total_documents = await medical_documents.count_documents({})

    return {
        "total_patients": total_patients,
        "total_clinical_records": total_records,
        "total_medical_documents": total_documents
    }
