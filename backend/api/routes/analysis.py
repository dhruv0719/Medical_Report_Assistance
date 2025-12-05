# backend/api/routes/analysis.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from backend.orchestrator.pipeline import MedicalReportPipeline
from backend.api.routes.users import fastapi_users
from backend.api.auth.models import User
import tempfile
from pathlib import Path
import uuid

router = APIRouter()

# Define the user dependency for protected routes
current_active_user = fastapi_users.current_user(active=True)

@router.post("/analyze-report", response_model=dict, status_code=202)
async def analyze_report_endpoint(
    file: UploadFile = File(...),
    user: User = Depends(current_active_user)
):
    """
    Accepts a medical report (PDF/TXT), processes it, and returns the analysis.
    This is a protected endpoint and requires authentication.
    """
    # NOTE: For a real production app, you would use background tasks (Celery).
    # For simplicity in this step, we'll process it synchronously.
    
    # Securely handle the file upload in a temporary directory
    try:
        # Use a unique name to avoid conflicts
        suffix = Path(file.filename).suffix
        temp_file_path = Path(tempfile.gettempdir()) / f"{uuid.uuid4()}{suffix}"

        with open(temp_file_path, "wb") as buffer:
            buffer.write(await file.read())

        # Initialize and run the pipeline
        pipeline = MedicalReportPipeline(enable_llm=True, enable_audit=True)
        # Pass user_id to the pipeline for logging
        pipeline.audit_logger.user_id = user.id
        
        result = pipeline.process_file(temp_file_path)
        
        return result.to_dict()

    except Exception as e:
        # Proper logging should be done here
        raise HTTPException(status_code=500, detail=f"An error occurred during analysis: {str(e)}")
    finally:
        # Clean up the temporary file
        if 'temp_file_path' in locals() and temp_file_path.exists():
            temp_file_path.unlink()