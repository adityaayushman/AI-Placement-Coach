from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Role = Literal["student", "coordinator", "admin"]
CompanyType = Literal["product", "service"]
Email = Annotated[str, Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=255)]


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class RegisterIn(BaseModel):
    email: Email
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=200)


class LoginIn(BaseModel):
    email: Email
    password: str = Field(max_length=128)


class RefreshIn(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: Role


class UserOut(ORM):
    id: int
    email: str
    full_name: str
    role: Role


class StaffCreateIn(RegisterIn):
    role: Literal["coordinator", "admin"]


class ProfileIn(BaseModel):
    department: str = Field(default="", max_length=100)
    graduation_year: int | None = Field(default=None, ge=2000, le=2100)
    gender: str | None = Field(default=None, max_length=30)
    target_company_type: CompanyType = "product"
    target_role: str = Field(default="Software Engineer", max_length=100)
    cgpa: float | None = Field(default=None, ge=0, le=10)
    backlogs: int = Field(default=0, ge=0, le=50)
    tenth_pct: float | None = Field(default=None, ge=0, le=100)
    twelfth_pct: float | None = Field(default=None, ge=0, le=100)
    internships: int = Field(default=0, ge=0, le=20)


class ProfileOut(ProfileIn, ORM):
    pseudonym_id: str


class AcademicIn(BaseModel):
    term: str = Field(max_length=40)
    gpa: float = Field(ge=0, le=10)
    backlogs: int = Field(default=0, ge=0, le=50)


class AcademicOut(AcademicIn, ORM):
    id: int


class CodingIn(BaseModel):
    platform: str = Field(max_length=60)
    problems_solved: int = Field(ge=0, le=100000)
    contest_rating: int | None = Field(default=None, ge=0, le=5000)


class CodingOut(CodingIn, ORM):
    id: int
    created_at: datetime


class ProjectIn(BaseModel):
    title: str = Field(max_length=200)
    description: str = Field(default="", max_length=5000)
    tech: list[str] = Field(default_factory=list, max_length=30)
    complexity: int = Field(default=1, ge=1, le=3)


class ProjectOut(ProjectIn, ORM):
    id: int


class CertificationIn(BaseModel):
    name: str = Field(max_length=200)
    issuer: str = Field(default="", max_length=200)
    year: int | None = Field(default=None, ge=1990, le=2100)


class CertificationOut(CertificationIn, ORM):
    id: int


class ConsentIn(BaseModel):
    scope: str
    granted: bool


class ConsentState(BaseModel):
    scope: str
    description: str
    granted: bool
