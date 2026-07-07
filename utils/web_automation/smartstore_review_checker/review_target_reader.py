# utils/web_automation/smartstore_review_checker/review_target_reader.py

"""
스마트스토어 리뷰 비교 대상 상품 파일 읽기 모듈

역할:
- 리뷰 통합본과 비교할 상품군 엑셀/CSV 파일을 읽는다.
- 상품번호(스마트스토어), 판매자상품코드, 상품명 등 필요한 컬럼을 정리한다.
- 이후 리뷰 통합본의 상품번호와 매칭할 수 있는 표준 DataFrame을 만든다.
"""

import os

import pandas as pd

from utils.global_logger import logger


REQUIRED_TARGET_COLUMNS = [
    "상품번호(스마트스토어)",
    "판매자상품코드",
]


OPTIONAL_TARGET_COLUMNS = [
    "그룹상품번호",
    "상품명",
    "채널",
    "스마트스토어전용 상품명",
]


def clean_text_value(value):
    """
    엑셀/CSV에서 읽은 값을 문자열로 정리한다.
    """

    if value is None:
        return ""

    text = str(value).strip()

    if text.lower() in ["nan", "none", "nat"]:
        return ""

    return text


def clean_product_no(value):
    """
    상품번호 값을 문자열로 정리한다.

    엑셀에서 숫자형으로 읽혀 1234567890.0처럼 되는 경우를 방지한다.
    """

    text = clean_text_value(value)

    if not text:
        return ""

    if text.endswith(".0"):
        text = text[:-2]

    return text.strip()


def read_target_excel_file(file_path):
    """
    비교 대상 상품 엑셀 파일을 읽는다.
    """

    dataframe = pd.read_excel(
        file_path,
        dtype=str,
    )

    return dataframe


def read_target_csv_file(file_path):
    """
    비교 대상 상품 CSV 파일을 읽는다.

    현재는 엑셀 사용 예정이지만,
    기존 상품목록 CSV와도 호환되도록 유지한다.
    """

    encoding_list = [
        "utf-8-sig",
        "cp949",
        "euc-kr",
    ]

    last_error = None

    for encoding in encoding_list:
        try:
            dataframe = pd.read_csv(
                file_path,
                dtype=str,
                encoding=encoding,
                sep=None,
                engine="python",
            )

            return dataframe

        except UnicodeDecodeError as error:
            last_error = error
            continue

    raise ValueError(
        f"비교 대상 상품 파일 인코딩을 확인하지 못했습니다: {last_error}"
    )


def validate_target_columns(dataframe):
    """
    비교 대상 상품 파일에 필요한 기본 컬럼이 있는지 확인한다.
    """

    missing_columns = [
        column
        for column in REQUIRED_TARGET_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"비교 대상 상품 파일에 필요한 열이 없습니다: {missing_columns}"
        )


def normalize_target_dataframe(dataframe):
    """
    비교 대상 상품 DataFrame을 표준화한다.
    """

    dataframe = dataframe.copy()

    dataframe.columns = [
        clean_text_value(column)
        for column in dataframe.columns
    ]

    dataframe = dataframe.dropna(how="all")
    dataframe = dataframe.fillna("")

    validate_target_columns(dataframe)

    dataframe["상품번호(스마트스토어)"] = (
        dataframe["상품번호(스마트스토어)"]
        .apply(clean_product_no)
    )

    dataframe["판매자상품코드"] = (
        dataframe["판매자상품코드"]
        .apply(clean_text_value)
    )

    for column in OPTIONAL_TARGET_COLUMNS:
        if column in dataframe.columns:
            dataframe[column] = dataframe[column].apply(clean_text_value)
        else:
            dataframe[column] = ""

    # 스마트스토어 상품번호와 판매자상품코드가 없는 행은 제외
    dataframe = dataframe[
        dataframe["상품번호(스마트스토어)"] != ""
    ].copy()

    dataframe = dataframe[
        dataframe["판매자상품코드"] != ""
    ].copy()

    # 채널 컬럼이 있는 경우 스마트스토어 행만 사용
    if "채널" in dataframe.columns:
        dataframe = dataframe[
            (dataframe["채널"] == "")
            | (dataframe["채널"] == "스마트스토어")
        ].copy()

    # 비교용 표준 상품번호 컬럼 추가
    dataframe["상품번호"] = dataframe["상품번호(스마트스토어)"]

    selected_columns = [
        "상품번호",
        "상품번호(스마트스토어)",
        "판매자상품코드",
        "그룹상품번호",
        "상품명",
        "채널",
        "스마트스토어전용 상품명",
    ]

    dataframe = dataframe[selected_columns].copy()

    return dataframe

