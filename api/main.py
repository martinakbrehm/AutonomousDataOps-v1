from fastapi import FastAPI, UploadFile, File, Form, Header
from fastapi.responses import JSONResponse
from api.schemas import RunRequest
from pipelines.etl_pipeline import run_pipeline_from_file
import shutil
import os
from utils.logging_config import configure_logging, logger
from utils.observability import init_observability
from tools.security import verify_api_key, save_upload_file
from memory.sql_memory import SQLMemory


# SQL memory for logging auth events
sql_mem = SQLMemory()


configure_logging()
app = FastAPI(title="Autonomous DataOps MAS")
init_observability(app)


@app.post("/run")
async def run_pipeline(
    file: UploadFile = File(...),
    clean: bool = Form(True),
    analyze: bool = Form(True),
    transform: bool = Form(False),
    x_api_key: str | None = Header(None, convert_underscores=False),
):
    # authenticate (logs failures/rate-limits to SQL memory)
    verify_api_key(x_api_key, sql_memory=sql_mem)

    # save uploaded file to a temp location with validation (size + extension)
    os.makedirs(".uploads", exist_ok=True)
    path = os.path.join('.uploads', file.filename)
    save_upload_file(file, path, allowed_exts=['.csv', '.xls', '.xlsx'], max_size=int(os.getenv('MAX_UPLOAD_BYTES', 10 * 1024 * 1024)))

    request = {"clean": clean, "analyze": analyze, "transform": transform}
    try:
        df, summary = run_pipeline_from_file(path, request)
        return JSONResponse({"status": "ok", "summary": summary})
    except Exception as e:
        logger.exception("Pipeline failed")
        return JSONResponse({"status": "error", "detail": str(e)}, status_code=500)


@app.get("/health")
def health():
    return {"status": "ok"}
