"""
Travel Sessions API endpoints with database integration
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.orm import Session
import json
import uuid

try:
    from fastapi import APIRouter, Depends, HTTPException
    from app.db.session import get_db
    from app.api.endpoints.auth import get_current_active_user
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    APIRouter = None
    Depends = None
    HTTPException = None
    get_current_active_user = None


# Pydantic models
class TravelSessionRequest(BaseModel):
    message: str
    source: Optional[str] = "web"


class TravelSessionResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: Optional[list] = None


# Create router only if FastAPI is available
if FASTAPI_AVAILABLE:
    router = APIRouter(prefix="/travel/sessions", tags=["travel-sessions"])
    
    @router.post("/", response_model=TravelSessionResponse)
    def create_travel_session(
        request: TravelSessionRequest, 
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_active_user)
    ):
        """Create a new travel session and process initial message."""
        try:
            # Generate session ID
            session_id = str(uuid.uuid4())
            user_id = str(current_user["id"])
            
            # Create session in database
            session_data = {
                "messages": [
                    {
                        "role": "user",
                        "content": request.message,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                ],
                "source": request.source
            }
            
            from sqlalchemy import text
            cursor = db.execute(
                text("""
                INSERT INTO travel_sessions (id, user_id, status, session_data, context_data, created_at)
                VALUES (:id, :user_id, :status, :session_data, :context_data, datetime('now'))
                """),
                {
                    "id": session_id,
                    "user_id": user_id,
                    "status": "active",
                    "session_data": json.dumps(session_data),
                    "context_data": json.dumps({})
                }
            )
            db.commit()
            
            # Prepare response
            response_data = {
                "session_id": session_id,
                "message": f"Travel session created. How can I help you plan your trip?",
                "suggestions": [
                    "Tell me your travel dates",
                    "What's your destination?",
                    "How many travelers?",
                    "What's your budget?"
                ],
                "status": "active"
            }
            
            return TravelSessionResponse(
                success=True,
                data=response_data,
                metadata={
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": request.source
                }
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.put("/{session_id}", response_model=TravelSessionResponse)
    def update_travel_session(
        session_id: str, 
        request: TravelSessionRequest, 
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_active_user)
    ):
        """Update travel session with new message."""
        try:
            from sqlalchemy import text
            # Get existing session and verify ownership
            result = db.execute(
                text("SELECT * FROM travel_sessions WHERE id = :id AND user_id = :user_id"),
                {"id": session_id, "user_id": str(current_user["id"])}
            ).fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail="Session not found")
            
            # Parse existing session data
            session_data = json.loads(result[3]) if result[3] else {"messages": []}
            
            # Add new message
            session_data["messages"].append({
                "role": "user",
                "content": request.message,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Update session
            db.execute(
                text("""
                UPDATE travel_sessions 
                SET session_data = :session_data, updated_at = datetime('now')
                WHERE id = :id AND user_id = :user_id
                """),
                {
                    "session_data": json.dumps(session_data),
                    "id": session_id,
                    "user_id": str(current_user["id"])
                }
            )
            db.commit()
            
            # Prepare response
            response_data = {
                "session_id": session_id,
                "message": "I've received your message. Let me help you with your travel planning.",
                "parsed_intent": {
                    "message": request.message,
                    "confidence": 0.85
                },
                "suggestions": [
                    "View available flights",
                    "Search for hotels",
                    "Check travel requirements",
                    "Get destination information"
                ],
                "status": "active"
            }
            
            return TravelSessionResponse(
                success=True,
                data=response_data,
                metadata={
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "update"
                }
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/{session_id}")
    def get_travel_session(
        session_id: str, 
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_active_user)
    ):
        """Get travel session details."""
        from sqlalchemy import text
        result = db.execute(
            text("SELECT * FROM travel_sessions WHERE id = :id AND user_id = :user_id"),
            {"id": session_id, "user_id": str(current_user["id"])}
        ).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = json.loads(result[3]) if result[3] else {}
        context_data = json.loads(result[4]) if result[4] else {}
        
        return {
            "id": result[0],
            "user_id": result[1],
            "status": result[2],
            "session_data": session_data,
            "context_data": context_data,
            "created_at": result[5],
            "updated_at": result[6]
        }
else:
    router = None