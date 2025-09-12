import pytest
from datetime import date, timedelta
from src.repository.contacts import (
    create_contact,
    get_contacts,
    get_contact_by_id,
    get_contact_by_email,
    update_contact,
    remove_contact,
    search_contacts,
    get_upcoming_birthdays,
)
from src.schemas.contacts import ContactCreate, ContactUpdate


class TestContactsCRUD:
    """A collection of tests for contact CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_contact(self, session, owner):
        """Tests successful contact creation."""
        contact_data = ContactCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="+1234567890",
            birthday=date(1990, 1, 1),
        )
        contact = await create_contact(contact_data, owner.id, session)
        assert contact.first_name == "John"
        assert contact.email == "john@example.com"
        assert contact.owner_id == owner.id

    @pytest.mark.asyncio
    async def test_get_contacts(self, session, owner):
        """Tests successful retrieval of a list of contacts."""
        contacts_data = [
            ContactCreate(
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                phone="+111",
                birthday=date(1990, 1, 1),
            ),
            ContactCreate(
                first_name="Jane",
                last_name="Smith",
                email="jane@example.com",
                phone="+222",
                birthday=date(1991, 2, 2),
            ),
        ]
        for contact_data in contacts_data:
            await create_contact(contact_data, owner.id, session)
        contacts = await get_contacts(0, 10, owner.id, session)
        assert len(contacts) == 2

    @pytest.mark.asyncio
    async def test_get_contact_by_id_found(self, session, owner):
        """Tests successful retrieval of a contact by its ID."""
        contact_data = ContactCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="+111",
            birthday=date(1990, 1, 1),
        )
        created_contact = await create_contact(contact_data, owner.id, session)
        contact = await get_contact_by_id(created_contact.id, owner.id, session)
        assert contact is not None
        assert contact.email == "john@example.com"

    @pytest.mark.asyncio
    async def test_get_contact_by_id_not_found(self, session, owner):
        """Tests retrieval of a non-existent contact by ID."""
        contact = await get_contact_by_id(999, owner.id, session)
        assert contact is None

    @pytest.mark.asyncio
    async def test_get_contact_by_email_found(self, session, owner):
        """Tests successful retrieval of a contact by its email address."""
        contact_data = ContactCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="+111",
            birthday=date(1990, 1, 1),
        )
        await create_contact(contact_data, owner.id, session)
        contact = await get_contact_by_email("john@example.com", owner.id, session)
        assert contact is not None
        assert contact.email == "john@example.com"

    @pytest.mark.asyncio
    async def test_update_contact_full(self, session, owner):
        """Tests a full update of an existing contact."""
        contact_data = ContactCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="+111",
            birthday=date(1990, 1, 1),
        )
        created_contact = await create_contact(contact_data, owner.id, session)
        update_data = ContactUpdate(
            first_name="Johnny",
            last_name="Doe",
            email="johnny@example.com",
            phone="+222",
            birthday=date(1991, 2, 2),
        )
        updated_contact = await update_contact(
            created_contact.id, owner.id, update_data, session
        )
        assert updated_contact.first_name == "Johnny"
        assert updated_contact.email == "johnny@example.com"

    @pytest.mark.asyncio
    async def test_update_contact_partial(self, session, owner):
        """Tests a partial update of an existing contact."""
        contact_data = ContactCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="+111",
            birthday=date(1990, 1, 1),
        )
        created_contact = await create_contact(contact_data, owner.id, session)
        update_data = ContactUpdate(
            first_name="Johnny",
            last_name="Doe",
            email="john@example.com",
            phone="+111",
            birthday=date(1990, 1, 1),
        )
        updated_contact = await update_contact(
            created_contact.id, owner.id, update_data, session
        )
        assert updated_contact.first_name == "Johnny"
        assert updated_contact.last_name == "Doe"

    @pytest.mark.asyncio
    async def test_remove_contact(self, session, owner):
        """Tests successful removal of a contact."""
        contact_data = ContactCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="+111",
            birthday=date(1990, 1, 1),
        )
        created_contact = await create_contact(contact_data, owner.id, session)
        removed_contact = await remove_contact(created_contact.id, owner.id, session)
        assert removed_contact is not None
        contact = await get_contact_by_id(created_contact.id, owner.id, session)
        assert contact is None


class TestContactsSearch:
    """A collection of tests for contact search and upcoming birthdays retrieval."""

    @pytest.mark.asyncio
    async def test_search_contacts(self, session, owner):
        """Tests successful contact search by name and email."""
        contacts_data = [
            ContactCreate(
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                phone="+111",
                birthday=date(1990, 1, 1),
            ),
            ContactCreate(
                first_name="Jane",
                last_name="Smith",
                email="jane@example.com",
                phone="+222",
                birthday=date(1991, 2, 2),
            ),
        ]
        for contact_data in contacts_data:
            await create_contact(contact_data, owner.id, session)
        results = await search_contacts("John", owner.id, 0, 10, session)
        assert len(results) == 1
        assert results[0].first_name == "John"
        results = await search_contacts("example.com", owner.id, 0, 10, session)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_contacts_no_match(self, session, owner):
        """Tests a search that returns no matching contacts."""
        contact_data = ContactCreate(
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com",
            phone="+111",
            birthday=date(1990, 1, 1),
        )
        await create_contact(contact_data, owner.id, session)

        results = await search_contacts("xyz", owner.id, 0, 10, session)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_get_upcoming_birthdays(self, session, owner):
        """Tests successful retrieval of contacts with upcoming birthdays."""
        today = date.today()
        contacts_data = [
            ContactCreate(
                first_name="Birthday",
                last_name="Today",
                email="today@example.com",
                phone="+111",
                birthday=today,
            ),
            ContactCreate(
                first_name="Birthday",
                last_name="Tomorrow",
                email="tomorrow@example.com",
                phone="+222",
                birthday=today + timedelta(days=1),
            ),
            ContactCreate(
                first_name="Birthday",
                last_name="NextWeek",
                email="nextweek@example.com",
                phone="+333",
                birthday=today + timedelta(days=7),
            ),
        ]
        for contact_data in contacts_data:
            await create_contact(contact_data, owner.id, session)
        birthdays = await get_upcoming_birthdays(owner.id, session)
        assert len(birthdays) >= 2

    @pytest.mark.asyncio
    async def test_get_upcoming_birthdays_across_year(
        self, session, owner, monkeypatch
    ):
        """Tests retrieving upcoming birthdays that span across the end of the year."""
        mock_today = date(2025, 12, 29)

        class MockDate(date):
            @classmethod
            def today(cls):
                return mock_today

        import src.repository.contacts as contacts_module

        monkeypatch.setattr(contacts_module, "date", MockDate)

        await create_contact(
            ContactCreate(
                first_name="ThisYear",
                last_name="Test",
                email="t@t.com",
                phone="+1",
                birthday=date(1990, 12, 31),
            ),
            owner.id,
            session,
        )
        await create_contact(
            ContactCreate(
                first_name="NextYear",
                last_name="Test",
                email="n@n.com",
                phone="+2",
                birthday=date(1990, 1, 3),
            ),
            owner.id,
            session,
        )

        upcoming_birthdays = await contacts_module.get_upcoming_birthdays(
            owner.id, session
        )
        names = sorted([c.first_name for c in upcoming_birthdays])
        assert names == ["NextYear", "ThisYear"]


class TestContactsOwnership:
    """A collection of tests for owner isolation and access errors."""

    @pytest.mark.asyncio
    async def test_get_contact_by_id_wrong_owner(self, session, owner, another_owner):
        """Tests that a contact cannot be retrieved by a user who is not its owner."""
        contact_data = ContactCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="+111",
            birthday=date(1990, 1, 1),
        )
        created_contact = await create_contact(contact_data, owner.id, session)
        contact = await get_contact_by_id(created_contact.id, another_owner.id, session)
        assert contact is None

    @pytest.mark.asyncio
    async def test_update_contact_not_found(self, session, owner):
        """Tests that a non-existent contact cannot be updated."""
        update_data = ContactUpdate(
            first_name="NonExistent",
            last_name="User",
            email="nonexistent@example.com",
            phone="+111",
            birthday=date(1990, 1, 1),
        )
        updated_contact = await update_contact(999, owner.id, update_data, session)
        assert updated_contact is None

    @pytest.mark.asyncio
    async def test_update_contact_wrong_owner(self, session, owner, another_owner):
        """Tests that a contact cannot be updated by a user who is not its owner."""
        contact_data = ContactCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="+111",
            birthday=date(1990, 1, 1),
        )
        created_contact = await create_contact(contact_data, owner.id, session)
        update_data = ContactUpdate(
            first_name="Updated",
            last_name="Doe",
            email="john@example.com",
            phone="+111",
            birthday=date(1990, 1, 1),
        )
        updated_contact = await update_contact(
            created_contact.id, another_owner.id, update_data, session
        )
        assert updated_contact is None

    @pytest.mark.asyncio
    async def test_remove_contact_not_found(self, session, owner):
        """Tests that a non-existent contact cannot be removed."""
        removed_contact = await remove_contact(999, owner.id, session)
        assert removed_contact is None

    @pytest.mark.asyncio
    async def test_remove_contact_wrong_owner(self, session, owner, another_owner):
        """Tests that a contact cannot be removed by a user who is not its owner."""
        contact_data = ContactCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="+111",
            birthday=date(1990, 1, 1),
        )
        created_contact = await create_contact(contact_data, owner.id, session)
        removed_contact = await remove_contact(
            created_contact.id, another_owner.id, session
        )
        assert removed_contact is None

    @pytest.mark.asyncio
    async def test_contacts_owner_isolation(self, session, owner, another_owner):
        """Tests that contacts are isolated to their respective owners."""
        await create_contact(
            ContactCreate(
                first_name="Alice",
                last_name="Test",
                email="alice@owner1.com",
                phone="+123",
                birthday=date(1990, 1, 1),
            ),
            owner.id,
            session,
        )
        await create_contact(
            ContactCreate(
                first_name="Bob",
                last_name="Test",
                email="bob@owner2.com",
                phone="+456",
                birthday=date(1990, 1, 1),
            ),
            another_owner.id,
            session,
        )

        contacts_owner1 = await get_contacts(0, 10, owner.id, session)
        assert len(contacts_owner1) == 1
        assert contacts_owner1[0].email == "alice@owner1.com"

        contact_from_owner2 = await get_contact_by_email(
            "bob@owner2.com", owner.id, session
        )
        assert contact_from_owner2 is None
