from __future__ import annotations

import base64
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from keywordObservation.keyword_observation_paths import (
    NAVER_COMMERCE_CREDENTIALS_FILE,
)


TOKEN_URL = (
    "https://api.commerce.naver.com/external/v1/oauth2/token"
)


class NaverCommerceAuthError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        payload: Any = None,
        trace_id: str = "",
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload
        self.trace_id = trace_id


@dataclass(frozen=True)
class NaverCommerceCredentials:
    client_id: str
    client_secret: str
    token_type: str = "SELF"
    account_id: str = ""


@dataclass
class AccessToken:
    value: str
    expires_at_epoch: float
    token_type: str = "Bearer"

    def is_reusable(
        self,
        *,
        minimum_remaining_seconds: int = 120,
    ) -> bool:
        return (
            bool(self.value)
            and self.expires_at_epoch - time.time()
            > minimum_remaining_seconds
        )



def _parse_json_response(
    response: requests.Response,
) -> Any:
    try:
        return response.json()
    except ValueError:
        return response.text



def _trace_id(
    response: requests.Response,
) -> str:
    return str(
        response.headers.get("GNCP-GW-Trace-ID")
        or response.headers.get("gncp-gw-trace-id")
        or ""
    )



def _load_credentials_json(
    path: Path,
) -> dict[str, Any]:
    if not path.exists():
        return {}

    try:
        loaded = json.loads(
            path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as error:
        raise NaverCommerceAuthError(
            f"커머스API 인증파일을 읽지 못했습니다: {error}"
        ) from error

    if not isinstance(loaded, dict):
        raise NaverCommerceAuthError(
            "커머스API 인증파일의 최상위 값은 JSON 객체여야 합니다."
        )

    return loaded



def load_naver_commerce_credentials(
    path: Path = NAVER_COMMERCE_CREDENTIALS_FILE,
) -> NaverCommerceCredentials:
    loaded = _load_credentials_json(path)

    client_id = str(
        os.getenv("NAVER_COMMERCE_CLIENT_ID", "")
        or loaded.get("client_id", "")
    ).strip()

    client_secret = str(
        os.getenv("NAVER_COMMERCE_CLIENT_SECRET", "")
        or loaded.get("client_secret", "")
    ).strip()

    token_type = str(
        os.getenv("NAVER_COMMERCE_TOKEN_TYPE", "")
        or loaded.get("token_type", "SELF")
        or "SELF"
    ).strip().upper()

    account_id = str(
        os.getenv("NAVER_COMMERCE_ACCOUNT_ID", "")
        or loaded.get("account_id", "")
    ).strip()

    placeholder_values = {
        "",
        "여기에_애플리케이션_ID를_입력하세요",
        "여기에_애플리케이션_시크릿을_입력하세요",
    }

    if client_id in placeholder_values:
        raise NaverCommerceAuthError(
            "커머스API 애플리케이션 ID가 없습니다. "
            f"'{path}'의 client_id를 입력해 주세요."
        )

    if client_secret in placeholder_values:
        raise NaverCommerceAuthError(
            "커머스API 애플리케이션 시크릿이 없습니다. "
            f"'{path}'의 client_secret을 입력해 주세요."
        )

    if token_type not in {"SELF", "SELLER"}:
        raise NaverCommerceAuthError(
            "커머스API token_type은 SELF 또는 SELLER여야 합니다."
        )

    if token_type == "SELLER" and not account_id:
        raise NaverCommerceAuthError(
            "SELLER 인증은 account_id가 필요합니다."
        )

    return NaverCommerceCredentials(
        client_id=client_id,
        client_secret=client_secret,
        token_type=token_type,
        account_id=account_id,
    )



def create_client_secret_sign(
    *,
    client_id: str,
    client_secret: str,
    timestamp: int,
) -> str:
    try:
        import bcrypt
    except ImportError as error:
        raise NaverCommerceAuthError(
            "bcrypt 라이브러리가 설치되어 있지 않습니다. "
            "가상환경에서 'python -m pip install bcrypt'를 실행해 주세요."
        ) from error

    password = f"{client_id}_{timestamp}".encode("utf-8")

    try:
        hashed = bcrypt.hashpw(
            password,
            client_secret.encode("utf-8"),
        )
    except ValueError as error:
        raise NaverCommerceAuthError(
            "애플리케이션 시크릿 형식이 올바르지 않습니다. "
            "커머스API센터의 전체 시크릿을 복사했는지 확인해 주세요."
        ) from error

    return base64.b64encode(hashed).decode("utf-8")


class NaverCommerceAuthenticator:
    def __init__(
        self,
        *,
        credentials_path: Path = NAVER_COMMERCE_CREDENTIALS_FILE,
        session: requests.Session | None = None,
    ) -> None:
        self.credentials_path = credentials_path
        self.session = session or requests.Session()
        self._cached_token: AccessToken | None = None

    def clear_token(self) -> None:
        self._cached_token = None

    def get_access_token(
        self,
        *,
        force_refresh: bool = False,
    ) -> str:
        if (
            not force_refresh
            and self._cached_token is not None
            and self._cached_token.is_reusable()
        ):
            return self._cached_token.value

        credentials = load_naver_commerce_credentials(
            self.credentials_path
        )

        timestamp = int(time.time() * 1000)

        signature = create_client_secret_sign(
            client_id=credentials.client_id,
            client_secret=credentials.client_secret,
            timestamp=timestamp,
        )

        form_data: dict[str, str | int] = {
            "client_id": credentials.client_id,
            "timestamp": timestamp,
            "grant_type": "client_credentials",
            "client_secret_sign": signature,
            "type": credentials.token_type,
        }

        if credentials.token_type == "SELLER":
            form_data["account_id"] = credentials.account_id

        try:
            response = self.session.post(
                TOKEN_URL,
                headers={
                    "Accept": "application/json",
                    "Content-Type": (
                        "application/x-www-form-urlencoded"
                    ),
                },
                data=form_data,
                timeout=30,
            )
        except requests.RequestException as error:
            raise NaverCommerceAuthError(
                f"커머스API 토큰 발급 요청이 실패했습니다: {error}"
            ) from error

        payload = _parse_json_response(response)
        trace_id = _trace_id(response)

        if not response.ok:
            raise NaverCommerceAuthError(
                f"커머스API 토큰 발급 실패: HTTP {response.status_code}",
                status_code=response.status_code,
                payload=payload,
                trace_id=trace_id,
            )

        if not isinstance(payload, dict):
            raise NaverCommerceAuthError(
                "커머스API 토큰 응답이 JSON 객체가 아닙니다.",
                payload=payload,
                trace_id=trace_id,
            )

        access_token = str(
            payload.get("access_token", "")
        ).strip()

        if not access_token:
            raise NaverCommerceAuthError(
                "커머스API 토큰 응답에 access_token이 없습니다.",
                payload=payload,
                trace_id=trace_id,
            )

        try:
            expires_in = int(payload.get("expires_in", 10800))
        except (TypeError, ValueError):
            expires_in = 10800

        self._cached_token = AccessToken(
            value=access_token,
            expires_at_epoch=time.time() + max(60, expires_in),
            token_type=str(payload.get("token_type", "Bearer")),
        )

        return access_token
