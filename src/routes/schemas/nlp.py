from pydantic import BaseModel
from typing import Optional

# Pydantic Scheme of the request in the API with push chunks endpoint
class PushRequest(BaseModel):
    do_reset : Optional[int] = 0

# Pydantic Scheme of the request in the API with search chunks endpoint
class SearchRequest(BaseModel):
    text : str
    limit : Optional[int] = 10