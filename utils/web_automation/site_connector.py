# utils/web_automation/site_connector.py

"""
사이트 접속 / 로그인 / 세션 유지 담당 모듈

역할:
- 사이트별 Selenium driver 생성
- 기존 로그인 세션 확인
- 로그인 페이지 여부 판단
- 로그인 성공 여부 판단
- 아이디/비밀번호 입력
- 로그인 버튼 클릭 또는 Enter 제출
- 로그인 후 메인 페이지 재진입
- 외부에서 사용할 open_web_automation(), close_driver() 제공

주의:
- 이 파일은 Selenium 실행 흐름과 로그인 흐름을 담당한다.
- 사이트별 URL, 로그인 selector, 성공 판단 문구 등은
  config/web_automation_settings.py의 SALE_SITES에서 관리한다.
- 클릭, 대기, selector 변환 같은 공통 기능은
  selenium_utils.py에서 가져와 사용한다.
"""

import os
import sys
from utils.web_automation.selenium_utils import (
    get_element_by_config,
    find_clickable_element_by_candidates,
    safe_click,
    wait_page_loaded,
    short_sleep,
    get_page_text,
    wait_page_text_ready,
)



# =========================================================
# 1. Selenium import
# =========================================================
# Keys:
#   로그인 버튼 클릭 실패 시 비밀번호 입력칸에서 Enter를 입력하기 위해 사용.
#
# WebDriverWait:
#   로그인 제출 후 성공 상태가 될 때까지 기다릴 때 사용.

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait


# =========================================================
# 2. 프로젝트 설정 / driver import
# =========================================================
# SALE_SITES:
#   사이트별 URL, 로그인 selector, 성공 판단 문구, 프로필명 등을 담은 설정.
#
# WAIT_SETTINGS:
#   element 대기, 로그인 후 대기, 기본 sleep 시간 등을 담은 설정.
#
# setup_driver:
#   rotationAuto/driver/driver_init.py에 있는 Chrome driver 생성 함수.

from config.web_automation_settings import SALE_SITES, WAIT_SETTINGS
from rotationAuto.driver.driver_init import setup_driver


# =========================================================
# 3. Selenium 공통 유틸 import
# =========================================================
# selenium_utils.py에 있는 공통 기능을 가져온다.
#
# get_element_by_config:
#   설정파일의 selector 기준으로 element 찾기.
#
# find_clickable_element_by_candidates:
#   여러 로그인 버튼 후보 중 클릭 가능한 버튼 찾기.
#
# safe_click:
#   일반 클릭 실패 시 JS 클릭으로 대체.
#
# wait_page_loaded:
#   페이지 기본 로딩 완료 대기.
#
# short_sleep:
#   짧은 대기.
#
# get_page_text:
#   현재 페이지 body 텍스트 가져오기.

from utils.web_automation.selenium_utils import (
    get_element_by_config,
    find_clickable_element_by_candidates,
    safe_click,
    wait_page_loaded,
    short_sleep,
    get_page_text,
)


# =========================================================
# 4. 사이트 설정 확인
# =========================================================

def get_site_config(site_key):
    """
    site_key에 해당하는 사이트 설정을 가져온다.

    site_key 예:
        "3mro"

    존재하지 않는 site_key가 들어오면 ValueError를 발생시킨다.

    이 함수를 따로 둔 이유:
        여러 함수에서 반복되는 SALE_SITES 존재 여부 확인을
        한 곳으로 모으기 위해서다.
    """

    if site_key not in SALE_SITES:
        raise ValueError(f"등록되지 않은 사이트입니다: {site_key}")

    return SALE_SITES[site_key]


# =========================================================
# 5. 로그인 페이지 여부 판단
# =========================================================

