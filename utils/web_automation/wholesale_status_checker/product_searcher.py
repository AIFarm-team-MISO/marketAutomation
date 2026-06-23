# utils/web_automation/product_searcher.py

"""
도매처 사이트 상품 검색 기능

역할:
- open_web_automation()으로 로그인된 driver를 전달받는다.
- 설정파일의 search_input_selectors 기준으로 검색창을 찾는다.
- 상품코드 또는 검색어를 입력한다.
- 엔터 또는 버튼 클릭으로 검색을 실행한다.
- 검색 결과 페이지가 로딩될 때까지 기다린다.

현재 단계:
- 3MRO 메인페이지 검색창에 상품코드를 입력하고 엔터 검색한다.
"""


# -------------------------------------------------
# 외부 라이브러리 import
# -------------------------------------------------
from selenium.webdriver.common.keys import Keys


# -------------------------------------------------
# 프로젝트 내부 import
# -------------------------------------------------
from config.web_automation_settings import WAIT_SETTINGS

from utils.web_automation.selenium_utils import (
    get_element_by_config,
    find_clickable_element_by_candidates,
    safe_click,
    wait_page_loaded,
    wait_page_text_ready,
)

from utils.web_automation.site_connector import get_site_config


def get_search_input_field(driver, site_config):
    """
    설정파일에 등록된 검색창 selector 후보를 순서대로 확인하여
    실제 검색 input 요소를 찾는다.

    설정 예:
    "search_input_selectors": [
        ("name", "sq"),
    ]
    """

    search_input_selectors = site_config.get("search_input_selectors", [])

    if not search_input_selectors:
        raise ValueError("search_input_selectors 설정이 없습니다.")

    last_error = None

    for selector_config in search_input_selectors:
        try:
            search_input = get_element_by_config(
                driver,
                selector_config,
                wait_seconds=WAIT_SETTINGS.get("element_wait", 10),
                clickable=False,
            )

            return search_input

        except Exception as e:
            last_error = e
            continue

    raise Exception(f"검색창을 찾지 못했습니다. 마지막 에러: {last_error}")


def clear_and_input_search_keyword(search_input, keyword):
    """
    검색창의 기존 값을 지우고 새 검색어를 입력한다.

    clear()만으로 값이 안 지워지는 사이트도 있어서
    Ctrl + A 후 Backspace를 함께 사용한다.
    """

    try:
        search_input.clear()
    except Exception:
        pass

    search_input.send_keys(Keys.CONTROL, "a")
    search_input.send_keys(Keys.BACKSPACE)
    search_input.send_keys(str(keyword))


def submit_search(driver, site_config, search_input):
    """
    설정값에 따라 검색을 실행한다.

    현재 기본 방식:
    - enter

    추후 확장 가능 방식:
    - button_click
    """

    site_name = site_config["site_name"]
    search_submit_method = site_config.get("search_submit_method", "enter")

    if search_submit_method == "enter":
        search_input.send_keys(Keys.RETURN)
        print(f"[{site_name}] 엔터로 검색을 실행했습니다.")
        return "enter"

    if search_submit_method == "button_click":
        search_button_selectors = site_config.get("search_button_selectors", [])

        if not search_button_selectors:
            raise ValueError("search_button_selectors 설정이 없습니다.")

        search_button = find_clickable_element_by_candidates(
            driver,
            search_button_selectors,
            wait_seconds=WAIT_SETTINGS.get("clickable_wait", 5),
        )

        safe_click(driver, search_button)
        print(f"[{site_name}] 검색 버튼 클릭으로 검색을 실행했습니다.")
        return "button_click"

    raise ValueError(f"지원하지 않는 검색 실행 방식입니다: {search_submit_method}")


def search_product_code(driver, site_key, product_code, move_to_main=True):
    """
    도매처 사이트에서 상품코드를 검색한다.

    예:
    search_product_code(driver, "3mro", "92998")

    반환:
    {
        "site_key": "3mro",
        "site_name": "3MRO",
        "product_code": "92998",
        "submit_method": "enter",
        "current_url": "검색결과 URL"
    }
    """

    site_config = get_site_config(site_key)

    site_name = site_config["site_name"]
    main_url = site_config["main_url"]

    print(f"[{site_name}] 상품코드 검색 준비: {product_code}")

    # -------------------------------------------------
    # 1. 검색창이 있는 메인페이지로 이동
    # -------------------------------------------------
    # 기본값은 True.
    # 이미 메인페이지에 있는 경우에는 move_to_main=False로 생략할 수 있다.
    if move_to_main:
        driver.get(main_url)

        wait_page_loaded(driver)
        wait_page_text_ready(driver, wait_seconds=3)

    # -------------------------------------------------
    # 2. 검색창 찾기
    # -------------------------------------------------
    search_input = get_search_input_field(driver, site_config)

    # -------------------------------------------------
    # 3. 검색어 입력
    # -------------------------------------------------
    clear_and_input_search_keyword(search_input, product_code)

    print(f"[{site_name}] 검색어 입력 완료: {product_code}")

    # -------------------------------------------------
    # 4. 검색 실행
    # -------------------------------------------------
    submit_method = submit_search(driver, site_config, search_input)

    # -------------------------------------------------
    # 5. 검색 결과 페이지 로딩 대기
    # -------------------------------------------------
    wait_page_loaded(driver)
    wait_page_text_ready(driver, wait_seconds=3)

    print(f"[{site_name}] 검색 결과 페이지 이동 완료")
    print(f"[{site_name}] 현재 URL: {driver.current_url}")

    return {
        "site_key": site_key,
        "site_name": site_name,
        "product_code": str(product_code),
        "submit_method": submit_method,
        "current_url": driver.current_url,
    }