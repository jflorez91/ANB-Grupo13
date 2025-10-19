from pydantic import BaseModel
from typing import Optional

class RankingResponse(BaseModel):
    position: int
    username: str
    city: str
    votes: int
    player_id: Optional[str] = None

    class Config:
        from_attributes = True