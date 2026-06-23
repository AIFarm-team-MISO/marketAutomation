# utils/web_automation/product_checker.py

"""
도매처 상품 상태 판별 기능

역할:
- 검색 결과 페이지에서 검색 결과 개수를 확인한다.
- 검색 결과가 0개면 not_found로 판단한다.
- 검색 결과가 1개 이상이면 NO.상품번호를 확인한다.
- 목표 상품번호와 일치하는 상품 카드 안에서 품절 여부를 확인한다.

현재 기준:
- 3MRO 검색 결과 페이지 기준
"""

import re

# -------------------------------------------------
# 외부 라이브러리 import
# -------------------------------------------------
from selenium.webdriver.common.by import By


# -------------------------------------------------
# 프로젝트 내부 import
# -------------------------------------------------
from config.web_automation_settings import WAIT_SETTINGS

from utils.web_automation.selenium_utils import get_element_by_config
from utils.web_automation.site_connector import get_site_config


def normalize_product_code(product_code):
    """
    상품코드를 비교하기 쉬운 숫자 문자열로 정리한다.

    예:
    92998 -> "92998"
    "NO.92998" -> "92998"
    """

    return (
        str(product_code)
        .replace("NO.", "")
        .replace("No.", "")
        .replace("no.", "")
        .strip()
    )


def extract_number_from_text(text):
    """
    문자열에서 숫자만 추출한다.

    예:
    "2" -> 2
    "총 2개" -> 2
    "검색결과 0건" -> 0
    """

    if not text:
        return None

    number_text = re.sub(r"[^0-9]", "", text)

    if number_text == "":
        return None

    return int(number_text)


def get_search_result_count(driver, site_key, target_code=None):
    """
    검색 결과 페이지에서 검색 결과 개수를 가져온다.

    주의:
    3MRO에서는 strong.text-crimson이 검색어 표시에도 사용될 수 있다.
    예를 들어 92998 검색 시 strong.text-crimson 값으로 92998이 먼저 잡힐 수 있다.

    따라서:
    1. strong.text-crimson 전체를 가져온다.
    2. target_code와 같은 숫자는 제외한다.
    3. 남은 숫자 중 첫 번째 값을 검색 결과 개수로 본다.
    4. 실패하면 NO.상품번호 span 개수를 보조값으로 사용한다.
    """

    site_config = get_site_config(site_key)
    site_name = site_config["site_name"]

    target_code = normalize_product_code(target_code) if target_code else None

    count_selectors = site_config.get("search_result_count_selectors", [])

    for selector_type, selector_value in count_selectors:
        try:
            by = None

            if selector_type in ["css", "css_selector"]:
                by = By.CSS_SELECTOR
            elif selector_type == "xpath":
                by = By.XPATH
            elif selector_type == "id":
                by = By.ID
            elif selector_type == "name":
                by = By.NAME

            if by is None:
                continue

            count_elements = driver.find_elements(by, selector_value)

            count_candidates = []

            for element in count_elements:
                text = element.text.strip()
                number = extract_number_from_text(text)

                if number is None:
                    continue

                # 검색어 자체가 strong.text-crimson으로 잡힌 경우 제외
                if target_code and str(number) == str(target_code):
                    continue

                count_candidates.append(number)

            if count_candidates:
                count = count_candidates[0]
                print(f"[{site_name}] 검색 결과 개수 후보: {count_candidates}")
                print(f"[{site_name}] 검색 결과 개수: {count}")
                return count

        except Exception:
            continue

    # 보조 판단: NO.상품번호 span 개수
    no_spans = driver.find_elements(
        By.XPATH,
        "//span[contains(normalize-space(), 'NO.')]"
    )

    fallback_count = len(no_spans)

    print(f"[{site_name}] 검색 결과 개수 selector 판별 실패. NO span 개수로 대체: {fallback_count}")

    return fallback_count


def find_nearest_product_card(no_span):
    """
    상품번호 span이 속한 상품 카드 영역을 찾는다.

    검색 결과 상품은 보통 li 단위로 나열되는 경우가 많다.
    li를 먼저 찾고, 없으면 div를 보조로 사용한다.
    """

    # 1순위: 가장 가까운 li
    try:
        return no_span.find_element(By.XPATH, "./ancestor::li[1]")
    except Exception:
        pass

    # 2순위: 가장 가까운 div
    try:
        return no_span.find_element(By.XPATH, "./ancestor::div[1]")
    except Exception:
        pass

    # 그래도 못 찾으면 span 자체 반환
    return no_span


