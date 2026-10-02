from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException

from app.database.mongodb import sessions_collection, messages_collection
from app.schemas.chat import (
    SessionCreate,
    SessionResponse,
    MessageCreate,
    MessageResponse,
    MessageListResponse
)

from bson import ObjectId
from bson.errors import InvalidId

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.post("/sessions", response_model=SessionResponse, status_code=201)
def create_session(session_data: SessionCreate):
    now = datetime.now(timezone.utc)

    session = {
        "user_id": session_data.user_id,
        "started_at": now,
        "last_message_at": now,
        "status": "active",
        "expires_at": now + timedelta(hours=24)
    }

    try:
        result = sessions_collection.insert_one(session)

        return SessionResponse(
            id=str(result.inserted_id),
            user_id=session["user_id"],
            status=session["status"]
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar sessão: {error}"
        )
        
        
@router.post("/messages", response_model=MessageResponse, status_code=201)
def create_message(message_data: MessageCreate):
    try:
        session_id = ObjectId(message_data.session_id)
    except InvalidId:
        raise HTTPException(
            status_code=400,
            detail="session_id inválido."
        )

    session = sessions_collection.find_one({"_id": session_id})

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Sessão não encontrada."
        )

    response_to = None

    if message_data.response_to:
        try:
            response_to = ObjectId(message_data.response_to)
        except InvalidId:
            raise HTTPException(
                status_code=400,
                detail="response_to inválido."
            )

    now = datetime.now(timezone.utc)

    message = {
        "session_id": session_id,
        "sender_id": message_data.sender_id,
        "content": message_data.content,
        "type": message_data.type,
        "response_to": response_to,
        "created_at": now
    }

    try:
        result = messages_collection.insert_one(message)

        sessions_collection.update_one(
            {"_id": session_id},
            {
                "$set": {
                    "last_message_at": now
                }
            }
        )

        return MessageResponse(
            id=str(result.inserted_id),
            session_id=str(session_id),
            sender_id=message["sender_id"],
            content=message["content"],
            type=message["type"],
            response_to=str(response_to) if response_to else None,
            created_at=now.isoformat()
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar mensagem: {error}"
        )        
        

@router.get(
    "/sessions/{session_id}/messages",
    response_model=MessageListResponse
)
def get_session_messages(
    session_id: str,
    limit: int = 20,
    cursor: str | None = None
):
    # Valida o ID da sessão
    try:
        session_object_id = ObjectId(session_id)
    except InvalidId:
        raise HTTPException(
            status_code=400,
            detail="session_id inválido."
        )

    # Verifica se a sessão existe
    session = sessions_collection.find_one(
        {"_id": session_object_id}
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Sessão não encontrada."
        )

    # Limita a quantidade de registros por página
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="limit deve estar entre 1 e 100."
        )

    query = {
        "session_id": session_object_id
    }

    # Se houver cursor, busca somente mensagens posteriores
    if cursor:
        try:
            cursor_object_id = ObjectId(cursor)
        except InvalidId:
            raise HTTPException(
                status_code=400,
                detail="cursor inválido."
            )

        query["_id"] = {
            "$gt": cursor_object_id
        }

    # Busca uma mensagem extra para saber se existe próxima página
    documents = list(
        messages_collection
        .find(query)
        .sort([
            ("created_at", 1),
            ("_id", 1)
        ])
        .limit(limit + 1)
    )

    has_next_page = len(documents) > limit

    if has_next_page:
        documents = documents[:limit]

    messages = [
        MessageResponse(
            id=str(document["_id"]),
            session_id=str(document["session_id"]),
            sender_id=document["sender_id"],
            content=document["content"],
            type=document["type"],
            response_to=(
                str(document["response_to"])
                if document.get("response_to")
                else None
            ),
            created_at=document["created_at"].isoformat()
        )
        for document in documents
    ]

    next_cursor = None

    if has_next_page and documents:
        next_cursor = str(documents[-1]["_id"])

    return MessageListResponse(
        messages=messages,
        next_cursor=next_cursor
    )        