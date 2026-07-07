# utils/web_automation/smartstore_review_checker/review_matcher.py

"""
스마트스토어 리뷰 통합본과 비교 대상 상품군 매칭 모듈

역할:
- 비교 대상 상품 목록과 리뷰 master의 상품별 리뷰 집계를 상품번호 기준으로 병합한다.
- 비교 대상 상품 정보 옆에 리뷰 통합본의 집계 정보를 붙인다.
- 리뷰 있음 / 리뷰 없음 / 리뷰 3개 이상 / 리뷰 1~2개로 분류한다.
"""

import pandas as pd

from utils.global_logger import logger


REVIEW_NUMERIC_COLUMNS = [
    "총리뷰수",
    "일반리뷰수",
    "한달사용리뷰수",
    "평균평점",
    "최저평점",
    "최고평점",
    "저평점리뷰수",
    "포토리뷰수",
    "베스트리뷰수",
]


REVIEW_TEXT_COLUMNS = [
    "대표상품명",
    "최초리뷰일",
    "최근리뷰일",
]


TARGET_BASE_COLUMNS = [
    "판매자상품코드",
    "상품번호",
    "그룹상품번호",
    "상품명",
    "스마트스토어전용 상품명",
    "채널",
]


def clean_text_value(value):
    """
    값을 문자열로 정리한다.
    """

    if value is None:
        return ""

    text = str(value).strip()

    if text.lower() in ["nan", "none", "nat"]:
        return ""

    return text


def clean_product_no(value):
    """
    상품번호를 문자열로 정리한다.
    """

    text = clean_text_value(value)

    if not text:
        return ""

    if text.endswith(".0"):
        text = text[:-2]

    return text.strip()


def prepare_target_dataframe(target_dataframe):
    """
    비교 대상 상품 DataFrame을 매칭용으로 정리한다.

    분류전순번:
    - 비교상품 파일에서의 원래 순서
    - 분류 후에도 원래 위치를 확인하기 위한 값
    


    - 분류 후에도 원래 위치를 확인하기 위한 값
    """

    dataframe = target_dataframe.copy()

    if "상품번호" not in dataframe.columns:
        raise ValueError("비교 대상 상품 DataFrame에 '상품번호' 열이 없습니다.")

    dataframe["상품번호"] = dataframe["상품번호"].apply(clean_product_no)

    dataframe["분류전순번"] = range(1, len(dataframe) + 1)

    for column in TARGET_BASE_COLUMNS:
        if column not in dataframe.columns:
            dataframe[column] = ""

    return dataframe


def prepare_product_summary_dataframe(product_summary_dataframe):
    """
    master의 상품별 리뷰 집계 DataFrame을 매칭용으로 정리한다.
    """

    dataframe = product_summary_dataframe.copy()

    if "상품번호" not in dataframe.columns:
        raise ValueError("상품별 리뷰 집계 DataFrame에 '상품번호' 열이 없습니다.")

    dataframe["상품번호"] = dataframe["상품번호"].apply(clean_product_no)

    for column in REVIEW_NUMERIC_COLUMNS:
        if column not in dataframe.columns:
            dataframe[column] = 0

    for column in REVIEW_TEXT_COLUMNS:
        if column not in dataframe.columns:
            dataframe[column] = ""

    selected_columns = [
        "상품번호",
        "대표상품명",
        "총리뷰수",
        "일반리뷰수",
        "한달사용리뷰수",
        "평균평점",
        "최저평점",
        "최고평점",
        "저평점리뷰수",
        "포토리뷰수",
        "베스트리뷰수",
        "최초리뷰일",
        "최근리뷰일",
    ]

    dataframe = dataframe[selected_columns].copy()

    dataframe = dataframe.sort_values(
        by=["총리뷰수"],
        ascending=False,
    )

    dataframe = dataframe.drop_duplicates(
        subset=["상품번호"],
        keep="first",
    )

    return dataframe


def fill_review_columns(matched_dataframe):
    """
    매칭 후 비어 있는 리뷰 관련 컬럼을 기본값으로 채운다.
    """

    dataframe = matched_dataframe.copy()

    for column in REVIEW_NUMERIC_COLUMNS:
        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        ).fillna(0)

    int_columns = [
        "총리뷰수",
        "일반리뷰수",
        "한달사용리뷰수",
        "저평점리뷰수",
        "포토리뷰수",
        "베스트리뷰수",
    ]

    for column in int_columns:
        dataframe[column] = dataframe[column].astype(int)

    for column in REVIEW_TEXT_COLUMNS:
        dataframe[column] = (
            dataframe[column]
            .fillna("")
            .apply(clean_text_value)
        )

    return dataframe


def apply_review_status(matched_dataframe):
    """
    총리뷰수 기준으로 리뷰상태와 리뷰구간을 부여한다.
    """

    dataframe = matched_dataframe.copy()

    def make_review_status(review_count):
        if review_count >= 3:
            return "review_3_or_more"

        if review_count >= 1:
            return "review_1_to_2"

        return "no_review"

    def make_review_group(review_count):
        if review_count >= 3:
            return "리뷰3개이상"

        if review_count >= 1:
            return "리뷰1~2개"

        return "리뷰없음"

    dataframe["리뷰상태"] = dataframe["총리뷰수"].apply(
        make_review_status
    )

    dataframe["리뷰구간"] = dataframe["총리뷰수"].apply(
        make_review_group
    )

    dataframe["리뷰매칭여부"] = dataframe["총리뷰수"].apply(
        lambda review_count: "Y" if review_count >= 1 else "N"
    )

    return dataframe