def check_3mro_product_status_from_search_result(driver, target_code, site_key="3mro"):
    """
    3MRO 검색 결과 페이지에서 목표 상품번호를 찾아 판매상태를 판별한다.

    판별 기준:
    - 정확히 NO.상품코드가 있으면 상품 존재
    - 해당 카드 안에 품절 표시가 있으면 품절
    - NO.상품코드가 없고 검색 결과 상품번호 후보도 없으면 제품없음
    - NO.상품코드가 없지만 다른 관련 상품번호가 있으면 확인필요
    """

    site_config = get_site_config(site_key)
    site_name = site_config["site_name"]

    target_code = normalize_product_code(target_code)

    # -------------------------------------------------
    # 1. 검색 결과 개수 확인
    # -------------------------------------------------
    result_count = get_search_result_count(
        driver,
        site_key,
        target_code=target_code,
    )

    # -------------------------------------------------
    # 2. 검색 결과 안의 NO.상품번호 span 확인
    # -------------------------------------------------
    no_spans = driver.find_elements(
        By.XPATH,
        "//span[contains(normalize-space(), 'NO.')]"
    )

    no_texts = []

    for no_span in no_spans:
        no_text = no_span.text.strip()

        if no_text:
            no_texts.append(no_text)

    # -------------------------------------------------
    # 3. 검색 결과 자체가 없는 경우
    # -------------------------------------------------
    # result_count가 0이고, 실제 NO.상품번호 span도 없으면 제품없음으로 본다.
    if result_count == 0 and len(no_texts) == 0:
        return {
            "site_key": site_key,
            "site_name": site_name,
            "target_code": target_code,
            "found": False,
            "status": "not_found",
            "sold_out": None,
            "search_result_count": result_count,
            "matched_count": 0,
            "reason": "검색 결과 0개",
            "product_no_text": "",
            "related_product_no_texts": [],
            "card_text": "",
            "current_url": driver.current_url,
        }

    # -------------------------------------------------
    # 4. 정확히 일치하는 NO.상품번호 찾기
    # -------------------------------------------------
    matched_cards = []

    for no_span in no_spans:
        no_text = no_span.text.strip()
        current_code = normalize_product_code(no_text)

        if current_code != target_code:
            continue

        product_card = find_nearest_product_card(no_span)

        sold_out_elements = product_card.find_elements(
            By.CSS_SELECTOR,
            "div.shop-rgba-red.rgba-banner"
        )

        card_text = product_card.text.strip()
        has_sold_out_text = "품절" in card_text

        is_sold_out = len(sold_out_elements) > 0 or has_sold_out_text

        matched_cards.append({
            "product_no_text": no_text,
            "sold_out": is_sold_out,
            "card_text": card_text,
        })

    # -------------------------------------------------
    # 5. 정확히 일치하는 상품번호가 있는 경우
    # -------------------------------------------------
    if matched_cards:
        first_match = matched_cards[0]

        if first_match["sold_out"]:
            status = "sold_out"
        else:
            status = "selling"

        return {
            "site_key": site_key,
            "site_name": site_name,
            "target_code": target_code,
            "found": True,
            "status": status,
            "sold_out": first_match["sold_out"],
            "search_result_count": result_count,
            "matched_count": len(matched_cards),
            "reason": "목표 상품번호 발견",
            "product_no_text": first_match["product_no_text"],
            "related_product_no_texts": no_texts,
            "card_text": first_match["card_text"][:1000],
            "current_url": driver.current_url,
        }

    # -------------------------------------------------
    # 6. 검색 결과는 있으나 정확히 일치하는 상품번호가 없는 경우
    # -------------------------------------------------
    # 예:
    # 203 검색 시 NO.20230, NO.20325, NO.20328 등이 나오지만
    # 정확히 NO.203은 없는 경우
    return {
        "site_key": site_key,
        "site_name": site_name,
        "target_code": target_code,
        "found": False,
        "status": "need_check",
        "sold_out": None,
        "search_result_count": result_count,
        "matched_count": 0,
        "reason": "검색 결과는 있으나 정확히 일치하는 상품번호 없음",
        "product_no_text": "",
        "related_product_no_texts": no_texts,
        "card_text": "",
        "current_url": driver.current_url,
    }