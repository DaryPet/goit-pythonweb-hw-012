from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy import select, or_, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact
from src.schemas.contacts import ContactCreate, ContactUpdate


async def create_contact(
    body: ContactCreate, owner_id: int, db: AsyncSession
) -> Contact:
    """
    Creates a new contact in the database.

    :param body: The data for the new contact.
    :param db: The database session.
    :return: The newly created contact object.
    """

    contact = Contact(**body.model_dump(), owner_id=owner_id)
    db.add(contact)
    await db.flush()
    await db.refresh(contact)
    return contact


async def get_contacts(
    skip: int, limit: int, owner_id: int, db: AsyncSession
) -> List[Contact]:
    """
    Retrieves a list of contacts with pagination.

    :param skip: The number of contacts to skip.
    :param limit: The maximum number of contacts to return.
    :param db: The database session.
    :return: A list of contact objects.
    """

    stmt = (
        select(Contact)
        .where(Contact.owner_id == owner_id)
        .order_by(Contact.id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_contact_by_id(
    contact_id: int, owner_id: int, db: AsyncSession
) -> Optional[Contact]:
    """
    Retrieves a single contact by its ID.

    :param contact_id: The ID of the contact to retrieve.
    :param db: The database session.
    :return: The contact object, or None if not found.
    """

    stmt = select(Contact).where(Contact.id == contact_id, Contact.owner_id == owner_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_contact_by_email(
    email: str, owner_id: int, db: AsyncSession
) -> Optional[Contact]:
    """
    Retrieves a single contact by its email address.

    :param email: The email of the contact to retrieve.
    :param db: The database session.
    :return: The contact object, or None if not found.
    """
    stmt = select(Contact).where(Contact.email == email, Contact.owner_id == owner_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_contact(
    contact_id: int, owner_id: int, body: ContactUpdate, db: AsyncSession
) -> Optional[Contact]:
    """
    Updates an existing contact's information.
    Only updates the fields provided in the body.

    :param contact_id: The ID of the contact to update.
    :param body: The data to update the contact with.
    :param db: The database session.
    :return: The updated contact object, or None if not found.
    """

    contact = await get_contact_by_id(contact_id, owner_id, db)
    if not contact:
        return None

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(contact, key, value)

    await db.flush()
    await db.refresh(contact)
    return contact


async def remove_contact(
    contact_id: int, owner_id: int, db: AsyncSession
) -> Optional[Contact]:
    """
    Removes a contact from the database.

    :param contact_id: The ID of the contact to remove.
    :param db: The database session.
    :return: The removed contact object, or None if not found.
    """

    contact = await get_contact_by_id(contact_id, owner_id, db)
    if not contact:
        return None

    await db.delete(contact)
    return contact


async def search_contacts(
    query: str,
    owner_id: int,
    skip: int,
    limit: int,
    db: AsyncSession,
) -> List[Contact]:
    """
    Searches for contacts by a query string in first name, last name, or email.

    :param query: The search query string.
    :param skip: The number of contacts to skip for pagination.
    :param limit: The maximum number of contacts to return.
    :param db: The database session.
    :return: A list of found contact objects.
    """

    stmt = (
        select(Contact)
        .where(
            and_(
                Contact.owner_id == owner_id,
                or_(
                    Contact.first_name.ilike(f"%{query}%"),
                    Contact.last_name.ilike(f"%{query}%"),
                    Contact.email.ilike(f"%{query}%"),
                ),
            )
        )
        .order_by(Contact.id)
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_upcoming_birthdays(owner_id: int, db: AsyncSession) -> List[Contact]:
    """
    Retrieves contacts with birthdays in the next 7 days.

    :param db: The database session.
    :return: A list of contacts with upcoming birthdays.
    """

    today = date.today()
    end_date = today + timedelta(days=7)

    start_doy = today.timetuple().tm_yday
    end_doy = end_date.timetuple().tm_yday

    stmt = select(Contact).where(Contact.owner_id == owner_id)

    if start_doy <= end_doy:
        stmt = stmt.where(
            and_(
                extract("doy", Contact.birthday) >= start_doy,
                extract("doy", Contact.birthday) <= end_doy,
            )
        )
    else:
        stmt = stmt.where(
            or_(
                extract("doy", Contact.birthday) >= start_doy,
                extract("doy", Contact.birthday) <= end_doy,
            )
        )

    stmt = stmt.order_by(
        extract("doy", Contact.birthday), Contact.last_name, Contact.first_name
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
