import uuid
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import String, TIMESTAMP, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone


class Base(DeclarativeBase):
    pass


class Users(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        index=True,
        default=uuid.uuid4,
    )
    username: Mapped[str] = mapped_column(String(), index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.now(timezone.utc), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    is_superuser: Mapped[bool] = mapped_column(nullable=False, default=False)

    searches: Mapped[list["Searches"]] = relationship(back_populates="user")
    favorites: Mapped[list["Favorites"]] = relationship(back_populates="user")
    feedback: Mapped[list["Feedback"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email}, is_active={self.is_active})"


class Releases(Base):
    __tablename__ = "releases"
    id: Mapped[int] = mapped_column(
        Integer(), nullable=False, primary_key=True, index=True
    )
    artist_name: Mapped[str] = mapped_column(String(), nullable=False)
    styles: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    release_title: Mapped[str] = mapped_column(String(), nullable=False)
    country: Mapped[str | None] = mapped_column(String(), nullable=True)
    catno: Mapped[str | None] = mapped_column(String(), nullable=True)
    label_name: Mapped[str | None] = mapped_column(String(), nullable=True)
    release_year: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    want: Mapped[float | None] = mapped_column(Float(), nullable=True)
    have: Mapped[float | None] = mapped_column(Float(), nullable=True)
    want_to_have_ratio: Mapped[float | None] = mapped_column(Float(), nullable=True)
    video_count: Mapped[float | None] = mapped_column(Float(), nullable=True)
    low: Mapped[float | None] = mapped_column(Float(), nullable=True)
    median: Mapped[float | None] = mapped_column(Float(), nullable=True)
    high: Mapped[float | None] = mapped_column(Float(), nullable=True)

    recommendations: Mapped[list["Recommendations"]] = relationship(
        back_populates="release"
    )
    favorites: Mapped[list["Favorites"]] = relationship(back_populates="release")


class Searches(Base):
    __tablename__ = "searches"
    id: Mapped[int] = mapped_column(
        Integer(), primary_key=True, nullable=False, index=True, autoincrement=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    release_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.now(timezone.utc), nullable=False
    )

    user: Mapped["Users"] = relationship(back_populates="searches")
    recommendations: Mapped[list["Recommendations"]] = relationship(
        back_populates="search"
    )
    feedback: Mapped["Feedback"] = relationship(back_populates="search")


class Recommendations(Base):
    __tablename__ = "recommendations"
    id: Mapped[int] = mapped_column(
        Integer(), primary_key=True, nullable=False, index=True, autoincrement=True
    )
    search_id: Mapped[int] = mapped_column(
        Integer(), ForeignKey("searches.id"), nullable=False, index=True
    )
    release_id: Mapped[int] = mapped_column(
        Integer(), ForeignKey("releases.id"), nullable=False, index=True
    )

    search: Mapped["Searches"] = relationship(back_populates="recommendations")
    release: Mapped["Releases"] = relationship(back_populates="recommendations")


class Favorites(Base):
    __tablename__ = "favorites"
    id: Mapped[int] = mapped_column(
        Integer(), primary_key=True, nullable=False, index=True, autoincrement=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    release_id: Mapped[int] = mapped_column(
        Integer(), ForeignKey("releases.id"), nullable=False, index=True
    )
    release: Mapped["Releases"] = relationship(back_populates="favorites")
    user: Mapped["Users"] = relationship(back_populates="favorites")


class Feedback(Base):
    __tablename__ = "feedback"
    id: Mapped[int] = mapped_column(
        Integer(), primary_key=True, nullable=False, index=True, autoincrement=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    search_id: Mapped[int] = mapped_column(
        Integer(), ForeignKey("searches.id"), nullable=False, index=True
    )

    # 0-5 scale for  quality
    recommendation_rank: Mapped[int] = mapped_column(
        Integer(),
        nullable=False,
    )
    familiarity_rank: Mapped[int | None] = mapped_column(
        Integer(),
        nullable=True,
    )

    missing_release_reported: Mapped[bool] = mapped_column(nullable=True, default=False)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.now(timezone.utc), nullable=False
    )

    user: Mapped["Users"] = relationship(back_populates="feedback")
    search: Mapped["Searches"] = relationship(back_populates="feedback")
