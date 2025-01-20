import datetime
from pydantic import BaseModel

from db.postgresql.models.staff_account import AccountStatus


class EditStaffAccount(BaseModel):
    username: str
    password: str
    status: AccountStatus


class EditEmployeeInfo(BaseModel):
    ssn: str
    phonenumber: str
    realname: str
    email: str
    dob: datetime.date
