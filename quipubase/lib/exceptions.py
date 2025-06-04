from fastapi import HTTPException


class QuipubaseException(HTTPException):
    """Base Tool Exception for handling errors on multiple backends"""

    ...
