from pydantic import BaseModel, Field


class FacultyLoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class StudentLoginRequest(BaseModel):
    roll_no: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    username: str
    student_id: int | None = None
    must_change_password: bool = False


class ChangePasswordRequest(BaseModel):
    new_password: str = Field(min_length=6, description="New password, minimum 6 characters")
