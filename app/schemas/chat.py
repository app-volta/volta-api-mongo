from typing import Literal

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    user_id: str = Field(min_length=1)


class SessionResponse(BaseModel):
    id: str
    user_id: str
    status: str


class MessageCreate(BaseModel):
    session_id: str
    sender_id: str = Field(min_length=1)
    content: str = Field(min_length=1)
    type: Literal["user", "ai", "system"]
    response_to: str | None = None


class MessageResponse(BaseModel):
    id: str
    session_id: str
    sender_id: str
    content: str
    type: str
    response_to: str | None
    created_at: str
 
    
class MessageListResponse(BaseModel):
    messages: list[MessageResponse]
    next_cursor: str | None