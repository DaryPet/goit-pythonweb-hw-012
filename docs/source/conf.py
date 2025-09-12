# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys
from unittest.mock import MagicMock

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

autodoc_mock_imports = [
    "src.conf.config",
    "src.services.redis_service",
    "src.services.cloudinary_service",
    "src.services.email",
    "src.database.db",
    "redis.asyncio",
    "sqlalchemy",
    "fastapi",
]


class MockSettings(MagicMock):
    """
    A mock class for Pydantic settings to prevent import errors during the Sphinx build.
    """

    DB_URL = "mock"
    SECRET_KEY = "mock_secret_key"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRES_MIN = 30
    REFRESH_TOKEN_EXPIRES_DAYS = 7
    SMTP_HOST = "mock"
    SMTP_PORT = 587
    SMTP_USER = "mock"
    SMTP_PASSWORD = "mock"
    MAIL_FROM = "mock@example.com"
    REDIS_URL = "mock"
    REDIS_EXPIRES = 3600
    CLOUDINARY_CLOUD_NAME = "mock"
    CLOUDINARY_API_KEY = "mock"
    CLOUDINARY_API_SECRET = "mock"
    CORS_ORIGINS = ["*"]

    def __getattr__(self, name):
        if name == "MAIL_FROM":
            return "mock@example.com"
        return super().__getattr__(name)


sys.modules["src.conf.config"] = MockSettings()


project = "Contact-App"
copyright = "2025, Darya"
author = "Darya"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
