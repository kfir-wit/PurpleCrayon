"""
Decorators for PurpleCrayon.

This module contains decorators for LangChain tools and other utilities.
"""

from typing import Any, Callable, Dict, List, Optional, Union
from functools import wraps
import asyncio
import inspect


def langchain_tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    return_direct: bool = False,
    args_schema: Optional[type] = None
):
    """
    Decorator to convert a function into a LangChain tool.
    
    Args:
        name: Tool name (defaults to function name)
        description: Tool description (defaults to function docstring)
        return_direct: Whether to return results directly
        args_schema: Pydantic model for argument validation
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # Add LangChain tool metadata
        wrapper._langchain_tool = True
        wrapper._tool_name = name or func.__name__
        wrapper._tool_description = description or func.__doc__ or ""
        wrapper._return_direct = return_direct
        wrapper._args_schema = args_schema
        
        return wrapper
    return decorator


def async_tool(func: Callable) -> Callable:
    """
    Decorator to mark a function as an async tool.
    
    This ensures proper async handling for LangChain tools.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if inspect.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    wrapper._async_tool = True
    return wrapper


def validate_input(schema: type):
    """
    Decorator to validate function input using a Pydantic schema.
    
    Args:
        schema: Pydantic model class for validation
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Validate input using the schema
            try:
                validated_data = schema(**kwargs)
                return func(*args, **validated_data.dict())
            except Exception as e:
                raise ValueError(f"Input validation failed: {e}")
        
        wrapper._input_schema = schema
        return wrapper
    return decorator


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator to retry function execution on failure.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    if inspect.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        raise e
                    await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        raise e
                    import time
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
        
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_execution(logger_name: str = "purplecrayon"):
    """
    Decorator to log function execution.
    
    Args:
        logger_name: Name of the logger to use
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import logging
            logger = logging.getLogger(logger_name)
            
            logger.info(f"Executing {func.__name__} with args: {args}, kwargs: {kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.info(f"Successfully executed {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                raise
        
        return wrapper
    return decorator