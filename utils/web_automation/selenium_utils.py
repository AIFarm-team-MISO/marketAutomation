# utils/web_automation/selenium_utils.py

"""
Selenium 공통 유틸 함수 모음

역할:
- selector 문자열을 Selenium By 객체로 변환
- 설정파일 기반 element 찾기
- 여러 selector 후보 중 클릭 가능한 요소 찾기
- 안전 클릭 처리
- 페이지 로딩 대기
- 짧은 대기
- 페이지 텍스트 가져오기
- 브라우저 종료 감지

주의:
- 이 파일은 특정 도매처에 의존하지 않는 공통 기능만 둔다.
- 3MRO, 다른 도매처의 URL, 로그인 selector, 검색 selector 등은
  config/web_automation_settings.py에서 관리한다.
"""

import time


# =========================================================
# 1. Selenium import
# =========================================================
# By:
#   Selenium에서 element를 찾는 기준.
#   예: By.ID, By.NAME, By.CSS_SELECTOR, By.XPATH
#
# WebDriverWait:
#   특정 조건이 만족될 때까지 기다리는 객체.
#
# expected_conditions as EC:
#   Selenium에서 자주 쓰는 대기 조건 모음.
#   예: presence_of_element_located, element_to_be_clickable

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# =========================================================
# 2. 프로젝트 설정 import
# =========================================================
# WAIT_SETTINGS:
#   페이지 로딩 대기 시간, element 대기 시간, 클릭 대기 시간 등을
#   설정파일에서 가져와 공통으로 사용한다.

from config.web_automation_settings import WAIT_SETTINGS


# =========================================================
# 3. selector 변환
# =========================================================

def convert_by(selector_type):
    """
    설정파일에 적어둔 selector_type 문자열을 Selenium By 객체로 변환한다.

    설정파일에서는 Selenium 객체를 직접 쓰기보다 문자열로 관리하는 편이 편하다.

    예:
        ("name", "id")
        ("css", "button[type='submit']")
        ("xpath", "//button[contains(text(), '로그인')]")

    위와 같은 설정값을 실제 Selenium에서는 아래처럼 바꿔야 한다.

        "name"  -> By.NAME
        "css"   -> By.CSS_SELECTOR
        "xpath" -> By.XPATH

    지원 selector_type:
        id
        name
        class
        class_name
        css
        css_selector
        xpath
        tag
        tag_name
        link_text
        partial_link_text
    """

    selector_map = {
        "id": By.ID,
        "name": By.NAME,
        "class": By.CLASS_NAME,
        "class_name": By.CLASS_NAME,
        "css": By.CSS_SELECTOR,
        "css_selector": By.CSS_SELECTOR,
        "xpath": By.XPATH,
        "tag": By.TAG_NAME,
        "tag_name": By.TAG_NAME,
        "link_text": By.LINK_TEXT,
        "partial_link_text": By.PARTIAL_LINK_TEXT,
    }

    if selector_type not in selector_map:
        raise ValueError(f"지원하지 않는 selector_type 입니다: {selector_type}")

    return selector_map[selector_type]


# =========================================================
# 4. 설정 기반 element 찾기
# =========================================================

def get_element_by_config(driver, selector_config, wait_seconds=None, clickable=False):
    """
    설정값으로 element를 찾는다.

    selector_config 예:
        ("name", "id")
        ("css", ".btn_login")
        ("xpath", "//button[contains(text(), '로그인')]")

    wait_seconds:
        element를 찾을 때 최대 몇 초까지 기다릴지 설정한다.
        None이면 config.web_automation_settings.WAIT_SETTINGS의 element_wait 값을 사용한다.

    clickable:
        False:
            element가 DOM에 존재하는지만 확인한다.
            입력칸, 텍스트 영역 등을 찾을 때 주로 사용.

        True:
            element가 클릭 가능한 상태가 될 때까지 기다린다.
            버튼, 링크 등을 클릭하기 전에 사용.

    반환:
        Selenium WebElement
    """

    if wait_seconds is None:
        wait_seconds = WAIT_SETTINGS.get("element_wait", 10)

    selector_type, selector_value = selector_config
    by = convert_by(selector_type)

    if clickable:
        return WebDriverWait(driver, wait_seconds).until(
            EC.element_to_be_clickable((by, selector_value))
        )

    return WebDriverWait(driver, wait_seconds).until(
        EC.presence_of_element_located((by, selector_value))
    )


def find_clickable_element_by_candidates(driver, selector_candidates, wait_seconds=None):
    """
    여러 selector 후보 중 클릭 가능한 첫 번째 element를 찾는다.

    사용 이유:
        도매처마다 로그인 버튼, 검색 버튼 등의 selector가 다를 수 있다.
        또는 같은 사이트라도 button, input, a 태그 등으로 다르게 구현될 수 있다.

    예:
        selector_candidates = [
            ("css", "button[type='submit']"),
            ("css", "input[type='submit']"),
            ("css", ".login_btn"),
            ("xpath", "//button[contains(text(), '로그인')]"),
        ]

    동작:
        1. selector 후보를 위에서부터 하나씩 시도
        2. 클릭 가능한 element를 찾으면 바로 반환
        3. 전부 실패하면 마지막 에러를 포함해 예외 발생

    반환:
        Selenium WebElement
    """

    if wait_seconds is None:
        wait_seconds = WAIT_SETTINGS.get("clickable_wait", 5)

    last_error = None

    for selector_config in selector_candidates:
        selector_type, selector_value = selector_config
        by = convert_by(selector_type)

        try:
            element = WebDriverWait(driver, wait_seconds).until(
                EC.element_to_be_clickable((by, selector_value))
            )
            return element

        except Exception as e:
            last_error = e
            continue

    raise Exception(f"클릭 가능한 요소를 찾지 못했습니다. 마지막 에러: {last_error}")


