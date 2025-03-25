from pydantic import BaseModel


class EditCustomerInfo(BaseModel):
    email: str
    address: str
    phone: str
    profile_description: str
    profile_name: str


class EditCustomerAccount(BaseModel):
    username: str
    password: str
