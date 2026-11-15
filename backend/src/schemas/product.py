from pydantic import BaseModel, Field
class ProductInput(BaseModel):
    name: str = Field(min_length=2, max_length=160)
class PublishInput(BaseModel):
    job_id: int
    expected_version: int = Field(ge=0)
    request_id: str = Field(min_length=8, max_length=64)
class RollbackInput(BaseModel):
    target_version_id: int
    expected_version: int = Field(ge=0)
    request_id: str = Field(min_length=8, max_length=64)
