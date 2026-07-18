from __future__ import annotations

import base64
import json
import sys
import time
from typing import Any

import requests


# =============================================================================
# 사용자 설정
# =============================================================================
#
# 커머스API센터에서 확인한 값을 아래에 입력합니다.
#
# 주의:
# - 따옴표 안에 값을 붙여 넣습니다.
# - 애플리케이션 시크릿의 $ 기호도 그대로 입력합니다.
# - 인증정보가 들어간 이 파일은 Git에 올리지 않는 것이 안전합니다.
#

NAVER_COMMERCE_CLIENT_ID = "sIltmNvg6INzkAQw73puj"

NAVER_COMMERCE_CLIENT_SECRET = "$2a$04$hmg.BlCgvS4N6ebhblTsYu"


# 추천 태그를 조회할 키워드
TEST_KEYWORD = "테이프"


# 현재 애플리케이션에 연결된 자신의 스토어를 호출하므로 SELF 사용
TOKEN_TYPE = "SELF"


# 기존 상품에 실제 등록된 태그도 함께 확인하려면
# 스마트스토어 원상품번호를 입력합니다.
#
# 추천 태그만 테스트할 때는 빈 문자열로 둡니다.
ORIGIN_PRODUCT_NO = ""


# =============================================================================
# API 기본 설정
# =============================================================================

SCRIPT_VERSION = "NAVER_COMMERCE_TAG_TEST_V1"

BASE_URL = "https://api.commerce.naver.com/external"

TOKEN_URL = (
    f"{BASE_URL}/v1/oauth2/token"
)

RECOMMEND_TAG_PATH = (
    "/v2/tags/recommend-tags"
)


class NaverCommerceApiTestError(
    RuntimeError
):
    pass


# =============================================================================
# 공통 함수
# =============================================================================

def mask_value(
    value: str,
    *,
    left: int = 4,
    right: int = 4,
) -> str:
    """
    인증정보가 콘솔에 그대로 노출되지 않도록 일부만 표시한다.
    """
    normalized = str(
        value
    ).strip()

    if not normalized:
        return "없음"

    if len(normalized) <= left + right:
        return "*" * len(normalized)

    hidden_length = (
        len(normalized)
        - left
        - right
    )

    return (
        normalized[:left]
        + "*" * hidden_length
        + normalized[-right:]
    )


def validate_config() -> None:
    """
    코드 상단에 애플리케이션 ID와 시크릿이 입력되었는지 확인한다.
    """
    client_id = (
        NAVER_COMMERCE_CLIENT_ID
        .strip()
    )

    client_secret = (
        NAVER_COMMERCE_CLIENT_SECRET
        .strip()
    )

    if (
        not client_id
        or client_id
        == "여기에_애플리케이션_ID를_입력하세요"
    ):
        raise NaverCommerceApiTestError(
            (
                "코드 상단의 "
                "NAVER_COMMERCE_CLIENT_ID에 "
                "실제 애플리케이션 ID를 입력해 주세요."
            )
        )

    if (
        not client_secret
        or client_secret
        == "여기에_애플리케이션_시크릿을_입력하세요"
    ):
        raise NaverCommerceApiTestError(
            (
                "코드 상단의 "
                "NAVER_COMMERCE_CLIENT_SECRET에 "
                "실제 애플리케이션 시크릿을 입력해 주세요."
            )
        )

    if TOKEN_TYPE not in {
        "SELF",
        "SELLER",
    }:
        raise NaverCommerceApiTestError(
            (
                "TOKEN_TYPE은 SELF 또는 "
                "SELLER여야 합니다."
            )
        )


def require_bcrypt():
    """
    bcrypt 라이브러리를 불러온다.
    """
    try:
        import bcrypt

    except ImportError as error:
        raise NaverCommerceApiTestError(
            (
                "bcrypt 라이브러리가 설치되어 있지 않습니다.\n\n"
                "PowerShell에서 다음 명령을 실행해 주세요.\n\n"
                "& F:/marketAutomation/myenv/Scripts/python.exe "
                "-m pip install bcrypt"
            )
        ) from error

    return bcrypt


def parse_response(
    response: requests.Response,
) -> Any:
    """
    JSON 응답을 반환하고 JSON이 아니면 문자열을 반환한다.
    """
    try:
        return response.json()

    except ValueError:
        return response.text


def print_response_info(
    *,
    title: str,
    response: requests.Response,
) -> Any:
    """
    HTTP 상태와 오류 내용을 출력한다.
    """
    payload = parse_response(
        response
    )

    trace_id = (
        response.headers.get(
            "GNCP-GW-Trace-ID",
            "",
        )
        or response.headers.get(
            "gncp-gw-trace-id",
            "",
        )
    )

    print(
        "=" * 100
    )

    print(
        f"{title}: "
        f"{response.request.method} "
        f"{response.url}"
    )

    print(
        f"HTTP 상태: "
        f"{response.status_code}"
    )

    print(
        f"Trace ID: "
        f"{trace_id or '없음'}"
    )

    print(
        "=" * 100
    )

    if not response.ok:
        print(
            "오류 응답:"
        )

        if isinstance(
            payload,
            (
                dict,
                list,
            ),
        ):
            print(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    indent=2,
                )
            )

        else:
            print(
                payload
            )

    return payload


