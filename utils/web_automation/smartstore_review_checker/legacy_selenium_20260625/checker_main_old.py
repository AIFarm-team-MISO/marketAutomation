# utils/web_automation/smartstore_review_checker/checker_main.py

"""
스마트스토어 리뷰 확인 실행 파일

역할:
- 상품목록 파일에서 스마트스토어 상품번호와 판매자상품코드를 읽는다.
- 스마트스토어 공개 상품페이지에 접속한다.
- 페이지 텍스트 기반으로 리뷰 유무와 리뷰 수를 판별한다.
- 결과를 리스트로 반환한다.

주의:
- driver 생성은 smartstore_review_driver.py에서 처리한다.
- 페이지 접속/텍스트 수집은 smartstore_page_loader.py에서 처리한다.
- 리뷰 수 추출/리뷰 없음 판별은 smartstore_review_parser.py에서 처리한다.
"""

from utils.global_logger import logger
import time

# from utils.web_automation.smartstore_review_checker.legacy_selenium.smartstore_review_driver import (
#     create_smartstore_review_driver,
# )


# from utils.web_automation.smartstore_review_checker.legacy_selenium.smartstore_page_loader import (
#     build_smartstore_product_url,
#     get_body_text,
#     is_smartstore_service_error,
#     prepare_smartstore_session,
#     open_smartstore_product_only,
# )

# from utils.web_automation.smartstore_review_checker.legacy_selenium.smartstore_review_parser import (
#     extract_review_count_from_text,
#     find_review_related_lines,
#     has_no_review_text,
# )

from utils.web_automation.smartstore_review_checker.legacy_selenium_20260625.smartstore_review_reader import (
    read_excel_file,
    extract_review_targets_from_dataframe,
)


# -------------------------------------------------
# 기본 설정
# -------------------------------------------------
TEST_STORE_NAME = "misosupu"

# 테스트 중에는 5개만 확인한다.
# 전체 확인으로 바꿀 때는 None으로 변경한다.
REVIEW_TEST_LIMIT = 5

# 로그인 요구 화면이 감지되면 이후 작업을 중단한다.
STOP_ON_LOGIN_REQUIRED = True


def is_smartstore_login_required_page(page_text, current_url):
    """
    스마트스토어 상품페이지 대신 로그인 요구 화면이 나온 경우를 감지한다.
    """

    if current_url and "nid.naver.com" in current_url:
        return True

    if not page_text:
        return False

    login_required_keywords = [
        "네이버 로그인",
        "로그인 후 이용",
        "로그인이 필요",
        "아이디",
        "비밀번호",
        "로그인 상태 유지",
    ]

    return any(keyword in page_text for keyword in login_required_keywords)


def check_review_status_by_product_url(driver, store_name, product_url):
    """
    스마트스토어 상품페이지 URL에 접속하여 리뷰 유무를 판별한다.

    반환 예:
    {
        "product_url": "...",
        "review_count": 3,
        "has_review": True,
        "status": "review_exists",
        "reason": "리뷰 개수 1개 이상",
        "review_related_lines": [...],
        "page_text_sample": "..."
    }
    """


    open_smartstore_product_only(
        driver=driver,
        product_url=product_url,
    )

    page_text = get_body_text(driver)
    current_url = driver.current_url

    # -------------------------------------------------
    # 1. 로그인 요구 화면 확인
    # -------------------------------------------------
    if is_smartstore_login_required_page(page_text, current_url):
        return {
            "product_url": product_url,
            "review_count": None,
            "has_review": None,
            "status": "login_required",
            "reason": "스마트스토어 상품페이지 대신 로그인 요구 화면이 표시됨",
            "review_related_lines": [],
            "page_text_sample": page_text[:1000],
        }

    # -------------------------------------------------
    # 2. 서비스 접속 불가 화면 확인
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
    # 3. 리뷰 개수 / 리뷰 없음 문구 확인
    # -------------------------------------------------
    review_count = extract_review_count_from_text(page_text)
    no_review_text_found = has_no_review_text(page_text)
    review_related_lines = find_review_related_lines(page_text)

    # -------------------------------------------------
    # 4. 최종 상태 판별
    # -------------------------------------------------
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

    return {
        "product_url": product_url,
        "review_count": review_count,
        "has_review": has_review,
        "status": status,
        "reason": reason,
        "review_related_lines": review_related_lines,
        "page_text_sample": page_text[:1000],
    }


def make_review_result_with_target(target, result):
    """
    리뷰 확인 결과에 입력 파일의 상품 정보를 붙인다.
    """

    result["seller_product_code"] = target.get("seller_product_code", "")
    result["smartstore_product_no"] = target.get("smartstore_product_no", "")
    result["group_product_no"] = target.get("group_product_no", "")
    result["product_name"] = target.get("product_name", "")
    result["smartstore_only_product_name"] = target.get(
        "smartstore_only_product_name",
        "",
    )
    result["channel"] = target.get("channel", "")

    return result


def make_failed_review_result(target, product_url, error):
    """
    상품별 리뷰 확인 중 예외가 발생했을 때 결과 구조를 만든다.
    """

    return {
        "seller_product_code": target.get("seller_product_code", ""),
        "smartstore_product_no": target.get("smartstore_product_no", ""),
        "group_product_no": target.get("group_product_no", ""),
        "product_name": target.get("product_name", ""),
        "smartstore_only_product_name": target.get(
            "smartstore_only_product_name",
            "",
        ),
        "channel": target.get("channel", ""),
        "product_url": product_url,
        "review_count": None,
        "has_review": None,
        "status": "failed",
        "reason": str(error),
        "review_related_lines": [],
        "page_text_sample": "",
    }


