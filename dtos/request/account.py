from dataclasses import dataclass
from datetime import date
from pydantic import BaseModel
from db.models.account import AccountType, Account, EmployeeInfo


@dataclass
class AccountCreateDto(BaseModel):
    username: str
    password: str
    ssn: str
    phonenumber: str
    realname: str
    email: str
    dob: date
    type: AccountType

    def get_account(self) -> Account:
        employee_info = EmployeeInfo(
            ssn=self.ssn,
            phonenumber=self.phonenumber,
            realname=self.realname,
            email=self.email,
            dob=self.dob
        )
        account = Account(
            username=self.username,
            password=self.password,
            type=self.type,
            employee_info=employee_info
        )
        return account
