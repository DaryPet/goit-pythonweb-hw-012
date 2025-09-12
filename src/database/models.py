from datetime import date, datetime
from sqlalchemy import String, Date, Boolean, func, ForeignKey, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


class UserRole(enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class Base(DeclarativeBase):
    """Basic class for all ORM"""

    pass


class User(Base):
    """
    SQLAlchemy model for the 'users' table.
    Stores user information including authentication data and roles.
    """

    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    """The unique identifier for the user."""
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    """The user's email address, used for login and verification."""
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    """The hashed password for user authentication."""
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    """A flag indicating whether the user's email has been verified."""
    avatar_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    """The URL to the user's avatar image."""
    refresh_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    """The refresh token for maintaining user sessions."""
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER)
    """The user's role (e.g., USER or ADMIN)."""
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    """The timestamp when the user account was created."""
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )
    """The timestamp of the last update to the user's account."""

    contacts: Mapped[list["Contact"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    """A collection of contacts owned by this user."""


class Contact(Base):
    """
    SQLAlchemy model for the 'contacts' table.

    This model defines the table structure in the database, including the columns
    and their properties, for storing contact information.
    """

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    """The unique identifier for the contact."""
    first_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    """The first name of the contact."""
    last_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    """The last name of the contact."""
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    """The contact's email address."""
    phone: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    """The contact's phone number."""
    birthday: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    """The contact's birthday."""
    additional_data: Mapped[str | None] = mapped_column(String(255), nullable=True)
    """Additional information about the contact."""
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    """The foreign key linking the contact to its owner."""
    owner: Mapped["User"] = relationship(back_populates="contacts")
    """The owner of the contact, linked via a relationship."""