def log_review_result_one_line(index, total_count, result):
    """
    상품별 리뷰 확인 결과를 한 줄로 출력한다.
    """

    seller_product_code = result.get("seller_product_code", "")
    smartstore_product_no = result.get("smartstore_product_no", "")
    product_name = result.get("product_name", "")
    status = result.get("status", "")
    review_count = result.get("review_count", "")
    reason = result.get("reason", "")

    logger.log(
        (
            f"[{index}/{total_count}] "
            f"{seller_product_code} | "
            f"상품번호:{smartstore_product_no} | "
            f"상태:{status} | "
            f"리뷰수:{review_count} | "
            f"사유:{reason} | "
            f"상품명:{product_name}"
        ),
        level="INFO",
        also_to_report=True,
    )


def summarize_review_results(review_results):
    """
    리뷰 확인 결과 집계를 만든다.
    """

    review_exists_count = sum(
        1 for result in review_results
        if result.get("status") == "review_exists"
    )

    no_review_count = sum(
        1 for result in review_results
        if result.get("status") == "no_review"
    )

    need_check_count = sum(
        1 for result in review_results
        if result.get("status") == "need_check"
    )

    login_required_count = sum(
        1 for result in review_results
        if result.get("status") == "login_required"
    )

    service_error_count = sum(
        1 for result in review_results
        if result.get("status") == "service_error"
    )

    failed_count = sum(
        1 for result in review_results
        if result.get("status") == "failed"
    )

    return {
        "total": len(review_results),
        "review_exists": review_exists_count,
        "no_review": no_review_count,
        "need_check": need_check_count,
        "login_required": login_required_count,
        "service_error": service_error_count,
        "failed": failed_count,
    }


def smartstore_review_checker(file_path, base_file_name):
    """
    스마트스토어 상품목록 파일에서 상품번호와 판매자상품코드를 읽어
    상품별 리뷰 유무를 확인한다.
    """

    logger.log(
        f"[스마트스토어 리뷰 필터링 시작] 파일:{base_file_name}",
        level="INFO",
        also_to_report=True,
        emoji_key="스마트스토어",
        separator="1line",
    )

    sheet_data = read_excel_file(file_path, base_file_name)

    review_targets = extract_review_targets_from_dataframe(
        dataframe=sheet_data,
        store_name=TEST_STORE_NAME,
    )

    if REVIEW_TEST_LIMIT is None:
        test_targets = review_targets
    else:
        test_targets = review_targets[:REVIEW_TEST_LIMIT]

    logger.log(
        (
            f"[리뷰 확인 대상] "
            f"전체:{len(review_targets)}개 | "
            f"이번 확인:{len(test_targets)}개 | "
            f"스토어:{TEST_STORE_NAME}"
        ),
        level="INFO",
        also_to_report=True,
        emoji_key="스마트스토어",
    )


    driver = create_smartstore_review_driver()
    review_results = []


    try:
        prepare_smartstore_session(
            driver=driver,
            store_name=TEST_STORE_NAME,
        )

        for index, target in enumerate(test_targets, start=1):

            seller_product_code = target.get("seller_product_code", "")
            smartstore_product_no = target.get("smartstore_product_no", "")
            store_name = target.get("store_name", TEST_STORE_NAME)

            product_url = build_smartstore_product_url(
                store_name=store_name,
                product_no=smartstore_product_no,
            )

            try:
                result = check_review_status_by_product_url(
                    driver=driver,
                    store_name=store_name,
                    product_url=product_url,
                )

                result = make_review_result_with_target(
                    target=target,
                    result=result,
                )

            except Exception as error:
                result = make_failed_review_result(
                    target=target,
                    product_url=product_url,
                    error=error,
                )

            review_results.append(result)

            log_review_result_one_line(
                index=index,
                total_count=len(test_targets),
                result=result,
            )

            if (
                STOP_ON_LOGIN_REQUIRED
                and result.get("status") == "login_required"
            ):
                logger.log(
                    (
                        f"[스마트스토어 리뷰 확인 중단] "
                        f"로그인 요구 화면 감지 | "
                        f"마지막 상품코드:{seller_product_code} | "
                        f"상품번호:{smartstore_product_no}"
                    ),
                    level="WARNING",
                    also_to_report=True,
                    emoji_key="스마트스토어",
                )
                break
            
            # 다음 상품 접속 전 대기
            if index < len(test_targets):
                time.sleep(6)

    finally:
        logger.log(
            "[스마트스토어 리뷰 확인] 드라이버 종료",
            level="INFO",
            also_to_report=True,
            emoji_key="스마트스토어",
        )
        driver.quit()

    summary = summarize_review_results(review_results)

    logger.log(
        (
            f"[스마트스토어 리뷰 필터링 완료] "
            f"확인:{summary['total']}개 | "
            f"리뷰있음:{summary['review_exists']}개 | "
            f"리뷰없음:{summary['no_review']}개 | "
            f"확인필요:{summary['need_check']}개 | "
            f"로그인요구:{summary['login_required']}개 | "
            f"서비스오류:{summary['service_error']}개 | "
            f"실패:{summary['failed']}개"
        ),
        level="INFO",
        also_to_report=True,
        emoji_key="스마트스토어",
        separator="1line",
    )

    return review_results


def main():
    """
    단독 실행 테스트용 함수.

    현재는 main.py의 리뷰 필터링 메뉴에서
    smartstore_review_checker(file_path, base_file_name)를 호출하는 흐름을 사용한다.
    """

    pass


if __name__ == "__main__":
    main()