def is_login_page(driver, site_config):
    """
    현재 페이지가 로그인 페이지인지 판단한다.

    판단 기준:
    1. 현재 URL에 login_url_keywords 중 하나가 포함되어 있는지 확인
    2. 페이지 텍스트에 login_page_words가 모두 포함되어 있는지 확인

    예:
        URL에 "login" 포함
        또는 페이지 텍스트에 "로그인", "아이디", "비밀번호"가 모두 포함

    반환:
        True  → 로그인 페이지로 판단
        False → 로그인 페이지가 아니라고 판단
    """

    current_url = driver.current_url.lower()

    # URL 기준 로그인 페이지 판단
    for keyword in site_config.get("login_url_keywords", []):
        if keyword.lower() in current_url:
            return True

    # 페이지 텍스트 기준 로그인 페이지 판단
    page_text = get_page_text(driver)
    login_words = site_config.get("login_page_words", [])

    if login_words and all(word in page_text for word in login_words):
        return True

    return False


# =========================================================
# 6. 로그인 성공 여부 판단
# =========================================================

def is_login_success(driver, site_config):
    """
    로그인 성공 여부를 판단한다.

    판단 기준:
    1. 현재 URL에 success_url_keywords 중 하나가 포함되어 있는지 확인
    2. 페이지 텍스트에 success_page_words 중 하나가 포함되어 있는지 확인

    예:
        URL에 "/shop" 포함
        또는 페이지 텍스트에 "로그아웃", "마이페이지", "장바구니" 등이 포함

    반환:
        True  → 로그인 성공 상태로 판단
        False → 로그인 성공 상태가 아니라고 판단

    주의:
        success_url_keywords를 너무 넓게 잡으면
        로그인 전 메인 페이지도 성공으로 오판할 수 있다.
        가능하면 success_page_words를 함께 설정하는 것이 좋다.
    """

    current_url = driver.current_url.lower()

    # URL 기준 로그인 성공 판단
    for keyword in site_config.get("success_url_keywords", []):
        if keyword.lower() in current_url:
            return True

    # 페이지 텍스트 기준 로그인 성공 판단
    page_text = get_page_text(driver)

    for word in site_config.get("success_page_words", []):
        if word in page_text:
            return True

    return False


# =========================================================
# 7. 로그인 후 성공 상태 대기
# =========================================================

def wait_after_login(driver, site_config):
    """
    로그인 제출 후 로그인 성공 상태가 될 때까지 기다린다.

    내부적으로 is_login_success()를 반복 확인한다.

    성공:
        True 반환

    실패 또는 시간 초과:
        False 반환

    설정:
        after_login_wait_seconds:
            로그인 성공을 최대 몇 초 기다릴지 설정.

        after_login_extra_sleep_seconds:
            로그인 성공 판단 후 추가로 몇 초 더 기다릴지 설정.
            페이지 전환이나 세션 반영이 늦는 사이트를 대비한다.
    """

    wait_seconds = site_config.get(
        "after_login_wait_seconds",
        WAIT_SETTINGS.get("after_login_wait", 10)
    )

    extra_sleep = site_config.get(
        "after_login_extra_sleep_seconds",
        WAIT_SETTINGS.get("after_login_extra_sleep", 1)
    )

    try:
        WebDriverWait(driver, wait_seconds).until(
            lambda d: is_login_success(d, site_config)
        )

        short_sleep(extra_sleep)
        return True

    except Exception:
        short_sleep(extra_sleep)
        return False


# =========================================================
# 8. 로그인 폼 제출
# =========================================================

