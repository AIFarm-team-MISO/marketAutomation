import os


# -------------------------------------------------
# 프로젝트 루트 경로 등록
# -------------------------------------------------

# 이 파일을 직접 실행하거나 다른 위치에서 import할 때
# config, utils 같은 프로젝트 내부 모듈을 찾을 수 있게 한다.
# import sys
# PROJECT_ROOT = os.path.abspath(
#     os.path.join(os.path.dirname(__file__), "..", "..", "..")
# )

# if PROJECT_ROOT not in sys.path:
#     sys.path.insert(0, PROJECT_ROOT)

# -------------------------------------------------
# 여기부터 프로젝트 내부 import
# -------------------------------------------------
from config.web_automation_settings import SALE_SITES

from utils.web_automation import (
    open_web_automation,
    close_driver,
    wait_until_browser_closed,
)

from utils.web_automation.wholesale_status_checker.product_checker import (
    check_3mro_product_status_from_search_result,
)

from utils.web_automation.wholesale_status_checker.product_searcher import search_product_code

from utils.web_automation.wholesale_status_checker.product_status_runner import (
    check_multiple_product_codes,
    print_grouped_product_status_results,
    save_grouped_product_status_results_to_text_file,
)


"""
웹 자동화 실행파일

역할:
- 이 파일은 직접 실행하는 진입점이다.
- Selenium driver 생성, 사이트 접속, 로그인 세션 확인은
  site_connector.py의 open_web_automation()을 통해 수행한다.
- 브라우저가 열린 뒤 사용자가 직접 상태를 확인하고,
  브라우저 창을 닫으면 프로그램도 종료된다.

현재 테스트 흐름:
1. main() 실행
2. test_web_automation("3mro") 실행
3. open_web_automation("3mro") 호출
4. Chrome driver 생성
5. 3MRO 메인 페이지 접속
6. 기존 로그인 세션 확인
7. 로그인 상태 출력
8. 사용자가 브라우저 창을 닫을 때까지 대기
9. driver 종료

실행 명령:
    & F:/marketAutomation/myenv/Scripts/python.exe f:/marketAutomation/utils/web_automation/web_automation.py

주의:
- 이 파일에는 복잡한 자동화 로직을 넣지 않는다.
- 상품 검색, 품절 확인, 엑셀 저장 등은 이후 별도 파일로 분리하는 것이 좋다.
  예:
      product_searcher.py
      product_checker.py
      excel_reporter.py
"""

import os
import sys


# =========================================================
# 0. 프로젝트 루트 경로 등록
# =========================================================
# 현재 파일 위치:
# F:\marketAutomation\utils\web_automation\web_automation.py
#
# 프로젝트 루트:
# F:\marketAutomation
#
# 이 파일을 직접 실행하면 Python의 기준 경로가
# F:\marketAutomation\utils\web_automation 으로 잡힐 수 있다.
#
# 그러면 config, rotationAuto, utils 같은 프로젝트 패키지를
# 찾지 못할 수 있으므로 프로젝트 루트를 sys.path에 추가한다.

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# =========================================================
# 1. 프로젝트 설정 import
# =========================================================
# SALE_SITES:
#   config/web_automation_settings.py에 정의된 사이트별 설정 모음.
#
# 예:
#   SALE_SITES["3mro"]["site_name"]
#   SALE_SITES["3mro"]["main_url"]
#   SALE_SITES["3mro"]["login_url"]

from config.web_automation_settings import SALE_SITES


# =========================================================
# 2. 웹 자동화 패키지 함수 import
# =========================================================
# open_web_automation:
#   사이트 key를 받아 driver 생성 → 세션 확인 → 필요 시 로그인 → driver 반환.
#
# close_driver:
#   Selenium driver 종료.
#
# wait_until_browser_closed:
#   사용자가 브라우저 창을 닫을 때까지 대기.

from utils.web_automation import (
    open_web_automation,
    close_driver,
    wait_until_browser_closed,
)

