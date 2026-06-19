from datetime import datetime

from pydantic import BaseModel, Field


class AttendanceMarkRequest(BaseModel):
    session_id: int
    image_base64: str = Field(description="Base64-encoded JPEG image")


class AttendanceOut(BaseModel):
    id: int
    session_id: int
    student_id: int
    attendance_time: datetime
    confidence: float
    status: str

    model_config = {"from_attributes": True}


class MarkAttendanceResponse(BaseModel):
    attendance_id: int
    student_id: int
    student_name: str
    roll_no: str
    confidence: float
    status: str
    message: str
