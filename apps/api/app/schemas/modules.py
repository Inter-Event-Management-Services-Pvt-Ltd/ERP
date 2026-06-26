from pydantic import BaseModel


class ModuleStatusResponse(BaseModel):
    code: str
    enabled: bool
