from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import logging

# Get logger
logger = logging.getLogger(__name__)

async def error_handling_middleware(request: Request, call_next):
    """
    Middleware for consistent error handling across the API.
    
    Args:
        request: The incoming request
        call_next: The next middleware or route handler
        
    Returns:
        Response object, either from the route handler or an error response
    """
    try:
        # Process the request normally
        return await call_next(request)
    
    except SQLAlchemyError as e:
        # Handle database-specific errors
        error_msg = str(e)
        logger.error(f"Database error: {error_msg}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "A database error occurred",
                "type": "database_error"
            }
        )
        
    except Exception as e:
        # Handle all other exceptions
        error_msg = str(e)
        logger.error(f"Unhandled exception: {error_msg}")
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An unexpected error occurred",
                "type": "server_error"
            }
        )