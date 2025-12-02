from pydantic import BaseModel
from typing import Optional

# Pydantic Scheme of the request in the API with process endpoint
class ProcessRequest(BaseModel):
    file_id : str = None
    chunk_size : Optional[int] = 100
    overlap_size : Optional[int] = 20
    do_reset : Optional[bool] = False
    
