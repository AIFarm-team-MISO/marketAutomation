# utils/web_automation/smartstore_review_checker/review_download_reader.py

"""
스마트스토어 리뷰관리 다운로드 엑셀 파일 읽기 모듈

역할:
- smartstore_review_checker/review_data/onestop_living 폴더 안의
  리뷰 엑셀 파일들을 전부 읽는다.
- 여러 엑셀 파일을 하나의 DataFrame으로 병합한다.
- 상품번호, 상품명, 리뷰구분, 구매자평점, 리뷰등록일, 전시상태를 표준화한다.
"""

import os

import pandas as pd

from utils.global_logger import logger


REQUIRED_REVIEW_COLUMNS = [
    "상품번호",
    "상품명",
    "리뷰구분",
    "구매자평점",
    "리뷰등록일",
    "전시상태",
]


OPTIONAL_REVIEW_COLUMNS = [
    "리뷰글번호",
    "관련리뷰글번호",
    "상품주문번호",
    "포토/영상",
    "리뷰상세내용",
    "답글여부",
    "베스트리뷰",
    "혜택지급",
]


def clean_text_value(value):
    """
    엑셀에서 읽은 값을 문자열로 정리한다.
    """

    if value is None:
        return ""

    text = str(value).strip()

    if text.lower() in ["nan", "none"]:
        return ""

    return text


def clean_product_no(value):
    """
    상품번호를 문자열로 정리한다.

    엑셀에서 숫자로 읽혀 1234567890.0 형태가 되는 경우를 방지한다.
    """

    text = clean_text_value(value)

    if not text:
        return ""

    if text.endswith(".0"):
        text = text[:-2]

    return text.strip()


def validate_review_download_columns(dataframe):
    """
    리뷰 다운로드 엑셀에 필요한 기본 컬럼이 있는지 확인한다.
    """

    missing_columns = [
        column
        for column in REQUIRED_REVIEW_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"리뷰 다운로드 파일에 필요한 열이 없습니다: {missing_columns}"
        )


def normalize_review_download_dataframe(dataframe):
    """
    리뷰 다운로드 DataFrame을 표준화한다.
    """

    dataframe = dataframe.copy()

    dataframe.columns = [
        clean_text_value(column)
        for column in dataframe.columns
    ]

    dataframe = dataframe.dropna(how="all")
    dataframe = dataframe.fillna("")

    validate_review_download_columns(dataframe)

    dataframe["상품번호"] = dataframe["상품번호"].apply(clean_product_no)
    dataframe["상품명"] = dataframe["상품명"].apply(clean_text_value)
    dataframe["리뷰구분"] = dataframe["리뷰구분"].apply(clean_text_value)
    dataframe["구매자평점"] = dataframe["구매자평점"].apply(clean_text_value)
    dataframe["리뷰등록일"] = dataframe["리뷰등록일"].apply(clean_text_value)
    dataframe["전시상태"] = dataframe["전시상태"].apply(clean_text_value)

    for column in OPTIONAL_REVIEW_COLUMNS:
        if column in dataframe.columns:
            dataframe[column] = dataframe[column].apply(clean_text_value)

    dataframe = dataframe[
        dataframe["상품번호"] != ""
    ].copy()

    return dataframe


def read_review_download_file(file_path):
    """
    스마트스토어 리뷰관리 다운로드 엑셀 파일 1개를 읽는다.

    지원 형식:
    - .xlsx
    - .xls
    """

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"리뷰 다운로드 파일을 찾을 수 없습니다: {file_path}"
        )

    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()

    if file_extension not in [".xlsx", ".xls"]:
        raise ValueError(
            f"지원하지 않는 리뷰 다운로드 파일 형식입니다: {file_extension}"
        )

    logger.log(
        f"[리뷰 다운로드 파일 읽기 시작] {file_path}",
        level="INFO",
        also_to_report=True,
        emoji_key="스마트스토어",
    )

    dataframe = pd.read_excel(
        file_path,
        dtype=str,
    )

    dataframe = normalize_review_download_dataframe(dataframe)

    logger.log(
        (
            f"[리뷰 다운로드 파일 읽기 완료] "
            f"파일:{os.path.basename(file_path)} | "
            f"리뷰행:{len(dataframe)}개 | "
            f"고유상품:{dataframe['상품번호'].nunique()}개"
        ),
        level="INFO",
        also_to_report=True,
        emoji_key="스마트스토어",
    )

    return dataframe


