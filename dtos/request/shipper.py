from datetime import time
from pydantic import BaseModel


class ShipperShift(BaseModel):
    shipper_id: str
    start_time: time
    end_time: time
