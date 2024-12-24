from dataclasses import dataclass
from datetime import date
from pydantic import BaseModel
from db.models.staff_account import (
    AccountType,
    StaffAccount,
    EmployeeInfo,
    AccountStatus,
)


@dataclass
class AccountInfoForm(BaseModel):
    ssn: str
    phonenumber: str
    realname: str
    email: str
    dob: date

    def get_employee_info(self) -> EmployeeInfo:
        return EmployeeInfo(
            ssn=self.ssn,
            phonenumber=self.phonenumber,
            realname=self.realname,
            email=self.email,
            dob=self.dob,
        )


@dataclass
class AccountCreateDto(BaseModel):
    username: str
    password: str
    type: AccountType
    employee_info: AccountInfoForm
    account_status: AccountStatus

    def get_account(self) -> StaffAccount:
        account = StaffAccount(
            username=self.username,
            password=self.password,
            type=self.type,
            status=self.account_status,
            employee_info=self.employee_info.get_employee_info(),
        )
        return account
