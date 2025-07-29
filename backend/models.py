# Multi-tenant Client Models
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid

class ClientStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"

class ClientCreate(BaseModel):
    name: str = Field(..., description="Client name or company")
    email: EmailStr = Field(..., description="Client email")
    openai_api_key: str = Field(..., description="Client's OpenAI API key")
    openai_assistant_id: str = Field(..., description="Client's OpenAI Assistant ID")

class Client(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: EmailStr
    openai_api_key: str
    openai_assistant_id: str
    unique_url: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    whatsapp_port: int
    status: ClientStatus = ClientStatus.PENDING
    connected_phone: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: Optional[datetime] = None

class ClientResponse(BaseModel):
    id: str
    name: str
    email: str
    openai_api_key: Optional[str] = None
    openai_assistant_id: Optional[str] = None
    status: ClientStatus
    connected_phone: Optional[str]
    whatsapp_port: int
    unique_url: str
    created_at: datetime
    last_activity: Optional[datetime]

class ClientMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    phone_number: str
    message: str
    timestamp: int
    is_from_ai: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EmailTemplate(BaseModel):
    to_email: str
    client_name: str
    landing_url: str
    
class ToggleClientRequest(BaseModel):
    action: str  # "connect" or "disconnect"

class UpdateEmailRequest(BaseModel):
    new_email: EmailStr

class PausedConversation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    phone_number: str
    paused_at: datetime = Field(default_factory=datetime.utcnow)
    paused_by: str = "client"  # "client" or "global"