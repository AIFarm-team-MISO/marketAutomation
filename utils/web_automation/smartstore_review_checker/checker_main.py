# utils/web_automation/smartstore_review_checker/checker_main.py

import os

from config.web_automation_settings import (
    REVIEW_PRODUCTS_PATH,
    get_smartstore_review_market_config,
)


from utils.web_automation.smartstore_review_checker.review_target_reader import (
    read_review_target_file,
    print_target_preview,
)


from utils.web_automation.smartstore_review_checker.review_target_reader import (
    read_review_target_file,
    print_target_preview,
)
from utils.web_automation.smartstore_review_checker.review_matcher import (
    match_target_with_review_summary,
    split_review_matched_dataframe,
)

from utils.web_automation.smartstore_review_checker.review_result_writer import (
    write_review_filter_result_excel,
)


"""
스마트스토어 리뷰 필터링 메인 파일

 1. 리뷰 통합본 생성
 2. 비교 대상 상품 파일 읽기


"""

from utils.global_logger import logger

from utils.web_automation.smartstore_review_checker.review_master_builder import (
    build_review_master,
)

# 마켓을 설정파일에서 받아온다. 
market_config = get_smartstore_review_market_config()

MARKET_NAME = market_config["market_name"]
MARKET_DISPLAY_NAME = market_config["market_display_name"]


def smartstore_review_checker(file_path=None, base_file_name=None):
    """
    main.py 메뉴에서 호출되는 진입 함수.

    처리 흐름:
    1. 리뷰 통합본 생성
    2. 비교 대상 상품 파일 읽기
    3. 상품번호 기준 리뷰 집계 매칭
    4. 리뷰 있음 / 없음 / 3개 이상 / 1~2개 분류
    5. 결과 엑셀 저장
    """

    logger.log(
        (
            f"[스마트스토어 리뷰 필터링 시작] "
            f"마켓:{MARKET_DISPLAY_NAME} | "
            f"비교대상파일:{base_file_name}"
        ),
        level="INFO",
        also_to_report=True,
        emoji_key="스마트스토어",
        separator="1line",
    )

    master_result = build_review_master(
        market_name=MARKET_NAME,
        market_display_name=MARKET_DISPLAY_NAME,
    )

    if file_path:
        review_products_path = file_path
    else:
        review_products_path = REVIEW_PRODUCTS_PATH

    target_dataframe = read_review_target_file(
        review_products_path
    )

    print_target_preview(
        target_dataframe=target_dataframe,
        row_count=5,
    )

    matched_dataframe = match_target_with_review_summary(
        target_dataframe=target_dataframe,
        product_summary_dataframe=master_result["product_summary_dataframe"],
    )

    split_dataframes = split_review_matched_dataframe(
        matched_dataframe
    )

    target_file_path = target_dataframe.attrs.get(
        "source_file_path",
        review_products_path,
    )

    if os.path.isdir(review_products_path):
        output_folder_path = review_products_path
    else:
        output_folder_path = os.path.dirname(review_products_path)

    output_file_path = write_review_filter_result_excel(
        output_folder_path=output_folder_path,
        market_display_name=MARKET_DISPLAY_NAME,
        master_file_path=master_result["master_file_path"],
        target_file_path=target_file_path,
        matched_dataframe=matched_dataframe,
        split_dataframes=split_dataframes,
    )

    logger.log(
        (
            "[스마트스토어 리뷰 필터링 완료]\n"
            f"- 마켓: {MARKET_DISPLAY_NAME}\n"
            f"- 리뷰통합본: {master_result['master_file_path']}\n"
            f"- 비교대상파일: {target_file_path}\n"
            f"- 결과파일: {output_file_path}\n"
            f"- 전체상품: {len(split_dataframes['all'])}개\n"
            f"- 리뷰있음: {len(split_dataframes['review_exists'])}개\n"
            f"- 리뷰없음: {len(split_dataframes['no_review'])}개\n"
            f"- 리뷰3개이상: {len(split_dataframes['review_over_3'])}개\n"
            f"- 리뷰1~2개: {len(split_dataframes['review_1_to_2'])}개"
        ),
        level="INFO",
        also_to_report=True,
        emoji_key="스마트스토어",
        separator="1line",
    )

    return {
        "master_result": master_result,
        "target_dataframe": target_dataframe,
        "matched_dataframe": matched_dataframe,
        "split_dataframes": split_dataframes,
        "output_file_path": output_file_path,
    }

def main():
    """
    단독 실행 테스트용 함수.
    """

    smartstore_review_checker()


if __name__ == "__main__":
    main()