"""
Aeryn — Structured Logger
Simple structured logging with timestamps and levels.
"""

import sys
import json
import logging
from datetime import datetime
from typing import Optional

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout,
)

# Create logger
logger = logging.getLogger('aeryn')


def info(msg: str, **kwargs):
    """Log info message with optional structured data."""
    _log('INFO', msg, **kwargs)


def warn(msg: str, **kwargs):
    """Log warning message with optional structured data."""
    _log('WARNING', msg, **kwargs)


def error(msg: str, **kwargs):
    """Log error message with optional structured data."""
    _log('ERROR', msg, **kwargs)


def debug(msg: str, **kwargs):
    """Log debug message with optional structured data."""
    _log('DEBUG', msg, **kwargs)


def _log(level: str, msg: str, **kwargs):
    """Internal log function with structured data support."""
    if kwargs:
        msg = f"{msg} | {json.dumps(kwargs, default=str)}"
    
    if level == 'INFO':
        logger.info(msg)
    elif level == 'WARNING':
        logger.warning(msg)
    elif level == 'ERROR':
        logger.error(msg)
    elif level == 'DEBUG':
        logger.debug(msg)


def log_exception(exc: Exception, context: str = ""):
    """Log exception with traceback."""
    import traceback
    tb = traceback.format_exc()
    error(f"Exception in {context}: {exc}", traceback=tb)
