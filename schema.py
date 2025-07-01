from typing import Optional, Dict
from pydantic import BaseModel
from typing import List

class RunJobRequest(BaseModel):
    # job_instance_id: int
    job_instance_ids: List[int]
    restart: Optional[bool] = False
    data: Optional[Dict] = None  # <-- make sure this is Optional if you want to skip it

class StopJobRequestSchema(BaseModel):
    #job_instance_id: int
    job_instance_ids: List[int]