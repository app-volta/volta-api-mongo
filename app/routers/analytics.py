from datetime import datetime, time, timezone
from fastapi import APIRouter, HTTPException, Query
from app.database.mongodb import messages_collection, sessions_collection

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


@router.get("/messages-per-day")
def get_messages_per_day():
    pipeline = [
        {
            "$match": {
                "created_at": {
                    "$type": "date"
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$created_at"
                    }
                },
                "total_messages": {
                    "$sum": 1
                }
            }
        },
        {
            "$sort": {
                "_id": 1
            }
        }
    ]

    results = list(messages_collection.aggregate(pipeline))

    return [
        {
            "date": result["_id"],
            "total_messages": result["total_messages"]
        }
        for result in results
    ]
    
    
@router.get("/average-ai-response-time")
def get_average_ai_response_time():
    pipeline = [
        {
            "$match": {
                "type": "ai",
                "response_to": {
                    "$ne": None
                }
            }
        },
        {
            "$lookup": {
                "from": "messages",
                "localField": "response_to",
                "foreignField": "_id",
                "as": "user_message"
            }
        },
        {
            "$unwind": "$user_message"
        },
        {
            "$match": {
                "user_message.type": "user"
            }
        },
        {
            "$project": {
                "response_time_ms": {
                    "$subtract": [
                        "$created_at",
                        "$user_message.created_at"
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": None,
                "total_responses": {
                    "$sum": 1
                },
                "average_response_time_ms": {
                    "$avg": "$response_time_ms"
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "total_responses": 1,
                "average_response_time_ms": 1,
                "average_response_time_seconds": {
                    "$divide": [
                        "$average_response_time_ms",
                        1000
                    ]
                }
            }
        }
    ]

    results = list(messages_collection.aggregate(pipeline))

    if not results:
        return {
            "total_responses": 0,
            "average_response_time_ms": None,
            "average_response_time_seconds": None
        }

    return results[0]


@router.get("/active-sessions")
def get_active_sessions(
    start_date: str | None = Query(
        default=None,
        description="Data inicial no formato YYYY-MM-DD"
    ),
    end_date: str | None = Query(
        default=None,
        description="Data final no formato YYYY-MM-DD"
    )
):
    match_filter = {
        "status": "active",
        "started_at": {
            "$type": "date"
        }
    }

    date_filter = {}

    try:
        if start_date:
            start = datetime.strptime(
                start_date,
                "%Y-%m-%d"
            ).replace(tzinfo=timezone.utc)

            date_filter["$gte"] = start

        if end_date:
            end = datetime.combine(
                datetime.strptime(
                    end_date,
                    "%Y-%m-%d"
                ).date(),
                time.max,
                tzinfo=timezone.utc
            )

            date_filter["$lte"] = end

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Datas devem estar no formato YYYY-MM-DD."
        )

    if start_date and end_date and start > end:
        raise HTTPException(
            status_code=400,
            detail="start_date não pode ser maior que end_date."
        )

    if date_filter:
        match_filter["started_at"].update(date_filter)

    pipeline = [
        {
            "$match": match_filter
        },
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$started_at"
                    }
                },
                "active_sessions": {
                    "$sum": 1
                }
            }
        },
        {
            "$sort": {
                "_id": 1
            }
        }
    ]

    results = list(
        sessions_collection.aggregate(pipeline)
    )

    return [
        {
            "date": result["_id"],
            "active_sessions": result["active_sessions"]
        }
        for result in results
    ]