# =========================================================
# 5. 클릭 관련 유틸
# =========================================================

def safe_click(driver, element):
    """
    element를 안전하게 클릭한다.

    일반적인 Selenium 클릭:
        element.click()

    문제:
        - 요소가 화면 밖에 있으면 클릭 실패 가능
        - 상단 메뉴나 팝업에 가려져 있으면 클릭 실패 가능
        - 일부 사이트에서는 일반 클릭이 막히는 경우 있음

    처리 방식:
        1. scrollIntoView로 요소를 화면 중앙 근처로 이동
        2. 일반 click() 시도
        3. 실패하면 JavaScript click으로 대체

    주의:
        JS 클릭은 실제 사용자 클릭과 약간 다르게 동작할 수 있으므로
        일반 클릭 실패 시 fallback 용도로만 사용한다.
    """

    try:
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            element
        )
        time.sleep(0.2)
        element.click()

    except Exception:
        driver.execute_script("arguments[0].click();", element)


# =========================================================
# 6. 페이지 로딩 / 짧은 대기
# =========================================================

def wait_page_loaded(driver, wait_seconds=None):
    """
    현재 페이지의 기본 로딩이 끝날 때까지 대기한다.

    기준:
        document.readyState == "complete"

    의미:
        브라우저가 HTML 문서 로딩을 완료했다는 뜻.

    한계:
        ajax로 나중에 뜨는 상품 목록, 검색 결과, 동적 버튼까지
        모두 로딩되었다는 뜻은 아니다.

    따라서:
        페이지 이동 직후에는 wait_page_loaded()를 사용하고,
        특정 버튼/검색창/상품 영역은 get_element_by_config()로 따로 기다리는 것이 좋다.
    """

    if wait_seconds is None:
        wait_seconds = WAIT_SETTINGS.get("page_load_wait", 10)

    WebDriverWait(driver, wait_seconds).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


def short_sleep(seconds=None):
    """
    짧은 대기 함수.

    Selenium에서는 모든 것을 WebDriverWait로 처리하는 것이 가장 좋지만,
    실제 사이트 자동화에서는 클릭 직후 약간의 화면 전환 시간이 필요한 경우가 많다.

    사용 예:
        - 로그인 버튼 클릭 직후
        - 검색어 입력 후 Enter 직후
        - 페이지는 로딩되었지만 화면 반응이 약간 늦는 경우

    seconds:
        None이면 WAIT_SETTINGS["default_sleep"] 값을 사용한다.
    """

    if seconds is None:
        seconds = WAIT_SETTINGS.get("default_sleep", 1)

    time.sleep(seconds)


# =========================================================
# 7. 페이지 텍스트 가져오기
# =========================================================

def get_page_text(driver):
    """
    현재 페이지의 body 텍스트를 가져온다.

    사용 예:
        - 로그인 성공 여부 판단
        - 로그인 페이지 여부 판단
        - 상품 없음 문구 확인
        - 품절 문구 확인
        - 판매중 문구 확인

    실패 시:
        빈 문자열 "" 반환

    이유:
        텍스트를 가져오지 못했다고 해서 전체 자동화를 중단하기보다는,
        판단 함수 쪽에서 False로 처리하는 편이 안전하다.
    """

    try:
        return driver.find_element(By.TAG_NAME, "body").text

    except Exception:
        return ""


# =========================================================
# 8. 브라우저 종료 감지
# =========================================================

def wait_until_browser_closed(driver, check_interval=1):
    """
    사용자가 브라우저 창을 직접 닫을 때까지 대기한다.

    테스트 실행 시 사용한다.

    흐름:
        1. Selenium 브라우저 실행
        2. 로그인/세션 확인
        3. 사용자가 브라우저 상태를 눈으로 확인
        4. 사용자가 X 버튼으로 브라우저 닫음
        5. 이 함수가 브라우저 종료를 감지
        6. 프로그램 종료

    check_interval:
        브라우저 종료 여부를 몇 초 간격으로 확인할지 설정한다.

    참고:
        브라우저가 이미 닫히면 driver.window_handles 접근 중 예외가 날 수 있다.
        이 경우도 정상 종료 상황으로 보고 break 처리한다.
    """

    while True:
        try:
            if len(driver.window_handles) == 0:
                break

        except Exception:
            # 브라우저가 이미 닫혔거나 Selenium 세션이 끊긴 경우
            break

        time.sleep(check_interval)

def wait_page_text_ready(driver, wait_seconds=3):
    """
    페이지 body 텍스트가 어느 정도 로딩될 때까지 대기한다.

    sleep과 달리 조건이 만족되면 즉시 다음으로 넘어간다.
    """

    WebDriverWait(driver, wait_seconds).until(
        lambda d: len(get_page_text(d).strip()) > 0
    )