def submit_login_form(driver, site_config, password_field):
    """
    로그인 폼을 제출한다.

    제출 우선순위:
    1. 설정파일의 login_button_selectors 후보를 순서대로 시도
    2. 클릭 가능한 버튼을 찾으면 safe_click()으로 클릭
    3. 버튼 클릭에 실패하면 비밀번호 입력칸에서 Enter 입력

    site_config 관련 설정:
        login_button_selectors:
            로그인 버튼 selector 후보 목록.

        submit_fallback:
            버튼 클릭 실패 시 사용할 fallback 방식.
            현재는 "enter_password"를 사용.

    반환:
        "button_click"    → 로그인 버튼 클릭으로 제출
        "enter_password"  → 비밀번호 입력칸 Enter로 제출
    """

    button_selectors = site_config.get("login_button_selectors", [])
    fallback = site_config.get("submit_fallback", "enter_password")

    # 1. 로그인 버튼 후보 클릭 시도
    if button_selectors:
        try:
            login_button = find_clickable_element_by_candidates(
                driver,
                button_selectors,
                wait_seconds=WAIT_SETTINGS.get("clickable_wait", 5)
            )

            safe_click(driver, login_button)
            return "button_click"

        except Exception as e:
            print(f"로그인 버튼 클릭 실패. fallback 진행: {e}")

    # 2. 버튼 클릭 실패 시 Enter 제출
    if fallback == "enter_password":
        password_field.send_keys(Keys.RETURN)
        return "enter_password"

    raise Exception("로그인 제출 방법을 찾지 못했습니다.")


# =========================================================
# 9. driver 생성
# =========================================================

def create_web_driver(site_key):
    """
    사이트별 설정에 맞춰 Selenium driver를 생성한다.

    흐름:
    1. site_key로 사이트 설정 조회
    2. 사이트별 profile_name 확인
    3. 사이트별 download_dir 확인
    4. setup_driver() 호출
    5. 생성된 driver 반환

    profile_name:
        크롬 로그인 세션 유지에 사용한다.
        예: web_automation_data/chrome_profiles/3mro

    download_dir:
        해당 사이트에서 파일 다운로드 시 사용할 폴더.
        예: web_automation_data/downloads/3mro
    """

    site_config = get_site_config(site_key)

    profile_name = site_config.get("profile_name", site_key)
    download_dir = site_config.get("download_dir", None)

    driver = setup_driver(
        profile_name=profile_name,
        download_dir=download_dir,
    )

    return driver


# =========================================================
# 10. 로그인 실행
# =========================================================

def login_to_web_site(driver, site_key):
    """
    설정파일 기준으로 사이트 로그인을 실행한다.

    흐름:
    1. 로그인 페이지로 이동
    2. 페이지 로딩 대기
    3. 아이디 입력칸 찾기
    4. 비밀번호 입력칸 찾기
    5. 아이디/비밀번호 입력
    6. 로그인 버튼 클릭 또는 Enter 제출
    7. 로그인 성공 여부 대기
    8. 성공 여부 반환

    반환:
        True  → 로그인 성공으로 판단
        False → 로그인 성공 여부를 판단하지 못함
    """

    site_config = get_site_config(site_key)

    site_name = site_config["site_name"]
    login_url = site_config["login_url"]
    username = site_config["username"]
    password = site_config["password"]

    print(f"[{site_name}] 로그인 페이지로 이동합니다.")
    driver.get(login_url)

    driver.get(login_url)

    wait_page_loaded(driver)
    wait_page_text_ready(driver, wait_seconds=3)

    # 아이디 입력칸 찾기
    username_field = get_element_by_config(
        driver,
        site_config["id_selector"],
        wait_seconds=WAIT_SETTINGS.get("element_wait", 10),
    )

    # 비밀번호 입력칸 찾기
    password_field = get_element_by_config(
        driver,
        site_config["password_selector"],
        wait_seconds=WAIT_SETTINGS.get("element_wait", 10),
    )

    # 기존 입력값 제거
    username_field.clear()
    password_field.clear()

    # 로그인 정보 입력
    username_field.send_keys(username)
    password_field.send_keys(password)

    print(f"[{site_name}] 로그인 정보를 입력했습니다.")

    # 로그인 제출
    submit_method = submit_login_form(driver, site_config, password_field)

    print(f"[{site_name}] 로그인 제출 완료. 제출 방식: {submit_method}")
    print(f"[{site_name}] 로그인 결과를 기다립니다.")

    # 로그인 성공 여부 확인
    success = wait_after_login(driver, site_config)

    if success:
        print(f"[{site_name}] 로그인 성공으로 판단됩니다.")
    else:
        print(f"[{site_name}] 로그인 성공 여부를 자동 판단하지 못했습니다.")
        print(f"[{site_name}] 현재 URL: {driver.current_url}")

    return success


