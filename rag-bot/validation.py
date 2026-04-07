"""
Input validation schemas using Pydantic
Validates all API inputs for security and reliability
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import re

# Phone number validation regex (international format)
PHONE_REGEX = re.compile(r'^\d{10,15}$')

# File path validation
SAFE_PATH_REGEX = re.compile(r'^[a-zA-Z0-9_\-/\.]+$')

class QueryRequest(BaseModel):
    """Validation for /api/query endpoint"""
    user_id: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=4000)
    thread_id: Optional[str] = Field(None, max_length=100)

    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        if not v.strip():
            raise ValueError('user_id cannot be empty')
        return v.strip()

    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('message cannot be empty')
        # Remove excessive whitespace
        return ' '.join(v.split())

class WhatsAppSendRequest(BaseModel):
    """Validation for /api/whatsapp/send endpoint"""
    phone_number: str = Field(..., min_length=10, max_length=15)
    message: str = Field(..., min_length=1, max_length=4096)

    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v):
        # Remove common separators
        cleaned = v.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')

        if not PHONE_REGEX.match(cleaned):
            raise ValueError('Invalid phone number format. Use digits only (10-15 digits)')

        return cleaned

    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('message cannot be empty')
        # WhatsApp message length limit
        if len(v) > 4096:
            raise ValueError('message too long (max 4096 characters)')
        return v

class WhatsAppWelcomeRequest(BaseModel):
    """Validation for /api/whatsapp/welcome endpoint"""
    phone_number: str = Field(..., min_length=10, max_length=15)
    name: Optional[str] = Field(None, max_length=100)

    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v):
        cleaned = v.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
        if not PHONE_REGEX.match(cleaned):
            raise ValueError('Invalid phone number format')
        return cleaned

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v and not v.strip():
            return None
        return v.strip() if v else None

class UploadRequest(BaseModel):
    """Validation for /api/upload endpoint"""
    file_paths: List[str] = Field(..., min_length=1, max_length=100)

    @field_validator('file_paths')
    @classmethod
    def validate_paths(cls, v):
        validated = []
        for path in v:
            # Check for path traversal attempts
            if '..' in path:
                raise ValueError(f'Invalid file path (path traversal detected): {path}')

            # Check for safe characters
            if not SAFE_PATH_REGEX.match(path):
                raise ValueError(f'Invalid file path (unsafe characters): {path}')

            validated.append(path)

        return validated

def validate_request(schema_class: type[BaseModel], data: dict) -> tuple[bool, Optional[BaseModel], Optional[str]]:
    """
    Validate request data against Pydantic schema

    Returns:
        (is_valid, validated_data, error_message)
    """
    try:
        validated = schema_class(**data)
        return True, validated, None
    except Exception as e:
        return False, None, str(e)
