from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import json
import os
import tempfile
import uuid

from app.pipeline import run_pipeline
from app.utils.serialization import make_json_safe

app = FastAPI(
    title="AnomAI ML Service",
    description="Schema-first data profiling, anomaly detection, scoring and remidiation service.",
    version="2.0.0"
)

ALLOWED_EXTENSIONS = {
    ".csv", ".tsv", ".txt", ".xlsx", ".xls", ".ods",
    ".json", ".jsonl", ".ndjson", ".xml", ".parquet"
}
MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
EXPORT_DIR = os.path.join(tempfile.gettempdir(), "anomai_exports")
os.makedirs(EXPORT_DIR, exist_ok=True)


@app.get("/")
def root():
    return {"message": "AnomAI ML Service is running", "version": "2.0.0", "status": "operational"}


@app.get("/health")
def health():
    return {"status": "healthy", "service": "AnomAI ML Service", "version": "2.0.0"}


def validate_uploaded_file(dataset):
    if not dataset.filename:
        raise HTTPException(status_code=400, detail="No file was provided.")
    extension = os.path.splitext(dataset.filename)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported format. Supported: CSV, TSV, TXT, XLSX, XLS, ODS, JSON, JSONL, NDJSON, XML and Parquet."
        )
    return extension


def export_cleaned_dataset(cleaned_data, extension):
    export_id = uuid.uuid4().hex
    actual_extension = extension
    if extension == ".csv":
        filename = f"anomai_cleaned_{export_id}.csv"
        path = os.path.join(EXPORT_DIR, filename)
        cleaned_data.to_csv(path, index=False)
    elif extension == ".tsv":
        filename = f"anomai_cleaned_{export_id}.tsv"
        path = os.path.join(EXPORT_DIR, filename)
        cleaned_data.to_csv(path, index=False, sep="\t")
    elif extension == ".txt":
        filename = f"anomai_cleaned_{export_id}.txt"
        path = os.path.join(EXPORT_DIR, filename)
        cleaned_data.to_csv(path, index=False, sep="\t")
    elif extension == ".xlsx":
        filename = f"anomai_cleaned_{export_id}.xlsx"
        path = os.path.join(EXPORT_DIR, filename)
        cleaned_data.to_excel(path, index=False, engine="openpyxl")
    elif extension == ".xls":
        # pandas/openpyxl does not reliably write legacy XLS. Return a modern Excel workbook.
        actual_extension = ".xlsx"
        filename = f"anomai_cleaned_{export_id}.xlsx"
        path = os.path.join(EXPORT_DIR, filename)
        cleaned_data.to_excel(path, index=False, engine="openpyxl")
    elif extension == ".ods":
        filename = f"anomai_cleaned_{export_id}.ods"
        path = os.path.join(EXPORT_DIR, filename)
        cleaned_data.to_excel(path, index=False, engine="odf")
    elif extension == ".parquet":
        filename = f"anomai_cleaned_{export_id}.parquet"
        path = os.path.join(EXPORT_DIR, filename)
        cleaned_data.to_parquet(path, index=False)
    elif extension == ".xml":
        filename = f"anomai_cleaned_{export_id}.xml"
        path = os.path.join(EXPORT_DIR, filename)
        cleaned_data.to_xml(path, index=False, root_name="dataset", row_name="row")
    elif extension == ".json":
        filename = f"anomai_cleaned_{export_id}.json"
        path = os.path.join(EXPORT_DIR, filename)
        records = make_json_safe(cleaned_data)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(records, handle, ensure_ascii=False, indent=2)
    else:
        filename = f"anomai_cleaned_{export_id}.jsonl"
        path = os.path.join(EXPORT_DIR, filename)
        records = make_json_safe(cleaned_data)
        with open(path, "w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    return path, filename, actual_extension


@app.post("/analyze")
async def analyze_dataset(dataset: UploadFile = File(...)):
    temp_path = None
    try:
        extension = validate_uploaded_file(dataset)
        file_size = 0
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
            temp_path = temp_file.name
            while True:
                chunk = await dataset.read(1024 * 1024)
                if not chunk:
                    break
                file_size += len(chunk)
                if file_size > MAX_FILE_SIZE_BYTES:
                    raise HTTPException(status_code=413, detail=f"File is too large. Maximum allowed size is {MAX_FILE_SIZE_MB} MB.")
                temp_file.write(chunk)

        if file_size == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        result = run_pipeline(temp_path, statistical_method="iqr", contamination=0.05)
        cleaned_df = result.pop("cleaned_data", None)
        if cleaned_df is None:
            raise ValueError("Pipeline did not return cleaned data.")

        export_path, export_filename, actual_extension = export_cleaned_dataset(cleaned_df, extension)
        result["cleaned_data"] = make_json_safe(cleaned_df)
        result["cleaned_file"] = {
            "filename": export_filename,
            "download_url": f"/download/{export_filename}",
            "format": actual_extension.replace(".", ""),
            "source_format": extension.replace(".", "")
        }
        result["api"] = {
            "service": "AnomAI ML Service",
            "version": "2.0.0",
            "input_format": extension.replace(".", ""),
            "output_format": actual_extension.replace(".", ""),
            "file_size_bytes": file_size
        }
        return JSONResponse(status_code=200, content=make_json_safe(result))

    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        print("ANOMAI ML ERROR:", repr(error))
        raise HTTPException(status_code=500, detail="The ML pipeline could not complete this dataset. Check the dataset structure and server logs.") from error
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


@app.get("/download/{filename}")
def download_cleaned_dataset(filename: str):
    if not filename.startswith("anomai_cleaned_"):
        raise HTTPException(status_code=400, detail="Invalid cleaned dataset filename.")
    safe_name = os.path.basename(filename)
    file_path = os.path.join(EXPORT_DIR, safe_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Cleaned dataset file not found.")
    return FileResponse(file_path, filename=safe_name)