# =============================================================================
# 인증 토큰 발급
# =============================================================================

def create_client_secret_sign(
    *,
    client_id: str,
    client_secret: str,
    timestamp: int,
) -> str:
    """
    네이버 커머스API 전자서명을 생성한다.

    1. client_id와 timestamp를 밑줄로 연결
    2. 애플리케이션 시크릿을 salt로 bcrypt 해싱
    3. bcrypt 결과를 Base64 인코딩
    """
    bcrypt = require_bcrypt()

    password = (
        f"{client_id}_{timestamp}"
    ).encode(
        "utf-8"
    )

    try:
        hashed_password = (
            bcrypt.hashpw(
                password,
                client_secret.encode(
                    "utf-8"
                ),
            )
        )

    except ValueError as error:
        raise NaverCommerceApiTestError(
            (
                "애플리케이션 시크릿 형식이 "
                "올바르지 않습니다.\n"
                "커머스API센터에 표시된 전체 시크릿을 "
                "복사했는지 확인해 주세요."
            )
        ) from error

    client_secret_sign = (
        base64.b64encode(
            hashed_password
        ).decode(
            "utf-8"
        )
    )

    return client_secret_sign


def issue_access_token() -> str:
    """
    애플리케이션 ID와 시크릿으로 액세스 토큰을 발급한다.
    """
    client_id = (
        NAVER_COMMERCE_CLIENT_ID
        .strip()
    )

    client_secret = (
        NAVER_COMMERCE_CLIENT_SECRET
        .strip()
    )

    timestamp = int(
        time.time()
        * 1000
    )

    client_secret_sign = (
        create_client_secret_sign(
            client_id=client_id,
            client_secret=client_secret,
            timestamp=timestamp,
        )
    )

    form_data = {
        "client_id": client_id,
        "timestamp": timestamp,
        "grant_type": (
            "client_credentials"
        ),
        "client_secret_sign": (
            client_secret_sign
        ),
        "type": TOKEN_TYPE,
    }

    print()
    print(
        "인증 토큰 발급 요청"
    )

    print(
        "애플리케이션 ID: "
        f"{mask_value(client_id)}"
    )

    print(
        f"인증 타입: "
        f"{TOKEN_TYPE}"
    )

    try:
        response = requests.post(
            TOKEN_URL,
            headers={
                "Accept": (
                    "application/json"
                ),
                "Content-Type": (
                    "application/"
                    "x-www-form-urlencoded"
                ),
            },
            data=form_data,
            timeout=30,
        )

    except requests.RequestException as error:
        raise NaverCommerceApiTestError(
            (
                "토큰 발급 요청 자체가 "
                f"실패했습니다: {error}"
            )
        ) from error

    payload = print_response_info(
        title="인증 토큰 발급",
        response=response,
    )

    if not response.ok:
        raise NaverCommerceApiTestError(
            (
                "인증 토큰 발급 실패: "
                f"HTTP {response.status_code}"
            )
        )

    if not isinstance(
        payload,
        dict,
    ):
        raise NaverCommerceApiTestError(
            (
                "인증 토큰 응답이 "
                "JSON 객체가 아닙니다."
            )
        )

    access_token = str(
        payload.get(
            "access_token",
            "",
        )
    ).strip()

    if not access_token:
        raise NaverCommerceApiTestError(
            (
                "인증 응답에 "
                "access_token이 없습니다."
            )
        )

    print()
    print(
        "인증 토큰 발급 성공"
    )

    print(
        "토큰 종류: "
        f"{payload.get('token_type', 'Bearer')}"
    )

    print(
        "토큰 값: "
        f"{mask_value(access_token, left=8, right=6)}"
    )

    print(
        "유효시간: "
        f"{payload.get('expires_in')}초"
    )

    return access_token


# =============================================================================
# 커머스API 공통 요청
# =============================================================================

def request_commerce_api(
    *,
    method: str,
    path: str,
    access_token: str,
    params: dict[
        str,
        Any,
    ] | None = None,
) -> Any:
    """
    발급받은 액세스 토큰으로 커머스API를 호출한다.
    """
    url = (
        BASE_URL
        + path
    )

    headers = {
        "Accept": (
            "application/"
            "json;charset=UTF-8"
        ),
        "Authorization": (
            f"Bearer {access_token}"
        ),
    }

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            timeout=30,
        )

    except requests.RequestException as error:
        raise NaverCommerceApiTestError(
            (
                "커머스API 요청 자체가 "
                f"실패했습니다: {error}"
            )
        ) from error

    payload = print_response_info(
        title="커머스API 호출",
        response=response,
    )

    if not response.ok:
        raise NaverCommerceApiTestError(
            (
                "네이버 커머스API 호출 실패: "
                f"HTTP {response.status_code}"
            )
        )

    return payload


