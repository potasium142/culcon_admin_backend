import datetime
import re
from pydantic import BaseModel, EmailStr, Field


class EditStaffAccount(BaseModel):
    username: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    password: str


class EditEmployeeInfo(BaseModel):
    ssn: str = Field(pattern=r"[0-9]+")
    phonenumber: str = Field(pattern=r"0[1-9]{2}[0-9]{7}")
    realname: str
    email: EmailStr
    dob: datetime.date
