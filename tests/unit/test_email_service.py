import pytest
from unittest.mock import patch, AsyncMock
from fastapi import HTTPException
from src.services import email as email_service


class TestSendVerificationEmail:
    """A collection of tests for the email_service.send_verification_email function."""

    @pytest.mark.asyncio
    async def test_success(self):
        """Tests the successful sending of a verification email."""
        email = "test@example.com"
        username = "user1"
        host = "localhost"

        with patch(
            "src.security.tokens.create_email_token", return_value="dummy_token"
        ):
            with patch(
                "fastapi_mail.FastMail.send_message", new_callable=AsyncMock
            ) as mock_send:
                await email_service.send_verification_email(email, username, host)
                mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_failure(self):
        """Tests an error during the sending of a verification email."""
        email = "test@example.com"
        username = "user1"
        host = "localhost"

        with patch(
            "src.security.tokens.create_email_token", return_value="dummy_token"
        ):
            with patch(
                "fastapi_mail.FastMail.send_message",
                new_callable=AsyncMock,
                side_effect=Exception("fail"),
            ):
                with pytest.raises(HTTPException) as exc_info:
                    await email_service.send_verification_email(email, username, host)
                assert exc_info.value.status_code == 500
                assert "Failed to send verification email" in exc_info.value.detail


class TestSendPasswordResetEmail:
    """A collection of tests for the email_service.send_password_reset_email function."""

    @pytest.mark.asyncio
    async def test_success(self):
        """Tests the successful sending of a password reset email."""
        email = "test@example.com"
        username = "user1"
        host = "localhost"
        reset_token = "reset123"

        with patch(
            "fastapi_mail.FastMail.send_message", new_callable=AsyncMock
        ) as mock_send:
            await email_service.send_password_reset_email(
                email, username, host, reset_token
            )
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_failure(self):
        """Tests an error during the sending of a password reset email."""
        email = "test@example.com"
        username = "user1"
        host = "localhost"
        reset_token = "reset123"

        with patch(
            "fastapi_mail.FastMail.send_message",
            new_callable=AsyncMock,
            side_effect=Exception("fail"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await email_service.send_password_reset_email(
                    email, username, host, reset_token
                )
            assert exc_info.value.status_code == 500
            assert "Failed to send password reset email" in exc_info.value.detail
