import time
start_time = time.time()
print(f"[{time.strftime('%X')}] Starting mainImport load...")

from fastapi import FastAPI, HTTPException
from starlette.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from schema import RunJobRequest,StopJobRequestSchema
import os
import traceback
from utils.logger import logger
from utils.exceptions import Error
import dataGetter as DG
print(f"[{time.strftime('%X')}] mainImport loaded in {time.time() - start_time:.2f}s")

# ------------ Load Environment Variables ------------
load_dotenv()

# ------------ FastAPI Initialization ------------
app = FastAPI(
    title="Job Trigger API",
    description="API to trigger scheduled jobs",
    version="1.0"
)


# ------------ Oracle SQLAlchemy Configuration ------------
ORACLE_HOST = os.environ.get("ORACLE_HOST")
ORACLE_USERNAME = os.environ.get("ORACLE_USERNAME")
ORACLE_PASSWORD = os.environ.get("ORACLE_PASSWORD")

if not all([ORACLE_HOST, ORACLE_USERNAME, ORACLE_PASSWORD]):
    raise Exception("DB credentials are missing in environment variables.")

# SQLAlchemy engine for Oracle (using oracledb in thin mode)
DATABASE_URL = f"oracle+oracledb://{ORACLE_USERNAME}:{ORACLE_PASSWORD}@{ORACLE_HOST}"

try:
    start_db_connection = time.time()
    engine = create_engine(DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print(f"[{time.strftime('%X')}] DB connection established in {time.time() - start_db_connection:.2f}s")

    print("SQLAlchemy Oracle engine created successfully.")
except Exception as e:
    print(f"❌ Failed to create engine: {str(e)}")
    raise

# ------------ Root Health Check Endpoint ------------
@app.get("/")
def welcome():
    return {"message": "welcome to job trigger API"}
# ------------ Job Trigger Endpoint ------------
@app.post("/run_job/")
def run_job(run_job_request: RunJobRequest):
    """
    Trigger a job based on job_instance_id and optional restart flag.
    """
    db: Session = SessionLocal()
    try:
        result = DG.run_job(
            request=run_job_request,
            connection=db
        )
        return {"message": "SUCCESS", "api_response": result}

    except Error as e:
        raise HTTPException(status_code=e.status_code, detail=e.details)

    except Exception as e:
        traceback.print_exc()
        logger.logger.error(f"ERROR OCCURRED: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    finally:
        db.close()


@app.post("/stop_job/")
def stop_job(stop_job_request: StopJobRequestSchema):
    """
    stop a job based on job_instance_id and optional restart flag.
    """
    db: Session = SessionLocal()
    try:
        result = DG.stop_job(
            request=stop_job_request,
            connection=db
        )
        return {"message": "SUCCESS", "api_response": result}

    except Error as e:
       raise HTTPException(status_code=e.status_code, detail=e.details)

    except Exception as e:
        traceback.print_exc()
        logger.logger.error(f"ERROR OCCURRED: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    finally:
        db.close()

# ------------ Run with Uvicorn ------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080)
