# utils/web_automation/smartstore_review_checker.py

"""
스마트스토어 상품페이지 리뷰 확인 테스트

목적:
- 스마트스토어 공개 상품페이지 URL에 접속한다.
- 페이지 텍스트에서 리뷰 관련 문구를 찾는다.
- 리뷰 개수를 추출할 수 있는지 테스트한다.
- 우선은 리뷰 있음 / 리뷰 없음 / 확인필요 / 접속오류 수준으로 판별한다.

테스트 URL 예:
https://smartstore.naver.com/misosupu/products/13307779069
"""

import os

import re
import time

# -------------------------------------------------
# 프로젝트 루트 경로 등록
# -------------------------------------------------
# import sys
# PROJECT_ROOT = os.path.abspath(
#     os.path.join(os.path.dirname(__file__), "..", "..", "..")
# )

# if PROJECT_ROOT not in sys.path:
#     sys.path.insert(0, PROJECT_ROOT)


# -------------------------------------------------
# 외부 라이브러리 import
# -------------------------------------------------
from selenium.webdriver.common.by import By


# -------------------------------------------------
# 프로젝트 내부 import
# -------------------------------------------------
from rotationAuto.driver.driver_init import setup_driver

from utils.web_automation.selenium_utils import (
    wait_page_loaded,
    wait_page_text_ready,
)


# -------------------------------------------------
# 테스트 설정
# -------------------------------------------------
TEST_STORE_NAME = "misosupu"
TEST_PRODUCT_NO = "11604414761"


def create_smartstore_review_driver():
    """
    스마트스토어 공개 상품페이지 리뷰 확인 전용 드라이버를 생성한다.

    3MRO 로그인 자동화와 분리해서,
    스마트스토어 상품페이지 접속 테스트에만 사용한다.
    """

    current_dir = os.path.dirname(__file__)

    download_dir = os.path.join(
        current_dir,
        "web_automation_data",
        "downloads",
        "smartstore_review",
    )

    driver = setup_driver(
        profile_name="smartstore_review",
        download_dir=download_dir,
    )

    return driver


def build_smartstore_product_url(store_name, product_no):
    """
    스마트스토어 상품번호로 공개 상품페이지 URL을 만든다.

    예:
    store_name = "misosupu"
    product_no = "11604414761"

    결과:
    https://smartstore.naver.com/misosupu/products/11604414761 : 리뷰있음
    https://smartstore.naver.com/misosupu/products/13307779069 : 리뷰없음 
    """

    return f"https://smartstore.naver.com/{store_name}/products/{product_no}"


def get_body_text(driver):
    """
    현재 페이지의 body 텍스트를 가져온다.
    """

    body = driver.find_element(By.TAG_NAME, "body")
    return body.text.strip()


def is_smartstore_service_error(page_text):
    """
    스마트스토어 서비스 접속 불가 페이지인지 확인한다.

    Selenium 접속 시 아래와 같은 화면이 뜨는 경우가 있다.

    - 현재 서비스 접속이 불가합니다.
    - 동시에 접속하는 이용자 수가 많거나
    - 인터넷 네트워크 상태가 불안정
    - 잠시 후 다시 접속
    """

    error_keywords = [
        "현재 서비스 접속이 불가합니다",
        "동시에 접속하는 이용자 수가 많거나",
        "인터넷 네트워크 상태가 불안정",
        "잠시 후 다시 접속",
    ]

    return any(keyword in page_text for keyword in error_keywords)


def open_smartstore_product_page(driver, store_name, product_url):
    """
    스마트스토어 상품페이지를 바로 열지 않고,
    네이버 메인 → 스토어 메인 → 상품페이지 순서로 접속한다.

    목적:
    - 상품 URL 직접 접속보다 일반 사용자 이동 흐름에 가깝게 테스트한다.
    - 스마트스토어 페이지가 정상 로딩되는지 확인한다.
    """

    print("[스마트스토어] 네이버 메인 접속")
    driver.get("https://www.naver.com")
    wait_page_loaded(driver)
    wait_page_text_ready(driver, wait_seconds=5)
    time.sleep(2)

    print("[스마트스토어] 스토어 메인 접속")
    store_main_url = f"https://smartstore.naver.com/{store_name}"
    driver.get(store_main_url)
    wait_page_loaded(driver)
    wait_page_text_ready(driver, wait_seconds=5)
    time.sleep(2)

    print("[스마트스토어] 상품페이지 접속")
    driver.get(product_url)
    wait_page_loaded(driver)
    wait_page_text_ready(driver, wait_seconds=5)
    time.sleep(3)


