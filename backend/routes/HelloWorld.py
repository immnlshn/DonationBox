import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get('/')
async def hello_world():
    """
    A simple Hello World endpoint to verify that the API is working.

    :return: A JSON response with a greeting message.
    :rtype: JSON
    """
    logger.info("Hello World endpoint was called")
    return {"message": "Hello, World!"}