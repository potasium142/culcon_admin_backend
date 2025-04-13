from datetime import time
from pydantic import BaseModel, Field


class ShipperShift(BaseModel):
    shipper_id: str
    start_time: time = Field(time(tzinfo=None))
    end_time: time = Field(time(tzinfo=None))
