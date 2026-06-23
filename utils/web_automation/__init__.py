# utils/web_automation/__init__.py

"""
utils.web_automation 패키지 초기화 파일

역할:
- site_connector.py와 selenium_utils.py에 있는 주요 함수를
  외부에서 짧게 import할 수 있도록 연결한다.

예를 들어 원래는 이렇게 가져와야 한다.

    from utils.web_automation.site_connector import open_web_automation
    from utils.web_automation.site_connector import close_driver

하지만 __init__.py에 아래처럼 연결해두면 이렇게 짧게 쓸 수 있다.

    from utils.web_automation import open_web_automation, close_driver

주의:
- 이 파일에는 실제 Selenium 실행 로직을 넣지 않는다.
- 실제 사이트 접속/로그인 로직은 site_connector.py에 둔다.
- 클릭, 대기, element 찾기 같은 공통 기능은 selenium_utils.py에 둔다.
"""


# =========================================================
# 1. 사이트 접속 / 로그인 관련 공개 함수
# =========================================================
# open_web_automation:
#   사이트 key를 받아 driver 생성 → 세션 확인 → 필요 시 로그인 → driver 반환
#
# close_driver:
#   Selenium driver 종료
#
# open_sale_site, open_wholesale_site:
#   예전 이름과의 호환을 위한 별칭.
#   새 코드에서는 open_web_automation 사용을 권장한다.

from .site_connector import (
    open_web_automation,
    close_driver,
    open_sale_site,
    open_wholesale_site,
)


# =========================================================
# 2. Selenium 공통 유틸 함수
# =========================================================
# convert_by:
#   "css", "xpath", "name" 같은 문자열을 Selenium By 객체로 변환
#
# get_element_by_config:
#   설정파일 selector 기준으로 element 찾기
#
# find_clickable_element_by_candidates:
#   여러 selector 후보 중 클릭 가능한 첫 번째 element 찾기
#
# safe_click:
#   일반 클릭 실패 시 JS 클릭으로 대체
#
# wait_page_loaded:
#   document.readyState == complete까지 대기
#
# short_sleep:
#   기본 짧은 대기
#
# get_page_text:
#   현재 페이지 body 텍스트 가져오기
#
# wait_until_browser_closed:
#   사용자가 브라우저를 닫을 때까지 대기

from .selenium_utils import (
    convert_by,
    get_element_by_config,
    find_clickable_element_by_candidates,
    safe_click,
    wait_page_loaded,
    short_sleep,
    get_page_text,
    wait_until_browser_closed,
)


# =========================================================
# 3. 외부 공개 이름 목록
# =========================================================
# __all__:
#   from utils.web_automation import * 를 사용할 때
#   외부로 공개할 이름을 명시한다.
#
# 꼭 필수는 아니지만,
# 패키지에서 어떤 함수들을 공식적으로 제공하는지
# 한눈에 보기 좋게 해준다.

__all__ = [
    # 사이트 접속 / 로그인
    "open_web_automation",
    "close_driver",
    "open_sale_site",
    "open_wholesale_site",

    # Selenium 공통 유틸
    "convert_by",
    "get_element_by_config",
    "find_clickable_element_by_candidates",
    "safe_click",
    "wait_page_loaded",
    "short_sleep",
    "get_page_text",
    "wait_until_browser_closed",
]