def arrange_output_columns(matched_dataframe):
    """
    결과 DataFrame의 컬럼 순서를 정리한다.

    상품번호와 판매자상품코드는 비교 대상 상품 파일 기준 값을 사용한다.
    상품번호(스마트스토어)는 상품번호와 동일하므로 결과에서 제외한다.
    """

    output_columns = [
        "분류전순번",
        "판매자상품코드",
        "상품번호",
        "그룹상품번호",
        "상품명",
        "스마트스토어전용 상품명",
        "채널",
        "리뷰매칭여부",
        "리뷰상태",
        "리뷰구간",
        "총리뷰수",
        "일반리뷰수",
        "한달사용리뷰수",
        "평균평점",
        "최저평점",
        "최고평점",
        "저평점리뷰수",
        "포토리뷰수",
        "베스트리뷰수",
        "최초리뷰일",
        "최근리뷰일",
        "대표상품명",
    ]

    existing_columns = [
        column
        for column in output_columns
        if column in matched_dataframe.columns
    ]

    return matched_dataframe[existing_columns].copy()


def match_target_with_review_summary(
    target_dataframe,
    product_summary_dataframe,
):
    """
    비교 대상 상품 목록과 상품별 리뷰 집계를 상품번호 기준으로 매칭한다.

    기준:
    - target_dataframe["상품번호"]
    - product_summary_dataframe["상품번호"]
    """

    target_dataframe = prepare_target_dataframe(target_dataframe)

    product_summary_dataframe = prepare_product_summary_dataframe(
        product_summary_dataframe
    )

    matched_dataframe = target_dataframe.merge(
        product_summary_dataframe,
        how="left",
        on="상품번호",
    )

    matched_dataframe = fill_review_columns(matched_dataframe)

    matched_dataframe = apply_review_status(matched_dataframe)

    matched_dataframe = arrange_output_columns(matched_dataframe)

    matched_dataframe = matched_dataframe.sort_values(
        by=["분류전순번"],
        ascending=True,
    )

    review_exists_count = int(
        (matched_dataframe["총리뷰수"] >= 1).sum()
    )

    no_review_count = int(
        (matched_dataframe["총리뷰수"] == 0).sum()
    )

    review_over_3_count = int(
        (matched_dataframe["총리뷰수"] >= 3).sum()
    )

    review_1_to_2_count = int(
        (
            (matched_dataframe["총리뷰수"] >= 1)
            & (matched_dataframe["총리뷰수"] <= 2)
        ).sum()
    )

    logger.log(
        (
            "[비교 대상 상품 리뷰 매칭 완료]\n"
            f"- 전체상품: {len(matched_dataframe)}개\n"
            f"- 리뷰있음: {review_exists_count}개\n"
            f"- 리뷰없음: {no_review_count}개\n"
            f"- 리뷰3개이상: {review_over_3_count}개\n"
            f"- 리뷰1~2개: {review_1_to_2_count}개"
        ),
        level="INFO",
        also_to_report=True,
        emoji_key="스마트스토어",
        separator="1line",
    )

    return matched_dataframe


def sort_review_sheet_dataframe(dataframe):
    """
    리뷰 분류 시트용 정렬을 적용한다.

    리뷰 관련 시트는 리뷰수 높은 순, 최근리뷰일 최신 순으로 정렬한다.
    단, 분류전순번을 함께 두어 원래 비교상품 위치는 확인할 수 있게 한다.
    """

    if dataframe.empty:
        return dataframe.copy()

    sort_columns = []
    ascending_values = []

    if "총리뷰수" in dataframe.columns:
        sort_columns.append("총리뷰수")
        ascending_values.append(False)

    if "최근리뷰일" in dataframe.columns:
        sort_columns.append("최근리뷰일")
        ascending_values.append(False)

    if "분류전순번" in dataframe.columns:
        sort_columns.append("분류전순번")
        ascending_values.append(True)

    if not sort_columns:
        return dataframe.copy()

    return dataframe.sort_values(
        by=sort_columns,
        ascending=ascending_values,
    ).copy()


def split_review_matched_dataframe(matched_dataframe):
    """
        매칭 결과를 결과 엑셀 시트별 DataFrame으로 분리한다.

        시트 구성:
        - 01_전체비교결과
        - 02_리뷰있음
        - 03_리뷰없음
        - 04_리뷰3개이상
        - 05_리뷰1~2개
    """

    all_dataframe = matched_dataframe.copy()

    review_exists_dataframe = matched_dataframe[
        matched_dataframe["총리뷰수"] >= 1
    ].copy()

    no_review_dataframe = matched_dataframe[
        matched_dataframe["총리뷰수"] == 0
    ].copy()

    review_over_3_dataframe = matched_dataframe[
        matched_dataframe["총리뷰수"] >= 3
    ].copy()

    review_1_to_2_dataframe = matched_dataframe[
        (matched_dataframe["총리뷰수"] >= 1)
        & (matched_dataframe["총리뷰수"] <= 2)
    ].copy()

    return {
        "all": all_dataframe,
        "review_exists": sort_review_sheet_dataframe(
            review_exists_dataframe
        ),
        "no_review": no_review_dataframe,
        "review_over_3": sort_review_sheet_dataframe(
            review_over_3_dataframe
        ),
        "review_1_to_2": sort_review_sheet_dataframe(
            review_1_to_2_dataframe
        ),
    }