def get_raw_product_codes_from_console():
    """
    콘솔에서 여러 줄 상품코드를 입력받는다.

    사용 방식:
    - 엑셀에서 상품코드를 여러 줄 복사해서 붙여넣는다.
    - 입력이 끝나면 END를 입력한다.
    """

    print("=" * 80)
    print("확인할 상품코드를 입력하세요.")
    print("엑셀에서 여러 행을 복사해서 그대로 붙여넣으면 됩니다.")
    print("입력이 끝나면 END 를 입력하세요.")
    print("=" * 80)

    lines = []

    while True:
        line = input()

        if line.strip().upper() == "END":
            break

        lines.append(line)

    return "\n".join(lines)

def get_raw_product_codes_from_text_file():
    """
    도매처 상품 상태 확인용 상품코드 입력 파일을 읽는다.

    파일 위치:
    utils/web_automation/wholesale_status_checker/input_product_codes.txt
    """

    current_dir = os.path.dirname(__file__)

    input_file_path = os.path.join(
        current_dir,
        "wholesale_status_checker",
        "input_product_codes.txt",
    )

    if not os.path.exists(input_file_path):
        raise FileNotFoundError(
            f"상품코드 입력 파일이 없습니다: {input_file_path}"
        )

    with open(input_file_path, "r", encoding="utf-8-sig") as file:
        return file.read()
# =========================================================
# 3. 로그인 / 세션 테스트 함수
# =========================================================

def test_web_automation(site_key="3mro"):
    """
    웹 자동화 로그인/세션 테스트용 함수.

    site_key:
        config.web_automation_settings.SALE_SITES에 등록된 사이트 key.

    예:
        "3mro"

    테스트 목적:
        - Chrome driver가 정상 실행되는지 확인
        - 브라우저 창 크기 설정이 적용되는지 확인
        - 사이트 메인 페이지 접속이 되는지 확인
        - 크롬 프로필 기반 로그인 세션이 유지되는지 확인
        - 브라우저 창을 닫았을 때 프로그램이 정상 종료되는지 확인

    동작:
        1. open_web_automation(site_key)로 driver 생성 및 로그인 상태 확인
        2. 현재 사이트명과 URL 출력
        3. 브라우저 창이 닫힐 때까지 대기
        4. finally에서 driver 종료
    """

    driver = open_web_automation(site_key)

    try:
        # 사이트 설정 가져오기
        site_config = SALE_SITES[site_key]
        site_name = site_config["site_name"]

        # 로그인 완료 후 상품코드 검색 테스트

        raw_product_codes = get_raw_product_codes_from_text_file()

        results = check_multiple_product_codes(
            driver,
            site_key,
            raw_product_codes,
        )

        print_grouped_product_status_results(results)
        save_grouped_product_status_results_to_text_file(results)





        print(f"[{site_name}] 웹 자동화 상품코드 상태 확인 테스트 완료")
        print(f"현재 URL: {driver.current_url}")
        print("브라우저 창을 닫으면 프로그램도 종료됩니다.")


        # 사용자가 브라우저 창을 직접 닫을 때까지 대기
        wait_until_browser_closed(driver)

    finally:
        # 테스트가 끝나면 driver 종료
        # 사용자가 이미 브라우저를 닫았더라도 close_driver()에서 예외를 무시한다.
        close_driver(driver)


# =========================================================
# 4. main 함수
# =========================================================

def main():
    """
    프로그램 실행 진입 함수.

    현재는 3MRO 테스트만 실행한다.

    이후 확장 방향:
        - site_key를 사용자 입력으로 받기
        - 여러 도매처 중 선택 실행
        - 상품코드 검색 테스트 실행
        - 엑셀 기반 대량 확인 실행
    """

    test_web_automation("3mro")


# =========================================================
# 5. 직접 실행 시 main() 호출
# =========================================================
# 이 파일을 직접 실행할 때만 main()을 실행한다.
#
# 다른 파일에서 import할 경우에는 main()이 자동 실행되지 않는다.
#
# 직접 실행:
#   python utils/web_automation/web_automation.py
#
# import:
#   from utils.web_automation.web_automation import test_web_automation

if __name__ == "__main__":
    main()

