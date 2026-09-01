from pydantic import BaseModel


class GeneratedFileRead(BaseModel):
    file_name: str
    download_path: str


class RestoreStatusRead(BaseModel):
    status: str
    message: str
    item_count: int | None = None
    attachment_count: int | None = None