# =============================================================================
# 추천 태그 조회
# =============================================================================

def test_recommend_tags(
    *,
    keyword: str,
    access_token: str,
) -> list[
    dict[str, Any]
]:
    """
    키워드와 관련된 네이버 추천 태그를 조회한다.
    """
    payload = request_commerce_api(
        method="GET",
        path=RECOMMEND_TAG_PATH,
        access_token=access_token,
        params={
            "keyword": keyword,
        },
    )

    if isinstance(
        payload,
        list,
    ):
        items = payload

    elif isinstance(
        payload,
        dict,
    ):
        items = (
            payload.get(
                "contents"
            )
            or payload.get(
                "items"
            )
            or payload.get(
                "data"
            )
            or payload.get(
                "results"
            )
            or []
        )

    else:
        items = []

    tags: list[
        dict[str, Any]
    ] = []

    for item in items:
        if not isinstance(
            item,
            dict,
        ):
            continue

        tags.append(
            {
                "code": (
                    item.get(
                        "code"
                    )
                ),
                "text": (
                    item.get(
                        "text"
                    )
                ),
            }
        )

    print()
    print(
        "추천 태그 조회 키워드: "
        f"{keyword}"
    )

    print(
        "추천 태그 수: "
        f"{len(tags)}개"
    )

    if tags:
        print()
        print(
            "추천 태그:"
        )

        for index, tag in enumerate(
            tags,
            start=1,
        ):
            print(
                f"{index:>2}. "
                f"code={tag.get('code')} / "
                f"text={tag.get('text')}"
            )

    else:
        print(
            "반환된 추천 태그가 없습니다."
        )

    print()
    print(
        "원본 JSON:"
    )

    if isinstance(
        payload,
        (
            dict,
            list,
        ),
    ):
        print(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            )
        )

    else:
        print(
            payload
        )

    return tags


# =============================================================================
# 기존 상품에 등록된 태그 조회
# =============================================================================

def find_seller_tags(
    payload: Any,
) -> list[
    dict[str, Any]
]:
    """
    원상품 조회 응답 전체에서 sellerTags를 재귀적으로 찾는다.
    """
    if isinstance(
        payload,
        dict,
    ):
        for key, value in (
            payload.items()
        ):
            if (
                key == "sellerTags"
                and isinstance(
                    value,
                    list,
                )
            ):
                return [
                    item
                    for item in value
                    if isinstance(
                        item,
                        dict,
                    )
                ]

            found = find_seller_tags(
                value
            )

            if found:
                return found

    elif isinstance(
        payload,
        list,
    ):
        for value in payload:
            found = find_seller_tags(
                value
            )

            if found:
                return found

    return []


def test_origin_product_tags(
    *,
    origin_product_no: str,
    access_token: str,
) -> list[
    dict[str, Any]
]:
    """
    특정 원상품에 실제 등록된 sellerTags를 조회한다.
    """
    payload = request_commerce_api(
        method="GET",
        path=(
            "/v2/products/"
            "origin-products/"
            f"{origin_product_no}"
        ),
        access_token=access_token,
    )

    seller_tags = find_seller_tags(
        payload
    )

    print()
    print(
        "원상품번호: "
        f"{origin_product_no}"
    )

    print(
        "등록 태그 수: "
        f"{len(seller_tags)}개"
    )

    if seller_tags:
        print()
        print(
            "상품에 등록된 태그:"
        )

        for index, tag in enumerate(
            seller_tags,
            start=1,
        ):
            print(
                f"{index:>2}. "
                f"code={tag.get('code')} / "
                f"text={tag.get('text')}"
            )

    else:
        print(
            (
                "응답에서 sellerTags를 "
                "찾지 못했습니다."
            )
        )

    return seller_tags


# =============================================================================
# 메인 실행
# =============================================================================

def main() -> int:
    print(
        "실행 버전: "
        f"{SCRIPT_VERSION}"
    )

    try:
        validate_config()

        access_token = (
            issue_access_token()
        )

        keyword = " ".join(
            str(
                TEST_KEYWORD
            ).split()
        )

        if not keyword:
            raise NaverCommerceApiTestError(
                (
                    "코드 상단의 TEST_KEYWORD가 "
                    "비어 있습니다."
                )
            )

        test_recommend_tags(
            keyword=keyword,
            access_token=access_token,
        )

        origin_product_no = (
            str(
                ORIGIN_PRODUCT_NO
            ).strip()
        )

        if origin_product_no:
            test_origin_product_tags(
                origin_product_no=(
                    origin_product_no
                ),
                access_token=(
                    access_token
                ),
            )

    except NaverCommerceApiTestError as error:
        print(
            f"\n[실패] {error}",
            file=sys.stderr,
        )

        return 1

    except KeyboardInterrupt:
        print(
            "\n사용자 요청으로 중단했습니다."
        )

        return 130

    print()
    print(
        "[성공] 테스트가 끝났습니다."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )