from dataclasses import dataclass
from datetime import date
from pydantic import BaseModel, Field
from db.postgresql.models import staff_account as sa


@dataclass
class AccountInfoForm(BaseModel):
    ssn: str
    phonenumber: str = Field(pattern=r"0[1-9][0-9]{8,9}")
    realname: str
    email: str
    dob: date

    def get(self) -> sa.EmployeeInfo:
        return sa.EmployeeInfo(
            ssn=self.ssn,
            phonenumber=self.phonenumber,
            realname=self.realname,
            email=self.email,
            dob=self.dob,
        )


@dataclass
class AccountCreateDto(BaseModel):
    username: str = Field(pattern=r"[A-Za-z0-9_-]+")
    password: str
    type: sa.AccountType
    employee_info: AccountInfoForm
    account_status: sa.AccountStatus

    def get(self) -> sa.StaffAccount:
        account = sa.StaffAccount(
            username=self.username,
            password=self.password,
            type=self.type,
            status=self.account_status,
            employee_info=self.employee_info.get(),
        )
        return account
