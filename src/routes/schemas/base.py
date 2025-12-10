from pydantic import BaseModel , Field , EmailStr
from typing import Optional

# Pydantic Scheme of the request in the API with push chunks endpoint
class PostScheme(BaseModel):
    id : int = Field(default=None)
    title : str = Field(default=None)
    content : str = Field(default = None)
    class config:
        json_scheme_extra = {
            "post_demo": {
                "title": "some title about animals",
                "content": "some content about animals"
            }
        }


class UserSchema(BaseModel):
    fullname: str = Field(...)
    email: EmailStr = Field(...)
    password: str = Field(...)

    class Config:
        json_schema_extra = {
            "example": {
                "fullname": "Joe Doe",
                "email": "joe@xyz.com",
                "password": "any"
            }
        }


class UserLoginScheme(BaseModel):

    email : EmailStr = Field(default = None)
    password : str = Field(default = None)

    class config:
        json_schema_extra = {
            "user_demo": {
                "email":"help@bekbrace.com",
                "password":"123"
            }
        }