def scroll_page_for_lazy_loading(driver):
    """
    스마트스토어 페이지는 일부 영역이 스크롤 후 로딩될 수 있으므로
    페이지를 조금씩 내려 리뷰 관련 텍스트가 로딩될 기회를 준다.
    """

    scroll_positions = [
        500,
        1200,
        2000,
        3000,
        4500,
        6000,
    ]

    for position in scroll_positions:
        driver.execute_script(f"window.scrollTo(0, {position});")
        time.sleep(0.8)

    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(0.5)


def has_no_review_text(page_text):
    """
    페이지 텍스트에서 명확한 리뷰 없음 문구를 확인한다.

    주의:
    - '첫리뷰를 남겨주세요'는 리뷰이벤트 문구로 리뷰 있는 상품에도 나올 수 있으므로 제외한다.
    """

    if not page_text:
        return False

    no_review_keywords = [
        "아직 작성된 리뷰가 없습니다",
    ]

    return any(keyword in page_text for keyword in no_review_keywords)

def extract_review_count_from_text(page_text):
    """
    페이지 전체 텍스트에서 리뷰 개수를 추정한다.

    우선순위:
    1. 줄 단위에서 '리뷰 3' 형태 확인
    2. '상세정보리뷰 3Q&A' 형태 확인
    3. '3건 리뷰' 형태 확인
    4. '0.00건 리뷰' 형태 확인
    """

    if not page_text:
        return None

    # -------------------------------------------------
    # 1. 줄 단위 패턴 우선 확인
    # -------------------------------------------------
    for line in page_text.splitlines():
        clean_line = line.strip()

        # 예: 리뷰 3
        match = re.fullmatch(r"리뷰\s*([0-9,]+)", clean_line)
        if match:
            return int(match.group(1).replace(",", ""))

        # 예: 구매평 3
        match = re.fullmatch(r"구매평\s*([0-9,]+)", clean_line)
        if match:
            return int(match.group(1).replace(",", ""))

        # 예: 구매후기 3
        match = re.fullmatch(r"구매후기\s*([0-9,]+)", clean_line)
        if match:
            return int(match.group(1).replace(",", ""))

    # -------------------------------------------------
    # 2. 탭 문구 패턴 확인
    # -------------------------------------------------
    tab_patterns = [
        r"상세정보리뷰\s*([0-9,]+)\s*Q&A",
        r"상세정보\s*리뷰\s*([0-9,]+)\s*Q&A",
    ]

    for pattern in tab_patterns:
        match = re.search(pattern, page_text)

        if match:
            return int(match.group(1).replace(",", ""))

    # -------------------------------------------------
    # 3. 일반 리뷰 건수 패턴 확인
    # -------------------------------------------------
    general_patterns = [
        r"([0-9,]+)\s*건\s*리뷰",
        r"([0-9,]+)\s*개의\s*리뷰",
        r"리뷰\s*([0-9,]+)",
        r"구매평\s*([0-9,]+)",
        r"구매후기\s*([0-9,]+)",
    ]

    for pattern in general_patterns:
        match = re.search(pattern, page_text)

        if match:
            number_text = match.group(1).replace(",", "")
            return int(number_text)

    # -------------------------------------------------
    # 4. 0.00건 리뷰 같은 평점+리뷰 결합형 처리
    # -------------------------------------------------
    # 예:
    # 0.00건 리뷰 → 리뷰 0
    # 5.03건 리뷰 → 평점 5.0 + 리뷰 3일 가능성이 있어 주의
    #
    # 이 패턴은 리뷰 없음 판단 보조용으로만 사용한다.
    # 0.00건 리뷰만 0으로 인정한다.
    if "0.00건 리뷰" in page_text:
        return 0

    return None




    """
    페이지 전체 텍스트에서 리뷰 개수를 추정한다.

    예상 가능한 문구 예:
    - 리뷰 0
    - 리뷰 12
    - 리뷰 1,234
    - 구매평 3
    - 12개의 리뷰
    - 12건 리뷰
    - 0.00건 리뷰

    반환:
    - 숫자를 찾으면 int
    - 못 찾으면 None
    """

    if not page_text:
        return None

    patterns = [
        r"리뷰\s*([0-9,]+)",
        r"구매평\s*([0-9,]+)",
        r"구매후기\s*([0-9,]+)",
        r"([0-9,]+)\s*개의\s*리뷰",
        r"([0-9,]+)\s*개의\s*구매평",
        r"([0-9,]+)\s*개의\s*구매후기",
        r"([0-9,]+)\s*건\s*리뷰",
        r"([0-9,]+)\s*건\s*구매평",
        r"([0-9]+(?:\.[0-9]+)?)\s*건\s*리뷰",
    ]

    for pattern in patterns:
        match = re.search(pattern, page_text)

        if match:
            number_text = match.group(1).replace(",", "")

            # 0.00 같은 소수 형태도 처리
            if "." in number_text:
                return int(float(number_text))

            return int(number_text)

    return None
