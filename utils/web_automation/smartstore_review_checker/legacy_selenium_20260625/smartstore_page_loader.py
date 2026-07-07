# utils/web_automation/smartstore_review_checker/smartstore_page_loader.py

import time

from selenium.webdriver.common.by import By
from utils.global_logger import logger

from utils.web_automation.selenium_utils import (
    wait_page_loaded,
    wait_page_text_ready,
)


def build_smartstore_product_url(store_name, product_no):
    """
    스마트스토어 상품번호로 공개 상품페이지 URL을 만든다.
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
    """

    if not page_text:
        return False

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
    """

    print("[스마트스토어] 네이버 메인 접속")
    driver.get("https://www.naver.com")
    wait_page_loaded(driver)
    wait_page_text_ready(driver, wait_seconds=5)
    #time.sleep(0.5)

    print("[스마트스토어] 스토어 메인 접속")
    store_main_url = f"https://smartstore.naver.com/{store_name}"
    driver.get(store_main_url)
    wait_page_loaded(driver)
    wait_page_text_ready(driver, wait_seconds=5)
    #time.sleep(1)

    print("[스마트스토어] 상품페이지 접속")
    driver.get(product_url)
    wait_page_loaded(driver)
    wait_page_text_ready(driver, wait_seconds=5)
    #time.sleep(1.5)


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

def prepare_smartstore_session(driver, store_name):
    """
    스마트스토어 접속 전 세션을 준비한다.
    네이버 메인과 스토어 메인은 작업 시작 시 1회만 접속한다.
    """

    logger.log(
        "[스마트스토어] 네이버 메인 접속",
        level="INFO",
        also_to_report=True,
    )
    driver.get("https://www.naver.com")
    wait_page_loaded(driver)
    wait_page_text_ready(driver, wait_seconds=5)

    logger.log(
        "[스마트스토어] 스토어 메인 접속",
        level="INFO",
        also_to_report=True,
    )
    store_main_url = f"https://smartstore.naver.com/{store_name}"
    driver.get(store_main_url)
    wait_page_loaded(driver)
    wait_page_text_ready(driver, wait_seconds=5)


def open_smartstore_product_only(driver, product_url):
    """
    이미 세션 준비가 된 상태에서 상품페이지로만 이동한다.
    """

    logger.log(
        "[스마트스토어] 상품페이지 접속",
        level="INFO",
        also_to_report=True,
    )
    driver.get(product_url)
    wait_page_loaded(driver)
    wait_page_text_ready(driver, wait_seconds=5)
    

from utils.global_logger import logger

from utils.web_automation.selenium_utils import (
    wait_page_loaded,
    wait_page_text_ready,
)


def prepare_smartstore_session(driver, store_name):
    """
    스마트스토어 리뷰 확인 전 세션 준비.
    네이버 메인과 스토어 메인은 작업 시작 시 1회만 접속한다.
    """

    logger.log(
        "[스마트스토어] 세션 준비: 네이버 메인 접속",
        level="INFO",
        also_to_report=True,
        emoji_key="스마트스토어",
    )

    driver.get("https://www.naver.com")
    wait_page_loaded(driver)
    wait_page_text_ready(driver, wait_seconds=5)

    logger.log(
        "[스마트스토어] 세션 준비: 스토어 메인 접속",
        level="INFO",
        also_to_report=True,
        emoji_key="스마트스토어",
    )

    store_main_url = f"https://smartstore.naver.com/{store_name}"
    driver.get(store_main_url)
    wait_page_loaded(driver)
    wait_page_text_ready(driver, wait_seconds=5)


def open_smartstore_product_only(driver, product_url):
    """
    세션 준비 이후 상품페이지로만 이동한다.
    """

    driver.get(product_url)
    wait_page_loaded(driver)
    wait_page_text_ready(driver, wait_seconds=5)