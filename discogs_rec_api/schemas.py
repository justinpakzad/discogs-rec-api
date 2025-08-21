from pydantic import BaseModel, Field, EmailStr, ConfigDict
from datetime import datetime
from typing import Annotated
import uuid


class UserBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: Annotated[
        str,
        Field(
            min_length=2, max_length=20, pattern=r"^[a-z0-9]+$", examples=["userson"]
        ),
    ]
    email: Annotated[EmailStr, Field(examples=["user.userson@example.com"])]


class UserCreate(UserBase):
    password: Annotated[str, Field(min_length=8, max_length=32)]


class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool = True
    created_at: datetime


class UserAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    username: str
    email: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime


class AdminListUsers(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    users: list[UserAdminResponse]
    user_count: int


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class RecommendationRequest(BaseModel):
    url: str
    n_recs: int = 5


class RecommendationRequestBatch(BaseModel):
    urls: list[str]
    n_recs: int = 5


class RecommendationResponseData(BaseModel):
    url: str
    artist_name: str
    release_title: str
    label_name: str


class InputInfo(BaseModel):
    release_id: int
    url: str


class RecommendationResponse(BaseModel):
    search_id: int | None = None
    recommendations: list[RecommendationResponseData]


class RecommendationResponseBatch(BaseModel):
    search_id: int | None = None
    input_data: InputInfo
    recommendations: list[RecommendationResponseData]


class Recommendations(BaseModel):
    id: int
    release_id: int


class FeedbackRequest(BaseModel):
    recommendation_rank: int = Field(ge=1, le=5)
    familiarity_rank: int = Field(ge=1, le=5)
    missing_release_reported: bool = False


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: uuid.UUID
    search_id: int
    created_at: datetime
    recommendation_rank: int
    familiarity_rank: int
    missing_release_reported: bool
