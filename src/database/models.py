from datetime import date
from sqlalchemy import String, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """Basic class for all ORM"""
    pass

class Contact(Base):
    """
    SQLAlchemy model for the 'contacts' table.

    This model defines the table structure in the database, including the columns
    and their properties, for storing contact information.
    """
    __tablename__="contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    birthday: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    additional_data: Mapped[str | None] = mapped_column(String(255), nullable=True)
