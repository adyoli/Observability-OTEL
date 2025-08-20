from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentMetadataCreate(BaseModel):
    filename: str
    file_size: int
    file_type: str
    content_type: Optional[str] = None
    file_path: Optional[str] = None


class DocumentMetadataResponse(BaseModel):
    id: int
    client_id: str
    filename: str
    file_size: int
    file_type: str
    content_type: Optional[str] = None
    upload_timestamp: datetime
    file_path: Optional[str] = None

    class Config:
        from_attributes = True
