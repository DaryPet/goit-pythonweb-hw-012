import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import status
from httpx import AsyncClient


class TestContactsRoutes:
    """A collection of tests for contact endpoints."""

    @staticmethod
    def _create_mock_contact(**kwargs):
        """Creates a mock contact to avoid code duplication."""
        defaults = {
            "id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "birthday": "1990-01-01",
            "owner_id": 1,
            "additional_data": "test",
        }
        defaults.update(kwargs)
        return MagicMock(**defaults)

    @staticmethod
    def _get_json_data(contact):
        """Returns a dictionary of contact data for JSON requests."""
        return {
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "email": contact.email,
            "phone": contact.phone,
            "birthday": contact.birthday,
        }

    @pytest.mark.asyncio
    async def test_create_contact_success(
        self, client: AsyncClient, mock_repo_contacts: AsyncMock
    ):
        """Tests successful contact creation."""
        # Arrange
        contact_mock = self._create_mock_contact()
        mock_repo_contacts.get_contact_by_email.return_value = None
        mock_repo_contacts.create_contact.return_value = contact_mock

        # Act
        response = await client.post(
            "/api/contacts/", json=self._get_json_data(contact_mock)
        )

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["first_name"] == "John"
        assert data["email"] == "john@example.com"

    @pytest.mark.asyncio
    async def test_create_contact_email_exists(
        self, client: AsyncClient, mock_repo_contacts: AsyncMock
    ):
        """Tests contact creation with an existing email."""
        # Arrange
        existing_contact = self._create_mock_contact()
        mock_repo_contacts.get_contact_by_email.return_value = existing_contact

        # Act
        response = await client.post(
            "/api/contacts/", json=self._get_json_data(existing_contact)
        )

        # Assert
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json()["detail"] == "Contact with this email already exists."

    @pytest.mark.asyncio
    async def test_get_contacts_success(
        self, client: AsyncClient, mock_repo_contacts: AsyncMock
    ):
        """Tests successful retrieval of a list of contacts."""
        # Arrange
        contact1 = self._create_mock_contact()
        contact2 = self._create_mock_contact(
            id=2, first_name="Jane", email="jane@example.com"
        )
        mock_repo_contacts.get_contacts.return_value = [contact1, contact2]

        # Act
        response = await client.get("/api/contacts/?skip=0&limit=10")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["first_name"] == "John"
        assert data[1]["first_name"] == "Jane"

    @pytest.mark.asyncio
    async def test_get_contact_by_id_success(
        self, client: AsyncClient, mock_repo_contacts: AsyncMock
    ):
        """Tests successful retrieval of a contact by ID."""
        # Arrange
        contact_mock = self._create_mock_contact()
        mock_repo_contacts.get_contact_by_id.return_value = contact_mock

        # Act
        response = await client.get("/api/contacts/1")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["first_name"] == "John"
        assert data["email"] == "john@example.com"

    @pytest.mark.asyncio
    async def test_get_contact_by_id_not_found(
        self, client: AsyncClient, mock_repo_contacts: AsyncMock
    ):
        """Tests retrieving a non-existent contact by ID."""
        # Arrange
        mock_repo_contacts.get_contact_by_id.return_value = None

        # Act
        response = await client.get("/api/contacts/999")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Contact not found"

    @pytest.mark.asyncio
    async def test_update_contact_full_success(
        self, client: AsyncClient, mock_repo_contacts: AsyncMock
    ):
        """Tests a full update of a contact."""
        # Arrange
        updated_contact_mock = self._create_mock_contact(
            first_name="Johnny", email="johnny@example.com", phone="+2222222222"
        )
        mock_repo_contacts.update_contact.return_value = updated_contact_mock

        # Act
        response = await client.put(
            "/api/contacts/1", json=self._get_json_data(updated_contact_mock)
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["first_name"] == "Johnny"
        assert data["email"] == "johnny@example.com"

    @pytest.mark.asyncio
    async def test_update_contact_not_found(
        self, client: AsyncClient, mock_repo_contacts: AsyncMock
    ):
        """Tests updating a non-existent contact."""
        # Arrange
        mock_repo_contacts.update_contact.return_value = None

        # Act
        response = await client.put(
            "/api/contacts/999", json=self._get_json_data(self._create_mock_contact())
        )

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Contact not found"

    @pytest.mark.asyncio
    async def test_partial_update_contact_success(
        self, client: AsyncClient, mock_repo_contacts: AsyncMock
    ):
        """Tests a successful partial update of a contact."""
        # Arrange
        updated_contact_mock = self._create_mock_contact(first_name="Johnny")
        mock_repo_contacts.update_contact.return_value = updated_contact_mock

        # Act
        response = await client.patch(
            "/api/contacts/1",
            json={
                "first_name": "Johnny",
                "last_name": "Doe",
                "email": "john@example.com",
                "phone": "+1234567890",
                "birthday": "1990-01-01",
            },
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["first_name"] == "Johnny"

    @pytest.mark.asyncio
    async def test_delete_contact_success(
        self, client: AsyncClient, mock_repo_contacts: AsyncMock
    ):
        """Tests successful contact deletion."""
        # Arrange
        contact_mock = self._create_mock_contact()
        mock_repo_contacts.remove_contact.return_value = contact_mock

        # Act
        response = await client.delete("/api/contacts/1")

        # Assert
        assert response.status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.asyncio
    async def test_delete_contact_not_found(
        self, client: AsyncClient, mock_repo_contacts: AsyncMock
    ):
        """Tests deleting a non-existent contact."""
        # Arrange
        mock_repo_contacts.remove_contact.return_value = None

        # Act
        response = await client.delete("/api/contacts/999")

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Contact not found"

    @pytest.mark.asyncio
    async def test_search_contacts_success(
        self, client: AsyncClient, mock_repo_contacts: AsyncMock
    ):
        """Tests successful contact search."""
        # Arrange
        contact = self._create_mock_contact()
        mock_repo_contacts.search_contacts.return_value = [contact]

        # Act
        response = await client.get("/api/contacts/search/?query=John")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["first_name"] == "John"

    @pytest.mark.asyncio
    async def test_search_contacts_no_results(
        self, client: AsyncClient, mock_repo_contacts: AsyncMock
    ):
        """Tests a search that yields no results."""
        # Arrange
        mock_repo_contacts.search_contacts.return_value = []

        # Act
        response = await client.get("/api/contacts/search/?query=nonexistent")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_get_upcoming_birthdays_success(
        self, client: AsyncClient, mock_repo_contacts: AsyncMock
    ):
        """Tests successful retrieval of upcoming birthdays."""
        # Arrange
        contact1 = self._create_mock_contact()
        contact2 = self._create_mock_contact(
            id=2, first_name="Jane", email="jane@example.com"
        )
        mock_repo_contacts.get_upcoming_birthdays.return_value = [contact1, contact2]

        # Act
        response = await client.get("/api/contacts/birthdays/")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["first_name"] == "John"
        assert data[1]["first_name"] == "Jane"

    @pytest.mark.asyncio
    async def test_get_upcoming_birthdays_empty(
        self, client: AsyncClient, mock_repo_contacts: AsyncMock
    ):
        """Tests retrieval of upcoming birthdays when there are none."""
        # Arrange
        mock_repo_contacts.get_upcoming_birthdays.return_value = []

        # Act
        response = await client.get("/api/contacts/birthdays/")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0
