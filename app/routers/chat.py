from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import ChatRequest

router = APIRouter()

@router.post("/ai/chat/")
async def chat_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Test chat endpoint."""
    
    try:
        # Simple static response for testing
        response = f"Hello! I received your message: '{request.query}'. The chat system is working! (User ID: {request.user_id})"
        return {"response": response}
        
    except Exception as e:
        print(f"Chat endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Chat service temporarily unavailable"
        )
