# utils/web_automation/wholesale_status_checker/__init__.py

"""
도매처 상품 상태 확인 패키지.

역할:
- 도매처 상품코드 검색
- 검색 결과 기반 상품 상태 판별
- 정상 / 품절 / 제품없음 / 확인필요 / 실패 결과 정리

구성:
- product_searcher.py
    도매처 사이트에서 상품코드 검색을 실행한다.

- product_checker.py
    검색 결과 페이지에서 목표 상품코드의 상태를 판별한다.

- product_status_runner.py
    여러 상품코드를 반복 확인하고 결과를 그룹별로 정리한다.

주의:
- 이 패키지의 __init__.py에서는 Selenium driver를 생성하지 않는다.
- 실제 실행 흐름은 web_automation.py 또는 product_status_runner.py에서 관리한다.
"""

__all__ = [
    "product_searcher",
    "product_checker",
    "product_status_runner",
]