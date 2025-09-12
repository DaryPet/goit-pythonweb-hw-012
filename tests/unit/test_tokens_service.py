import pytest
from jose import jwt, JWTError
from src.security import tokens
from src.conf.config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM


class TestAccessToken:
    """A collection of tests for the tokens.create_access_token function."""

    @pytest.mark.parametrize("minutes", [None, 5, 60])
    def test_structure(self, minutes):
        """Tests the structure of the access token."""
        sub = "123"
        token = tokens.create_access_token(sub=sub, minutes=minutes)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert decoded["sub"] == str(sub)
        assert decoded["token_type"] == "access"
        assert "iat" in decoded
        assert "exp" in decoded
        assert decoded["exp"] > decoded["iat"]


class TestRefreshToken:
    """A collection of tests for the tokens.create_refresh_token function."""

    @pytest.mark.parametrize("days", [None, 1, 7])
    def test_structure(self, days):
        """Tests the structure of the refresh token."""
        sub = "456"
        token = tokens.create_refresh_token(sub=sub, days=days)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert decoded["sub"] == str(sub)
        assert decoded["token_type"] == "refresh"
        assert "iat" in decoded
        assert "exp" in decoded
        assert decoded["exp"] > decoded["iat"]


class TestEmailToken:
    """A collection of tests for the tokens.create_email_token function."""

    def test_structure(self):
        """Tests the structure of the email verification token."""
        sub = "email@example.com"
        token = tokens.create_email_token(sub)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert decoded["sub"] == str(sub)
        assert decoded["token_type"] == "email_verification"
        assert "iat" in decoded
        assert "exp" in decoded
        assert decoded["exp"] > decoded["iat"]


class TestPasswordResetToken:
    """A collection of tests for the tokens.create_password_reset_token function."""

    def test_structure(self):
        """Tests the structure of the password reset token."""
        sub = "reset@example.com"
        token = tokens.create_password_reset_token(sub)
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert decoded["sub"] == str(sub)
        assert decoded["token_type"] == "password_reset"
        assert "iat" in decoded
        assert "exp" in decoded
        assert decoded["exp"] > decoded["iat"]


class TestTokenExpiry:
    """A collection of tests for checking token expiration differences."""

    def test_tokens_have_different_expiry(self):
        """Tests that different token types have different expiration times."""
        access_token = tokens.create_access_token("1")
        refresh_token = tokens.create_refresh_token("1")
        email_token = tokens.create_email_token("1")
        reset_token = tokens.create_password_reset_token("1")

        decoded_access = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        decoded_refresh = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        decoded_email = jwt.decode(email_token, SECRET_KEY, algorithms=[ALGORITHM])
        decoded_reset = jwt.decode(reset_token, SECRET_KEY, algorithms=[ALGORITHM])

        assert decoded_access["exp"] != decoded_refresh["exp"]
        assert decoded_email["exp"] != decoded_reset["exp"]


class TestInvalidJWT:
    """A collection of tests for handling invalid JWTs."""

    def test_invalid_jwt_raises(self):
        """Tests that an invalid JWT raises a JWTError."""
        invalid_token = "not_a_real_token"
        with pytest.raises(JWTError):
            jwt.decode(invalid_token, SECRET_KEY, algorithms=[ALGORITHM])
