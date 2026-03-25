from pydantic import BaseModel
from typing import Optional, List, Any


class RunRequest(BaseModel):
    clean: Optional[bool] = True
    analyze: Optional[bool] = True
    transform: Optional[bool] = False
    transform_params: Optional[dict] = {}
