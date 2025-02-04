import datetime
from pydantic import BaseModel


class EditStaffAccount(BaseModel):
    username: str
    password: str


class EditEmployeeInfo(BaseModel):
    ssn: str
    phonenumber: str
    realname: str
    email: str
    dob: datetime.date