def find_review_related_lines(page_text, max_lines=40):
    """
    페이지 텍스트 중 리뷰 관련 줄만 추려서 확인용으로 반환한다.
    """

    review_keywords = [
        "리뷰",
        "구매평",
        "구매후기",
        "평점",
        "별점",
        "만족도",
    ]

    related_lines = []

    for line in page_text.splitlines():
        clean_line = line.strip()

        if not clean_line:
            continue

        if any(keyword in clean_line for keyword in review_keywords):
            if clean_line not in related_lines:
                related_lines.append(clean_line)

        if len(related_lines) >= max_lines:
            break

    return related_lines


def check_review_status_by_product_url(driver, store_name, product_url):
    """
    스마트스토어 상품페이지 URL에 접속하여 리뷰 유무를 판별한다.

    반환 예:
    {
        "product_url": "...",
        "review_count": 3,
        "has_review": True,
        "status": "review_exists",
        "reason": "리뷰 개수 1개 이상"
    }
    """

    print("=" * 80)
    print("[스마트스토어 리뷰 확인 테스트 시작]")
    print(f"접속 URL: {product_url}")
    print("=" * 80)

    # 네이버 메인 → 스토어 메인 → 상품페이지 순서로 접속
    open_smartstore_product_page(
        driver,
        store_name,
        product_url,
    )

    # 스크롤을 통해 동적 영역 로딩 유도
    scroll_page_for_lazy_loading(driver)

    page_text = get_body_text(driver)

    # -------------------------------------------------
    # 1. 서비스 접속 불가 화면인지 먼저 확인
    # -------------------------------------------------
    if is_smartstore_service_error(page_text):
        return {
            "product_url": product_url,
            "review_count": None,
            "has_review": None,
            "status": "service_error",
            "reason": "스마트스토어 서비스 접속 불가 페이지가 표시됨",
            "review_related_lines": [],
            "page_text_sample": page_text[:1000],
        }

    # -------------------------------------------------
    # 2. 리뷰 개수 확인
    # -------------------------------------------------
    review_count = extract_review_count_from_text(page_text)
    review_related_lines = find_review_related_lines(page_text)

    no_review_text_found = has_no_review_text(page_text)

    if review_count is None and no_review_text_found:
        status = "no_review"
        has_review = False
        review_count = 0
        reason = "리뷰 없음 문구 확인"

    elif review_count is None:
        status = "need_check"
        has_review = None
        reason = "페이지 텍스트에서 리뷰 개수를 추출하지 못함"

    elif review_count > 0:
        status = "review_exists"
        has_review = True
        reason = "리뷰 개수 1개 이상"

    else:
        status = "no_review"
        has_review = False
        reason = "리뷰 개수 0개"

    result = {
        "product_url": product_url,
        "review_count": review_count,
        "has_review": has_review,
        "status": status,
        "reason": reason,
        "review_related_lines": review_related_lines,
        "page_text_sample": page_text[:1000],
    }

    return result


def print_review_check_result(result):
    """
    리뷰 확인 결과를 콘솔에 출력한다.
    """

    print("=" * 80)
    print("[스마트스토어 리뷰 확인 결과]")
    print(f"URL: {result['product_url']}")
    print(f"상태: {result['status']}")
    print(f"리뷰 있음 여부: {result['has_review']}")
    print(f"리뷰 개수: {result['review_count']}")
    print(f"판단 사유: {result['reason']}")

    print("-" * 80)
    print("[리뷰 관련으로 감지된 문구]")

    review_related_lines = result.get("review_related_lines", [])

    if review_related_lines:
        for line in review_related_lines:
            print(line)
    else:
        print("리뷰 관련 문구를 찾지 못했습니다.")

    print("-" * 80)
    print("[페이지 텍스트 일부]")

    page_text_sample = result.get("page_text_sample", "")

    if page_text_sample:
        print(page_text_sample)
    else:
        print("페이지 텍스트 샘플 없음")

    print("=" * 80)


def test_smartstore_review_checker():
    """
    테스트 실행 함수
    """

    product_url = build_smartstore_product_url(
        TEST_STORE_NAME,
        TEST_PRODUCT_NO,
    )

    driver = create_smartstore_review_driver()

    try:
        result = check_review_status_by_product_url(
            driver,
            TEST_STORE_NAME,
            product_url,
        )

        print_review_check_result(result)

        print("브라우저에서 화면을 직접 확인한 뒤 Enter를 누르면 종료됩니다.")
        input()

    finally:
        print("작업 완료 후 드라이버를 종료합니다.")
        driver.quit()


if __name__ == "__main__":
    test_smartstore_review_checker()