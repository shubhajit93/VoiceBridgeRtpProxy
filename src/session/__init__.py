from pydantic import BaseModel, Field
from enum import Enum


class CallContext(BaseModel):
    class Status(str, Enum):
        ACTIVE = "active"
        INACTIVE = "inactive"

    callId: str
    inbound: dict = {}
    outbound: dict = {}
    status: Status = Status.INACTIVE

    def is_activate(self) -> bool:
        return self.status == CallContext.Status.ACTIVE

    def deactivate(self):
        self.status = CallContext.Status.INACTIVE

    def activate(self):
        self.status = CallContext.Status.ACTIVE

    def is_active(self) -> bool:
        return self.status == CallContext.Status.ACTIVE
