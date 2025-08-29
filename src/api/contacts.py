# src/api/contacts.py

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.repository import contacts as repository_contacts
from src.schemas import ContactCreate, ContactUpdate, ContactResponse
from src.core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/search/", response_model=List[ContactResponse])
async def search_contacts(
    query: str = Query(..., min_length=1),
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """
    Searches for contacts by first name, last name, or email.
    """
    logger.info(f"Searching for contacts with query: '{query}'")
    contacts = await repository_contacts.search_contacts(query, skip, limit, db)
    return contacts


@router.get("/birthdays/", response_model=List[ContactResponse])
async def get_upcoming_birthdays(db: AsyncSession = Depends(get_db)):
    """
    Retrieves contacts with birthdays in the next 7 days.
    """
    logger.info("Fetching upcoming birthdays.")
    contacts = await repository_contacts.get_upcoming_birthdays(db)
    return contacts

@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(body: ContactCreate, db: AsyncSession = Depends(get_db)):
    """
    Creates a new contact.
    """
    logger.info(f"Creating a new contact for email: {body.email}")
    existing_contact = await repository_contacts.get_contact_by_email(body.email, db)
    if existing_contact:
        logger.warning(f"Email {body.email} already exists.")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contact with this email already exists.",
        )
    contact = await repository_contacts.create_contact(body, db)
    return contact


@router.get("/", response_model=List[ContactResponse])
async def get_contacts(
    skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)
):
    """
    Retrieves a list of contacts with pagination.
    """
    logger.info(f"Fetching contacts with skip={skip}, limit={limit}")
    contacts = await repository_contacts.get_contacts(skip, limit, db)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieves a single contact by its ID.
    """
    logger.info(f"Fetching contact with ID: {contact_id}")
    contact = await repository_contacts.get_contact_by_id(contact_id, db)
    if contact is None:
        logger.warning(f"Contact with ID {contact_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int, body: ContactCreate, db: AsyncSession = Depends(get_db)
):
    """
    Performs a full update of a contact.
    """
    logger.info(f"Updating contact with ID: {contact_id}")
    contact = await repository_contacts.update_contact(contact_id, body, db)
    if contact is None:
        logger.warning(f"Contact with ID {contact_id} not found for full update.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.patch("/{contact_id}", response_model=ContactResponse)
async def partial_update_contact(
    contact_id: int, body: ContactUpdate, db: AsyncSession = Depends(get_db)
):
    """
    Performs a partial update of a contact.
    """
    logger.info(f"Partially updating contact with ID: {contact_id}")
    contact = await repository_contacts.update_contact(contact_id, body, db)
    if contact is None:
        logger.warning(f"Contact with ID {contact_id} not found for partial update.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    """
    Deletes a contact.
    """
    logger.info(f"Deleting contact with ID: {contact_id}")
    contact = await repository_contacts.remove_contact(contact_id, db)
    if contact is None:
        logger.warning(f"Contact with ID {contact_id} not found for deletion.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return None

