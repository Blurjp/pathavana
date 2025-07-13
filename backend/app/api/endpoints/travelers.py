"""
Travelers API endpoints with database integration and authentication
"""
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

try:
    from fastapi import APIRouter, Depends, HTTPException, Query
    from app.db.session import get_db
    from app.api.endpoints.auth import get_current_active_user
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    APIRouter = None
    Depends = None
    HTTPException = None
    Query = None
    get_current_active_user = None


# Pydantic models for travelers
class TravelerBase(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    passport_number: Optional[str] = None
    nationality: Optional[str] = None


class TravelerCreate(TravelerBase):
    pass


class TravelerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    passport_number: Optional[str] = None
    nationality: Optional[str] = None


class Traveler(TravelerBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Create router only if FastAPI is available
if FASTAPI_AVAILABLE:
    router = APIRouter(prefix="/travelers", tags=["travelers"])
    
    @router.get("/", response_model=List[Traveler])
    def get_travelers(
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_active_user)
    ):
        """Get all travelers for the current user"""
        query = db.execute(
            text("SELECT * FROM travelers WHERE user_id = :user_id ORDER BY created_at DESC LIMIT :limit OFFSET :skip"),
            {"user_id": current_user["id"], "limit": limit, "skip": skip}
        )
        travelers = query.fetchall()
        
        # Convert to dict format
        result = []
        for traveler in travelers:
            result.append({
                "id": traveler[0],
                "user_id": traveler[1],
                "first_name": traveler[2],
                "last_name": traveler[3],
                "email": traveler[4],
                "phone": traveler[5],
                "date_of_birth": traveler[6],
                "passport_number": traveler[7],
                "nationality": traveler[8],
                "created_at": traveler[9],
                "updated_at": traveler[10]
            })
        
        return result
    
    @router.post("/", response_model=Traveler)
    def create_traveler(
        traveler: TravelerCreate, 
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_active_user)
    ):
        """Create a new traveler"""
        user_id = current_user["id"]
        
        cursor = db.execute(
            text("""
                INSERT INTO travelers (user_id, first_name, last_name, email, phone, 
                                     date_of_birth, passport_number, nationality, created_at)
                VALUES (:user_id, :first_name, :last_name, :email, :phone, 
                        :date_of_birth, :passport_number, :nationality, datetime('now'))
            """),
            {
                "user_id": user_id,
                "first_name": traveler.first_name,
                "last_name": traveler.last_name,
                "email": traveler.email,
                "phone": traveler.phone,
                "date_of_birth": str(traveler.date_of_birth) if traveler.date_of_birth else None,
                "passport_number": traveler.passport_number,
                "nationality": traveler.nationality
            }
        )
        db.commit()
        
        traveler_id = cursor.lastrowid
        
        # Fetch the created traveler
        result = db.execute(
            text("SELECT * FROM travelers WHERE id = :id AND user_id = :user_id"),
            {"id": traveler_id, "user_id": user_id}
        ).fetchone()
        
        return {
            "id": result[0],
            "user_id": result[1],
            "first_name": result[2],
            "last_name": result[3],
            "email": result[4],
            "phone": result[5],
            "date_of_birth": result[6],
            "passport_number": result[7],
            "nationality": result[8],
            "created_at": result[9],
            "updated_at": result[10]
        }
    
    @router.get("/{traveler_id}", response_model=Traveler)
    def get_traveler(
        traveler_id: int, 
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_active_user)
    ):
        """Get a specific traveler by ID"""
        result = db.execute(
            text("SELECT * FROM travelers WHERE id = :id AND user_id = :user_id"),
            {"id": traveler_id, "user_id": current_user["id"]}
        ).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Traveler not found")
        
        return {
            "id": result[0],
            "user_id": result[1],
            "first_name": result[2],
            "last_name": result[3],
            "email": result[4],
            "phone": result[5],
            "date_of_birth": result[6],
            "passport_number": result[7],
            "nationality": result[8],
            "created_at": result[9],
            "updated_at": result[10]
        }
    
    @router.put("/{traveler_id}", response_model=Traveler)
    def update_traveler(
        traveler_id: int, 
        traveler: TravelerUpdate, 
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_active_user)
    ):
        """Update a traveler"""
        # Check if traveler exists and belongs to user
        existing = db.execute(
            text("SELECT * FROM travelers WHERE id = :id AND user_id = :user_id"),
            {"id": traveler_id, "user_id": current_user["id"]}
        ).fetchone()
        
        if not existing:
            raise HTTPException(status_code=404, detail="Traveler not found")
        
        # Build update query dynamically
        updates = []
        params = {"id": traveler_id, "user_id": current_user["id"]}
        
        if traveler.first_name is not None:
            updates.append("first_name = :first_name")
            params["first_name"] = traveler.first_name
        if traveler.last_name is not None:
            updates.append("last_name = :last_name")
            params["last_name"] = traveler.last_name
        if traveler.email is not None:
            updates.append("email = :email")
            params["email"] = traveler.email
        if traveler.phone is not None:
            updates.append("phone = :phone")
            params["phone"] = traveler.phone
        if traveler.date_of_birth is not None:
            updates.append("date_of_birth = :date_of_birth")
            params["date_of_birth"] = str(traveler.date_of_birth)
        if traveler.passport_number is not None:
            updates.append("passport_number = :passport_number")
            params["passport_number"] = traveler.passport_number
        if traveler.nationality is not None:
            updates.append("nationality = :nationality")
            params["nationality"] = traveler.nationality
        
        if updates:
            updates.append("updated_at = datetime('now')")
            query = f"UPDATE travelers SET {', '.join(updates)} WHERE id = :id AND user_id = :user_id"
            db.execute(text(query), params)
            db.commit()
        
        # Return updated traveler
        result = db.execute(
            text("SELECT * FROM travelers WHERE id = :id AND user_id = :user_id"),
            {"id": traveler_id, "user_id": current_user["id"]}
        ).fetchone()
        
        return {
            "id": result[0],
            "user_id": result[1],
            "first_name": result[2],
            "last_name": result[3],
            "email": result[4],
            "phone": result[5],
            "date_of_birth": result[6],
            "passport_number": result[7],
            "nationality": result[8],
            "created_at": result[9],
            "updated_at": result[10]
        }
    
    @router.delete("/{traveler_id}")
    def delete_traveler(
        traveler_id: int, 
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_active_user)
    ):
        """Delete a traveler"""
        # Check if traveler exists and belongs to user
        existing = db.execute(
            text("SELECT * FROM travelers WHERE id = :id AND user_id = :user_id"),
            {"id": traveler_id, "user_id": current_user["id"]}
        ).fetchone()
        
        if not existing:
            raise HTTPException(status_code=404, detail="Traveler not found")
        
        db.execute(
            text("DELETE FROM travelers WHERE id = :id AND user_id = :user_id"),
            {"id": traveler_id, "user_id": current_user["id"]}
        )
        db.commit()
        
        return {"message": "Traveler deleted successfully"}
else:
    router = None