def get_target_file_paths_from_folder(folder_path):
    """
    비교 대상 상품 폴더 안의 읽을 수 있는 파일 목록을 가져온다.

    주의:
    - 리뷰필터링완료_output 파일은 결과 파일이므로 비교 대상에서 제외한다.
    """

    if not os.path.exists(folder_path):
        raise FileNotFoundError(
            f"비교 대상 상품 폴더를 찾을 수 없습니다: {folder_path}"
        )

    allowed_extensions = [
        ".xlsx",
        ".xls",
        ".csv",
    ]

    exclude_keywords = [
        "리뷰필터링완료_output",
        "review_filter_output",
    ]

    file_paths = []

    for file_name in os.listdir(folder_path):
        if file_name.startswith("~$"):
            continue

        # 결과 파일은 다음 실행 시 비교 대상 상품 파일로 선택되면 안 되므로 제외
        if any(keyword in file_name for keyword in exclude_keywords):
            continue

        file_path = os.path.join(folder_path, file_name)

        if not os.path.isfile(file_path):
            continue

        _, file_extension = os.path.splitext(file_name)
        file_extension = file_extension.lower()

        if file_extension in allowed_extensions:
            file_paths.append(file_path)

    file_paths.sort(
        key=lambda path: os.path.getmtime(path),
        reverse=True,
    )

    return file_paths

def resolve_review_target_file_path(file_path_or_folder_path):
    """
    비교 대상 상품 경로가 파일이면 그대로 사용하고,
    폴더이면 폴더 안의 최신 엑셀/CSV 파일 1개를 사용한다.
    """

    if not file_path_or_folder_path:
        raise ValueError("비교 대상 상품 파일 또는 폴더 경로가 비어 있습니다.")

    if os.path.isfile(file_path_or_folder_path):
        return file_path_or_folder_path

    if os.path.isdir(file_path_or_folder_path):
        file_paths = get_target_file_paths_from_folder(
            file_path_or_folder_path
        )

        if not file_paths:
            raise ValueError(
                (
                    "비교 대상 상품 폴더 안에 읽을 파일이 없습니다.\n"
                    f"폴더: {file_path_or_folder_path}"
                )
            )

        selected_file_path = file_paths[0]

        logger.log(
            (
                "[비교 대상 상품 파일 자동 선택]\n"
                f"- 폴더: {file_path_or_folder_path}\n"
                f"- 선택파일: {selected_file_path}\n"
                f"- 후보파일수: {len(file_paths)}개"
            ),
            level="INFO",
            also_to_report=True,
            emoji_key="스마트스토어",
        )

        return selected_file_path

    raise FileNotFoundError(
        f"비교 대상 상품 파일 또는 폴더를 찾을 수 없습니다: {file_path_or_folder_path}"
    )

def read_review_target_file(file_path):
    """
    리뷰 통합본과 비교할 상품군 파일을 읽는다.

    file_path에는 파일 경로 또는 폴더 경로를 넣을 수 있다.

    지원 형식:
    - .xlsx
    - .xls
    - .csv
    """

    resolved_file_path = resolve_review_target_file_path(file_path)

    _, file_extension = os.path.splitext(resolved_file_path)
    file_extension = file_extension.lower()

    logger.log(
        f"[비교 대상 상품 파일 읽기 시작] {resolved_file_path}",
        level="INFO",
        also_to_report=True,
        emoji_key="스마트스토어",
        separator="1line",
    )

    if file_extension in [".xlsx", ".xls"]:
        dataframe = read_target_excel_file(resolved_file_path)

    elif file_extension == ".csv":
        dataframe = read_target_csv_file(resolved_file_path)

    else:
        raise ValueError(
            f"지원하지 않는 비교 대상 상품 파일 형식입니다: {file_extension}"
        )

    target_dataframe = normalize_target_dataframe(dataframe)

    target_dataframe.attrs["source_file_path"] = resolved_file_path
    target_dataframe.attrs["source_folder_path"] = os.path.dirname(
    resolved_file_path
    )

    logger.log(
        (
            "[비교 대상 상품 파일 읽기 완료]\n"
            f"- 파일: {resolved_file_path}\n"
            f"- 상품행: {len(target_dataframe)}개\n"
            f"- 고유상품: {target_dataframe['상품번호'].nunique()}개"
        ),
        level="INFO",
        also_to_report=True,
        emoji_key="스마트스토어",
    )

    return target_dataframe

def print_target_preview(target_dataframe, row_count=5):
    """
    비교 대상 상품 파일의 앞부분을 로그로 확인한다.
    """

    preview_dataframe = target_dataframe.head(row_count)

    logger.log(
        f"[비교 대상 상품 미리보기] 상위 {row_count}개 행",
        level="INFO",
        also_to_report=True,
        emoji_key="스마트스토어",
    )

    for index, row in preview_dataframe.iterrows():
        logger.log(
            (
                f"{index + 1}. "
                f"판매자상품코드:{row.get('판매자상품코드', '')} | "
                f"상품번호:{row.get('상품번호', '')} | "
                f"그룹상품번호:{row.get('그룹상품번호', '')} | "
                f"채널:{row.get('채널', '')} | "
                f"상품명:{row.get('상품명', '')}"
            ),
            level="INFO",
            also_to_report=True,
        )