from src.security import passwords as password_service


class TestPasswordHash:
    """A collection of tests for the password_service.get_password_hash function."""

    def test_returns_string(self):
        """Tests that the hash returns a string and is different from the original password."""
        password = "mysecret"
        hashed = password_service.get_password_hash(password)
        assert isinstance(hashed, str)
        assert hashed != password


class TestVerifyPassword:
    """A collection of tests for the password_service.verify_password function."""

    def test_success(self):
        """Tests that a password is successfully verified when it matches the hash."""
        password = "mysecret"
        hashed = password_service.get_password_hash(password)
        assert password_service.verify_password(password, hashed) is True

    def test_failure(self):
        """Tests that a password fails verification when it does not match the hash."""
        password = "mysecret"
        wrong_password = "notmypassword"
        hashed = password_service.get_password_hash(password)
        assert password_service.verify_password(wrong_password, hashed) is False
