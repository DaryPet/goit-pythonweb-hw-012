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
    """The first name of the contact."""
    last_name: str = Field(max_length=50)
    """The last name of the contact."""
    email: EmailStr
    """The email address of the contact."""
    phone: str = Field(max_length=50)
    """The phone number of the contact."""
    birthday: date
    """The birthday of the contact."""
    additional_data: Optional[str] = Field(default=None, max_length=255)
    """Optional additional information about the contact."""


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
    """The new first name of the contact."""
    last_name: Optional[str] = Field(default=None, max_length=50)
    """The new last name of the contact."""
    email: Optional[EmailStr]
    """The new email address of the contact."""
    phone: Optional[str] = Field(default=None, max_length=50)
    """The new phone number of the contact."""
    birthday: Optional[date]
    """The new birthday of the contact."""
    additional_data: Optional[str] = Field(default=None, max_length=255)
    """New optional additional information about the contact."""


class ContactResponse(ContactBase):
    """
    Pydantic model for the API response.

    Includes the contact's ID from the database and inherits all fields
    from ContactBase. The `from_attributes=True` setting is essential for
    mapping the SQLAlchemy model fields to the Pydantic model.
    """

    id: int
    """The unique ID of the contact."""
    model_config = ConfigDict(from_attributes=True)