# =========================================================
# 11. 기존 세션 확인 후 필요 시 로그인
# =========================================================

def check_session_and_login(driver, site_key):
    """
    메인 페이지 접속 후 기존 로그인 세션을 확인한다.

    흐름:
    1. 메인 페이지 접속
    2. 페이지 로딩 대기
    3. 로그인 성공 상태인지 확인
    4. 이미 로그인 상태면 그대로 driver 반환
    5. 로그인 페이지로 이동된 상태면 로그인 실행
    6. 상태가 애매하면 설정에 따라 강제 로그인 실행
    7. 로그인 후 메인 페이지 재접속
    8. driver 반환

    force_login_when_unknown:
        True:
            로그인 상태를 명확히 판단하지 못하면 로그인 페이지로 이동해 로그인 시도.

        False:
            애매한 상태라도 강제 로그인하지 않고 현재 페이지 유지.
    """

    site_config = get_site_config(site_key)

    site_name = site_config["site_name"]
    main_url = site_config["main_url"]

    print(f"[{site_name}] 메인 페이지 접속")
    driver.get(main_url)

    wait_page_loaded(driver)
    wait_page_text_ready(driver, wait_seconds=3)


    # 1. 이미 로그인 상태인지 확인
    if is_login_success(driver, site_config):
        print(f"[{site_name}] 기존 로그인 세션 확인됨. 그대로 진행합니다.")
        return driver

    # 2. 로그인 페이지로 판단되면 로그인 실행
    if is_login_page(driver, site_config):
        print(f"[{site_name}] 로그인 세션 없음. 로그인을 진행합니다.")
        login_to_web_site(driver, site_key)

    # 3. 로그인 상태가 애매한 경우
    else:
        print(f"[{site_name}] 로그인 세션이 확인되지 않았습니다.")
        print(f"[{site_name}] 현재 URL: {driver.current_url}")

        force_login_when_unknown = site_config.get("force_login_when_unknown", True)

        if force_login_when_unknown:
            print(f"[{site_name}] 로그인 페이지로 이동해 로그인을 진행합니다.")
            login_to_web_site(driver, site_key)
        else:
            print(f"[{site_name}] 자동 로그인을 하지 않고 현재 페이지를 유지합니다.")

    # 로그인 이후 다시 메인 페이지로 이동
    # 이유:
    #   로그인 직후 마이페이지나 이전 페이지에 머무를 수 있으므로
    #   자동화 시작 위치를 항상 main_url로 통일한다.
    driver.get(main_url)
    wait_page_loaded(driver)
    wait_page_text_ready(driver, wait_seconds=3)

    return driver


# =========================================================
# 12. 외부 공개 함수
# =========================================================

def open_web_automation(site_key):
    """
    웹 자동화 작업용 driver를 생성하고 로그인 상태까지 확인한 뒤 반환한다.

    외부 사용 예:
        from utils.web_automation import open_web_automation, close_driver

        driver = open_web_automation("3mro")

        try:
            # 상품 검색, 품절 확인, 다운로드 등 작업
            pass
        finally:
            close_driver(driver)

    반환:
        로그인 세션이 확인된 Selenium driver
    """

    driver = create_web_driver(site_key)
    driver = check_session_and_login(driver, site_key)

    return driver


def close_driver(driver):
    """
    Selenium driver를 종료한다.

    이미 브라우저가 닫힌 경우에도
    프로그램이 중단되지 않도록 예외를 무시한다.
    """

    try:
        print("작업 완료 후 드라이버를 종료합니다.")
        driver.quit()

    except Exception:
        pass


# =========================================================
# 13. 기존 이름 호환용 alias
# =========================================================
# 이전 코드에서 open_sale_site, open_wholesale_site를 사용하더라도
# 당분간 깨지지 않게 별칭을 둔다.
#
# 이후 새 코드에서는 open_web_automation() 사용을 권장한다.

open_sale_site = open_web_automation
open_wholesale_site = open_web_automation

