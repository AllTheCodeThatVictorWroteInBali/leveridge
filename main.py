from contextlib import asynccontextmanager
from importlib import import_module
import logging
from pathlib import Path
from shutil import copyfileobj
from tempfile import TemporaryDirectory
from time import perf_counter

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse

from db.pdf import PdfStore


logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    started = perf_counter()
    logger.info("Loading PaddleOCR on CPU. Missing models will download; first startup may take several minutes.")
    try:
        app.state.read_pdf = import_module("model.paddle").read_pdf
    except Exception:
        logger.exception("PaddleOCR initialization failed; server startup aborted.")
        raise
    logger.info("PaddleOCR ready in %.1f seconds. PDF uploads can now be processed.", perf_counter() - started)
    yield


app = FastAPI(title="FastAPI Demo", lifespan=lifespan)
INDEX_FILE = Path(__file__).with_name("index.html")


@app.get("/index.html", response_class=FileResponse)
def index():
    return FileResponse(INDEX_FILE)


@app.post("/read")
def read(file: UploadFile):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        print(f"Invalid file upload attempt: {file.filename}")
        raise HTTPException(status_code=415, detail="Please upload a PDF file.")
    print(f"Received valid file upload: {file.filename}")

    with TemporaryDirectory(prefix="pdf-ocr-") as directory:
        pdf_path = Path(directory) / "upload.pdf"
        with pdf_path.open("wb") as destination:
            copyfileobj(file.file, destination)
        extracted_data = app.state.read_pdf(str(pdf_path))
        PdfStore().save_pdf(extracted_data)
        return extracted_data