from pydantic import BaseModel, EmailStr, Field


class EditCustomerInfo(BaseModel):
    email: EmailStr
    address: str
    phone: str = Field(pattern=r"0[1-9]{2}[0-9]{7}")
    profile_description: str
    profile_name: str


class EditCustomerAccount(BaseModel):
    username: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    password: str
