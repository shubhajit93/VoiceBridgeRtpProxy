from pydantic import BaseModel, Field
from enum import Enum


class BaseResponse(BaseModel):
    status_code: int = Field(default=200)


class OptInResponse(BaseResponse):
    callId: str
    host: str
    port: int


# Define the payload model for optout
class OptOutRequest(BaseModel):
    callId: str
    host: str
    port: int


class OptCloseRequest(BaseModel):
    callId: str


class OptCommonResponse(BaseResponse):
    message: str


class Actor(str, Enum):
    ASTERISK = "asterisk"
    DE = "dialogue_engine"
