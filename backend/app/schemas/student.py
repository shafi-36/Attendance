from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class StudentRegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    roll_no: str = Field(min_length=1, max_length=50)
    department: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


class StudentOut(BaseModel):
    id: int
    user_id: int
    roll_no: str
    name: str
    department: str
    email: str
    image_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class StudentListItem(BaseModel):
    id: int
    roll_no: str
    name: str
    department: str
    email: str
    image_url: str | None
    has_embedding: bool
    created_at: datetime

    model_config = {"from_attributes": True}
