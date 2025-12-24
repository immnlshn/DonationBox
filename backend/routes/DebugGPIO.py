import logging
from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

class GPIORequest(BaseModel):
    pin: int
    value: int

@router.post('/gpio')
async def gpio_debug(request: GPIORequest):
    """
    Handles the GPIO debug endpoint for setting a specified pin to a given value.

    This function is designed to accept input via a POST request and sets the
    specified GPIO pin to the provided value. It allows users to debug and manually
    control GPIO hardware.

    :param request: A GPIORequest object containing the pin and value.
    :return: A dictionary confirming the pin and value on successful operation.
    :rtype: dict
    """
    # TODO implement GPIOService mock logic
    return {"pin": request.pin, "value": request.value}
