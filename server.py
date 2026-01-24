import os
import hashlib
import json
import logging
from typing import Annotated

# Third-party imports
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from pydantic import ValidationError
import uvicorn

# Local imports
# We assume schemas.py is in the same directory and contains ToolMetadata
try:
    from schemas import ToolMetadata
except ImportError:
    # Fallback if running in an environment where imports are tricky, 
    # but in this setup it should work fine.
    # If schemas.py was missing, we would define ToolMetadata here.
    # Re-raising to ensure we fail fast if environment is wrong.
    raise

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("VA_Tool_Server")

app = FastAPI(title="VA Tool Publishing Server")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/uploadTool")
async def create_va(
    metadata: Annotated[str, Form(description="Stringified JSON metadata matching ToolMetadata schema")],
    content_hash: Annotated[str, Form(description="SHA256 hash of the zip file")],
    tool_zip: Annotated[UploadFile, File(description="The tool package zip file")],
):
    """
    Endpoint to receive, validate, and store a tool package.
    """
    logger.info(f"Received upload request for file: {tool_zip.filename}")

    # 1. Validate Metadata
    try:
        metadata_dict = json.loads(metadata)
        # Validate against the Pydantic schema from schemas.py
        validated_metadata = ToolMetadata(**metadata_dict)
        logger.info(f"Metadata valid for tool: {validated_metadata.name}")
    except json.JSONDecodeError:
        logger.error("Invalid JSON in metadata field")
        raise HTTPException(status_code=400, detail="Invalid JSON in metadata")
    except ValidationError as e:
        logger.error(f"Metadata schema validation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Schema validation failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error validation metadata: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Metadata validation error: {str(e)}")

    # 2. Read File and Compute Hash
    # We write to a temporary path first, or directly to final if we trust cleanup.
    # To be efficient, we compute hash while writing to disk to avoid storing large files in RAM.
    
    file_path = os.path.join(UPLOAD_DIR, tool_zip.filename or f"{validated_metadata.name}.zip")
    sha256_hash = hashlib.sha256()

    try:
        with open(file_path, "wb") as f:
            while chunk := await tool_zip.read(1024 * 1024):  # Read in 1MB chunks
                sha256_hash.update(chunk)
                f.write(chunk)
    except Exception as e:
        logger.error(f"Failed to write file to disk: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    computed_hash = sha256_hash.hexdigest()
    logger.info(f"Computed hash: {computed_hash}")

    # 3. Verify Hash
    if computed_hash != content_hash:
        logger.warning(f"Hash mismatch! Client sent: {content_hash}, Computed: {computed_hash}")
        # Delete the invalid file
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=400, 
            detail=f"Hash mismatch. Expected {content_hash}, got {computed_hash}"
        )

    logger.info(f"Hash verified successfully.")
    
    # 4. Success Response
    return {
        "status": "success",
        "message": "Tool package received and verified",
        "hash_verified": True,
        "tool_name": validated_metadata.name,
        "saved_as": tool_zip.filename
    }

if __name__ == "__main__":
    print(f"Starting server on https://browsez-platform-backend-production.up.railway.app")
    print(f"Uploads will be saved to: {os.path.abspath(UPLOAD_DIR)}")
    uvicorn.run(app, host="127.0.0.1", port=8000)