def get_review_download_file_paths_from_folder(folder_path):
    """
    리뷰 데이터 폴더 안의 엑셀 파일 경로 목록을 가져온다.
    """

    if not os.path.exists(folder_path):
        raise FileNotFoundError(
            f"리뷰 다운로드 폴더를 찾을 수 없습니다: {folder_path}"
        )

    allowed_extensions = [
        ".xlsx",
        ".xls",
    ]

    file_paths = []

    for file_name in os.listdir(folder_path):
        if file_name.startswith("~$"):
            continue

        file_path = os.path.join(folder_path, file_name)

        if not os.path.isfile(file_path):
            continue

        _, file_extension = os.path.splitext(file_name)
        file_extension = file_extension.lower()

        if file_extension in allowed_extensions:
            file_paths.append(file_path)

    file_paths.sort()

    logger.log(
        (
            f"[리뷰 다운로드 폴더 파일 확인] "
            f"폴더:{folder_path} | "
            f"파일수:{len(file_paths)}개"
        ),
        level="INFO",
        also_to_report=True,
        emoji_key="스마트스토어",
    )

    return file_paths


def read_review_download_files(file_paths):
    """
    여러 리뷰 엑셀 파일을 읽어 하나의 DataFrame으로 병합한다.
    """

    dataframes = []

    for file_path in file_paths:
        dataframe = read_review_download_file(file_path)
        dataframes.append(dataframe)

    if not dataframes:
        raise ValueError("읽을 리뷰 다운로드 엑셀 파일이 없습니다.")

    merged_dataframe = pd.concat(
        dataframes,
        ignore_index=True,
    )

    logger.log(
        (
            f"[리뷰 다운로드 파일 병합 완료] "
            f"파일수:{len(file_paths)}개 | "
            f"리뷰행:{len(merged_dataframe)}개 | "
            f"고유상품:{merged_dataframe['상품번호'].nunique()}개"
        ),
        level="INFO",
        also_to_report=True,
        emoji_key="스마트스토어",
    )

    return merged_dataframe


def read_review_download_folder(folder_path):
    """
    리뷰 데이터 폴더 안의 모든 리뷰 엑셀 파일을 읽어 하나의 DataFrame으로 병합한다.
    """

    file_paths = get_review_download_file_paths_from_folder(folder_path)

    if not file_paths:
        raise ValueError(
            f"리뷰 다운로드 폴더에 읽을 엑셀 파일이 없습니다: {folder_path}"
        )

    review_dataframe = read_review_download_files(file_paths)

    return review_dataframe


def print_review_download_preview(dataframe, row_count=5):
    """
    읽어온 리뷰 다운로드 데이터의 앞부분을 로그로 확인한다.
    """

    preview_dataframe = dataframe.head(row_count)

    logger.log(
        f"[리뷰 다운로드 미리보기] 상위 {row_count}개 행",
        level="INFO",
        also_to_report=True,
        emoji_key="스마트스토어",
    )

    for index, row in preview_dataframe.iterrows():
        logger.log(
            (
                f"{index + 1}. "
                f"상품번호:{row.get('상품번호', '')} | "
                f"리뷰구분:{row.get('리뷰구분', '')} | "
                f"평점:{row.get('구매자평점', '')} | "
                f"전시상태:{row.get('전시상태', '')} | "
                f"리뷰등록일:{row.get('리뷰등록일', '')} | "
                f"상품명:{row.get('상품명', '')}"
            ),
            level="INFO",
            also_to_report=True,
        )