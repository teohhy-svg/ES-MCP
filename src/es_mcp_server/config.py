"""Environment-driven server configuration."""

from __future__ import annotations

import re
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_KIBANA_SPACE_RE = re.compile(r"^[a-z0-9_-]+$")


class McpTransport(str, Enum):
    STDIO = "stdio"
    STREAMABLE_HTTP = "streamable-http"


class LogFormat(str, Enum):
    JSON = "json"
    TEXT = "text"


class Settings(BaseSettings):
    """Validated environment settings for the Elasticsearch MCP server."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
        case_sensitive=False,
    )

    server_name: str = Field(
        default="es-mcp-server",
        validation_alias="ES_MCP_SERVER_NAME",
    )
    mcp_transport: McpTransport = Field(
        default=McpTransport.STDIO,
        validation_alias="MCP_TRANSPORT",
    )
    mcp_http_host: str = Field(default="127.0.0.1", validation_alias="MCP_HTTP_HOST")
    mcp_http_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        validation_alias="MCP_HTTP_PORT",
    )
    mcp_http_path: str = Field(default="/mcp", validation_alias="MCP_HTTP_PATH")

    elasticsearch_url: str = Field(min_length=1, validation_alias="ELASTICSEARCH_URL")
    elasticsearch_username: str | None = Field(
        default=None,
        validation_alias="ELASTICSEARCH_USERNAME",
    )
    elasticsearch_password: SecretStr | None = Field(
        default=None,
        validation_alias="ELASTICSEARCH_PASSWORD",
    )
    elasticsearch_api_key: SecretStr | None = Field(
        default=None,
        validation_alias="ELASTICSEARCH_API_KEY",
    )
    elasticsearch_ca_cert_path: Path | None = Field(
        default=None,
        validation_alias="ELASTICSEARCH_CA_CERT_PATH",
    )
    kibana_url: str | None = Field(default=None, validation_alias="KIBANA_URL")
    kibana_username: str | None = Field(default=None, validation_alias="KIBANA_USERNAME")
    kibana_password: SecretStr | None = Field(
        default=None,
        validation_alias="KIBANA_PASSWORD",
    )
    kibana_api_key: SecretStr | None = Field(default=None, validation_alias="KIBANA_API_KEY")
    kibana_ca_cert_path: Path | None = Field(
        default=None,
        validation_alias="KIBANA_CA_CERT_PATH",
    )
    kibana_space_id: str | None = Field(default="default", validation_alias="KIBANA_SPACE_ID")
    kibana_request_timeout_seconds: float = Field(
        default=10.0,
        gt=0,
        validation_alias="KIBANA_REQUEST_TIMEOUT_SECONDS",
    )

    read_only: bool = Field(default=True, validation_alias="ES_READ_ONLY")
    enable_write_tools: bool = Field(default=False, validation_alias="ES_ENABLE_WRITE_TOOLS")
    enable_destructive_tools: bool = Field(
        default=False,
        validation_alias="ES_ENABLE_DESTRUCTIVE_TOOLS",
    )

    index_allowlist: list[str] = Field(
        default_factory=lambda: ["*"],
        validation_alias="ES_INDEX_ALLOWLIST",
    )
    index_denylist: list[str] = Field(
        default_factory=lambda: [
            ".*",
            ".security*",
            ".kibana*",
            ".fleet*",
            ".tasks",
            ".async-search*",
        ],
        validation_alias="ES_INDEX_DENYLIST",
    )

    max_result_size: int = Field(
        default=100,
        ge=1,
        le=10000,
        validation_alias="ES_MAX_RESULT_SIZE",
    )
    max_timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        le=300,
        validation_alias="ES_MAX_TIMEOUT_SECONDS",
    )
    request_timeout_seconds: float = Field(
        default=10.0,
        gt=0,
        validation_alias=AliasChoices(
            "ES_REQUEST_TIMEOUT_SECONDS",
            "ELASTICSEARCH_REQUEST_TIMEOUT_SECONDS",
        ),
    )

    log_index_pattern: str = Field(
        default="logs-*",
        validation_alias="ES_LOG_INDEX_PATTERN",
    )
    slow_log_index_pattern: str | None = Field(
        default=None,
        validation_alias="ES_SLOW_LOG_INDEX_PATTERN",
    )

    log_level: str = Field(default="INFO", validation_alias="ES_MCP_LOG_LEVEL")
    log_format: LogFormat = Field(default=LogFormat.JSON, validation_alias="ES_MCP_LOG_FORMAT")

    @field_validator("elasticsearch_url")
    @classmethod
    def validate_elasticsearch_url(cls, value: str) -> str:
        return cls._validate_http_url(value, "ELASTICSEARCH_URL")

    @field_validator("kibana_url")
    @classmethod
    def validate_kibana_url(cls, value: str | None) -> str | None:
        if value in {None, ""}:
            return None
        return cls._validate_http_url(value, "KIBANA_URL")

    @staticmethod
    def _validate_http_url(value: str, env_name: str) -> str:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError(f"{env_name} must be an http or https URL")
        if parsed.username or parsed.password:
            raise ValueError(
                f"Do not embed credentials in {env_name}; use auth environment variables"
            )
        return value.rstrip("/")

    @field_validator("index_allowlist", "index_denylist", mode="before")
    @classmethod
    def parse_pattern_list(cls, value: Any) -> Any:
        if value is None or isinstance(value, list):
            return value
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return value

    @field_validator("index_allowlist")
    @classmethod
    def validate_allowlist(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("ES_INDEX_ALLOWLIST must contain at least one pattern")
        return value

    @field_validator(
        "elasticsearch_ca_cert_path",
        "kibana_ca_cert_path",
        "kibana_space_id",
        "slow_log_index_pattern",
        mode="before",
    )
    @classmethod
    def empty_string_to_none(cls, value: Any) -> Any:
        if value == "":
            return None
        return value

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        normalized = value.upper()
        if normalized not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("ES_MCP_LOG_LEVEL must be a standard Python logging level")
        return normalized

    @field_validator("mcp_http_path")
    @classmethod
    def validate_http_path(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError("MCP_HTTP_PATH must start with /")
        return value

    @field_validator("kibana_space_id")
    @classmethod
    def validate_default_kibana_space_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        candidate = value.strip()
        if candidate in {"", "default"}:
            return "default"
        if candidate != value or not _KIBANA_SPACE_RE.fullmatch(candidate):
            raise ValueError(
                "KIBANA_SPACE_ID must use lowercase letters, digits, underscores, or hyphens"
            )
        return candidate

    @model_validator(mode="after")
    def validate_auth_and_limits(self) -> "Settings":
        has_basic_user = bool(self.elasticsearch_username)
        has_basic_password = self.elasticsearch_password is not None
        has_api_key = self.elasticsearch_api_key is not None
        has_kibana_basic_user = bool(self.kibana_username)
        has_kibana_basic_password = self.kibana_password is not None
        has_kibana_api_key = self.kibana_api_key is not None

        if has_basic_user != has_basic_password:
            raise ValueError(
                "ELASTICSEARCH_USERNAME and ELASTICSEARCH_PASSWORD must be provided together"
            )
        if has_api_key and has_basic_user:
            raise ValueError(
                "Use either ELASTICSEARCH_API_KEY or username/password authentication, not both"
            )
        if self.elasticsearch_ca_cert_path and not self.elasticsearch_ca_cert_path.exists():
            raise ValueError("ELASTICSEARCH_CA_CERT_PATH does not exist")
        if has_kibana_basic_user != has_kibana_basic_password:
            raise ValueError("KIBANA_USERNAME and KIBANA_PASSWORD must be provided together")
        if has_kibana_api_key and has_kibana_basic_user:
            raise ValueError(
                "Use either KIBANA_API_KEY or username/password authentication, not both"
            )
        if self.kibana_ca_cert_path and not self.kibana_ca_cert_path.exists():
            raise ValueError("KIBANA_CA_CERT_PATH does not exist")
        if self.request_timeout_seconds > self.max_timeout_seconds:
            raise ValueError("ES_REQUEST_TIMEOUT_SECONDS cannot exceed ES_MAX_TIMEOUT_SECONDS")
        if self.kibana_request_timeout_seconds > self.max_timeout_seconds:
            raise ValueError("KIBANA_REQUEST_TIMEOUT_SECONDS cannot exceed ES_MAX_TIMEOUT_SECONDS")
        if self.read_only and (self.enable_write_tools or self.enable_destructive_tools):
            raise ValueError("Set ES_READ_ONLY=false before enabling write or destructive tools")
        return self

    @property
    def masked_elasticsearch_url(self) -> str:
        parsed = urlsplit(self.elasticsearch_url)
        if parsed.username or parsed.password:
            host = parsed.hostname or ""
            if parsed.port:
                host = f"{host}:{parsed.port}"
            return urlunsplit(
                (parsed.scheme, f"***:***@{host}", parsed.path, parsed.query, parsed.fragment)
            )
        return self.elasticsearch_url

    @property
    def masked_kibana_url(self) -> str | None:
        if not self.kibana_url:
            return None
        parsed = urlsplit(self.kibana_url)
        if parsed.username or parsed.password:
            host = parsed.hostname or ""
            if parsed.port:
                host = f"{host}:{parsed.port}"
            return urlunsplit(
                (parsed.scheme, f"***:***@{host}", parsed.path, parsed.query, parsed.fragment)
            )
        return self.kibana_url

    def elasticsearch_client_options(self) -> dict[str, Any]:
        options: dict[str, Any] = {"request_timeout": self.request_timeout_seconds}
        if self.elasticsearch_api_key is not None:
            options["api_key"] = self.elasticsearch_api_key.get_secret_value()
        elif self.elasticsearch_username and self.elasticsearch_password is not None:
            options["basic_auth"] = (
                self.elasticsearch_username,
                self.elasticsearch_password.get_secret_value(),
            )
        if self.elasticsearch_ca_cert_path is not None:
            options["ca_certs"] = str(self.elasticsearch_ca_cert_path)
        return options

    def kibana_client_options(self) -> dict[str, Any]:
        options: dict[str, Any] = {
            "headers": {"kbn-xsrf": "es-mcp-server"},
            "timeout": self.kibana_request_timeout_seconds,
        }
        if self.kibana_api_key is not None:
            options["headers"]["Authorization"] = f"ApiKey {self.kibana_api_key.get_secret_value()}"
        elif self.kibana_username and self.kibana_password is not None:
            options["auth"] = (
                self.kibana_username,
                self.kibana_password.get_secret_value(),
            )
        elif self.elasticsearch_api_key is not None:
            options["headers"]["Authorization"] = (
                f"ApiKey {self.elasticsearch_api_key.get_secret_value()}"
            )
        elif self.elasticsearch_username and self.elasticsearch_password is not None:
            options["auth"] = (
                self.elasticsearch_username,
                self.elasticsearch_password.get_secret_value(),
            )
        if self.kibana_ca_cert_path is not None:
            options["verify"] = str(self.kibana_ca_cert_path)
        return options


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
