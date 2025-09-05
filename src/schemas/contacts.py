from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class ContactBase(BaseModel):
    """
    Base Pydantic model for contact data.

    This class defines the fundamental fields for a contact and is used for data validation
    and serialization.
    """

    first_name: str = Field(max_length=50)
    last_name: str = Field(max_length=50)
    email: EmailStr
    phone: str = Field(max_length=50)
    birthday: date
    additional_data: Optional[str] = Field(default=None, max_length=255)


class ContactCreate(ContactBase):
    """
    Pydantic model for creating a new contact.

    It inherits all fields from ContactBase.
    """

    pass


class ContactUpdate(BaseModel):
    """
    Pydantic model for updating an existing contact.

    All fields are optional to allow for partial updates (PATCH requests).
    """

    first_name: Optional[str] = Field(default=None, max_length=50)
    last_name: Optional[str] = Field(default=None, max_length=50)
    email: Optional[EmailStr]
    phone: Optional[str] = Field(default=None, max_length=50)
    birthday: Optional[date]
    additional_data: Optional[str] = Field(default=None, max_length=255)


class ContactResponse(ContactBase):
    """
    Pydantic model for the API response.

    Includes the contact's ID from the database and inherits all fields
    from ContactBase. The `from_attributes=True` setting is essential for
    mapping the SQLAlchemy model fields to the Pydantic model.
    """

    id: int
    model_config = ConfigDict(from_attributes=True)
