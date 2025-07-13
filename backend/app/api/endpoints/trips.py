"""
Trips API endpoints with database integration
"""
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

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


# Pydantic models for trips
class TripBase(BaseModel):
    title: str
    destination: str
    start_date: date
    end_date: date
    status: str = "planning"
    budget: Optional[float] = None
    notes: Optional[str] = None


class TripCreate(TripBase):
    pass


class TripUpdate(BaseModel):
    title: Optional[str] = None
    destination: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None
    budget: Optional[float] = None
    notes: Optional[str] = None


class Trip(TripBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Create router only if FastAPI is available
if FASTAPI_AVAILABLE:
    router = APIRouter(prefix="/trips", tags=["trips"])
    
    @router.get("/", response_model=List[Trip])
    def get_trips(
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_active_user)
    ):
        """Get all trips for the current user"""
        # Filter trips by authenticated user
        from sqlalchemy import text
        query = db.execute(
            text("SELECT * FROM trips WHERE user_id = :user_id ORDER BY created_at DESC LIMIT :limit OFFSET :skip"),
            {"user_id": current_user["id"], "limit": limit, "skip": skip}
        )
        trips = query.fetchall()
        
        # Convert to dict format
        result = []
        for trip in trips:
            result.append({
                "id": trip[0],
                "user_id": trip[1],
                "title": trip[2],
                "destination": trip[3],
                "start_date": trip[4],
                "end_date": trip[5],
                "status": trip[6],
                "budget": trip[7],
                "notes": trip[8],
                "created_at": trip[9],
                "updated_at": trip[10]
            })
        
        return result
    
    @router.post("/", response_model=Trip)
    def create_trip(
        trip: TripCreate, 
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_active_user)
    ):
        """Create a new trip"""
        user_id = current_user["id"]
        
        from sqlalchemy import text
        cursor = db.execute(
            text("""
            INSERT INTO trips (user_id, title, destination, start_date, end_date, status, budget, notes, created_at)
            VALUES (:user_id, :title, :destination, :start_date, :end_date, :status, :budget, :notes, datetime('now'))
            """),
            {
                "user_id": user_id,
                "title": trip.title,
                "destination": trip.destination,
                "start_date": str(trip.start_date),
                "end_date": str(trip.end_date),
                "status": trip.status,
                "budget": trip.budget,
                "notes": trip.notes
            }
        )
        db.commit()
        
        trip_id = cursor.lastrowid
        
        # Fetch the created trip
        result = db.execute(text("SELECT * FROM trips WHERE id = :id"), {"id": trip_id}).fetchone()
        
        return {
            "id": result[0],
            "user_id": result[1],
            "title": result[2],
            "destination": result[3],
            "start_date": result[4],
            "end_date": result[5],
            "status": result[6],
            "budget": result[7],
            "notes": result[8],
            "created_at": result[9],
            "updated_at": result[10]
        }
    
    @router.get("/{trip_id}", response_model=Trip)
    def get_trip(
        trip_id: int, 
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_active_user)
    ):
        """Get a specific trip by ID"""
        from sqlalchemy import text
        result = db.execute(
            text("SELECT * FROM trips WHERE id = :id AND user_id = :user_id"),
            {"id": trip_id, "user_id": current_user["id"]}
        ).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Trip not found")
        
        return {
            "id": result[0],
            "user_id": result[1],
            "title": result[2],
            "destination": result[3],
            "start_date": result[4],
            "end_date": result[5],
            "status": result[6],
            "budget": result[7],
            "notes": result[8],
            "created_at": result[9],
            "updated_at": result[10]
        }
    
    @router.put("/{trip_id}", response_model=Trip)
    def update_trip(
        trip_id: int, 
        trip: TripUpdate, 
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_active_user)
    ):
        """Update a trip"""
        from sqlalchemy import text
        # Check if trip exists and belongs to user
        existing = db.execute(
            text("SELECT * FROM trips WHERE id = :id AND user_id = :user_id"),
            {"id": trip_id, "user_id": current_user["id"]}
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Trip not found")
        
        # Build update query dynamically
        updates = []
        values = []
        
        if trip.title is not None:
            updates.append("title = ?")
            values.append(trip.title)
        if trip.destination is not None:
            updates.append("destination = ?")
            values.append(trip.destination)
        if trip.start_date is not None:
            updates.append("start_date = ?")
            values.append(str(trip.start_date))
        if trip.end_date is not None:
            updates.append("end_date = ?")
            values.append(str(trip.end_date))
        if trip.status is not None:
            updates.append("status = ?")
            values.append(trip.status)
        if trip.budget is not None:
            updates.append("budget = ?")
            values.append(trip.budget)
        if trip.notes is not None:
            updates.append("notes = ?")
            values.append(trip.notes)
        
        if updates:
            updates.append("updated_at = datetime('now')")
            values.append(trip_id)
            
            query = f"UPDATE trips SET {', '.join(updates)} WHERE id = :trip_id AND user_id = :user_id"
            params = {f"val{i}": v for i, v in enumerate(values)}
            params["trip_id"] = trip_id
            params["user_id"] = current_user["id"]
            
            # Build parameterized query
            parameterized_updates = []
            for i, update in enumerate(updates[:-1]):  # Exclude 'updated_at'
                param_name = f"val{i}"
                parameterized_updates.append(update.replace("?", f":{param_name}"))
            parameterized_updates.append(updates[-1])  # Add 'updated_at'
            
            query = f"UPDATE trips SET {', '.join(parameterized_updates)} WHERE id = :trip_id AND user_id = :user_id"
            db.execute(text(query), params)
            db.commit()
        
        # Return updated trip
        result = db.execute(
            text("SELECT * FROM trips WHERE id = :id AND user_id = :user_id"),
            {"id": trip_id, "user_id": current_user["id"]}
        ).fetchone()
        
        return {
            "id": result[0],
            "user_id": result[1],
            "title": result[2],
            "destination": result[3],
            "start_date": result[4],
            "end_date": result[5],
            "status": result[6],
            "budget": result[7],
            "notes": result[8],
            "created_at": result[9],
            "updated_at": result[10]
        }
    
    @router.delete("/{trip_id}")
    def delete_trip(
        trip_id: int, 
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_active_user)
    ):
        """Delete a trip"""
        from sqlalchemy import text
        # Check if trip exists and belongs to user
        existing = db.execute(
            text("SELECT * FROM trips WHERE id = :id AND user_id = :user_id"),
            {"id": trip_id, "user_id": current_user["id"]}
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Trip not found")
        
        db.execute(
            text("DELETE FROM trips WHERE id = :id AND user_id = :user_id"),
            {"id": trip_id, "user_id": current_user["id"]}
        )
        db.commit()
        
        return {"message": "Trip deleted successfully"}
else:
    router = None