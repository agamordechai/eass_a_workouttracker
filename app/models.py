from pydantic import BaseModel
from typing import Optional

class Exercise(BaseModel):
    name: str
    sets: int
    reps: int
    weight: Optional[float] = None

class ExerciseResponse(BaseModel):
    id: int
    name: str
    sets: int
    reps: int
    weight: Optional[float] = None

class ExerciseEditRequest(BaseModel):
    name: Optional[str] = None
    sets: Optional[int] = None
    reps: Optional[int] = None
    weight: Optional[float] = None
