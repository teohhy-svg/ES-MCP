"""Environment-driven server configuration."""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("ELASTICSEARCH_URL must be an http or https URL")
        if parsed.username or parsed.password:
            raise ValueError(
                "Do not embed credentials in ELASTICSEARCH_URL; use auth environment variables"
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

    @field_validator("elasticsearch_ca_cert_path", "slow_log_index_pattern", mode="before")
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

    @model_validator(mode="after")
    def validate_auth_and_limits(self) -> "Settings":
        has_basic_user = bool(self.elasticsearch_username)
        has_basic_password = self.elasticsearch_password is not None
        has_api_key = self.elasticsearch_api_key is not None

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
        if self.request_timeout_seconds > self.max_timeout_seconds:
            raise ValueError("ES_REQUEST_TIMEOUT_SECONDS cannot exceed ES_MAX_TIMEOUT_SECONDS")
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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
