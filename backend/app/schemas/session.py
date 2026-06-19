from datetime import date, datetime, time

from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    subject: str = Field(min_length=1, max_length=150)
    session_date: date
    start_time: time
    end_time: time | None = None


class SessionOut(BaseModel):
    id: int
    title: str
    subject: str
    faculty_id: int
    session_date: date
    start_time: time
    end_time: time | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
