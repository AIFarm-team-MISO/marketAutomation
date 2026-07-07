
import os
import pandas as pd
from utils.global_logger import logger


from utils.excel.excel_utils import (
    make_input_file_path,
    read_xls_all_sheets,
    read_xlsx_all_sheets,
    read_and_clean_first_sheet,
)


"""
스마트스토어 리뷰 확인용 입력 엑셀 처리 모듈

역할:
- 입력 엑셀 파일 경로 생성
- xlsx / xls 파일 읽기
- 첫 번째 시트 정리
- 스마트스토어 상품번호와 판매자상품코드 추출
- 리뷰 확인 대상 리스트 생성
"""

# utils/web_automation/smartstore_review_checker/smartstore_review_input_reader.py

"""
스마트스토어 리뷰 확인용 입력 엑셀 처리 모듈

역할:
- 입력 엑셀 파일 읽기
- 첫 번째 시트 정리
- 상품번호(스마트스토어), 판매자상품코드, 상품명 추출
- 리뷰 확인 대상 리스트 생성
"""

import os

from utils.excel.excel_utils import (
    make_input_file_path,
    read_xls_all_sheets,
    read_xlsx_all_sheets,
    read_and_clean_first_sheet,
)



def read_excel_file(file_path, base_file_name):
    """
    엑셀 또는 CSV 파일을 읽고 데이터프레임을 반환한다.

    지원 형식:
    - .xlsx : 모든 시트 읽기 후 첫 번째 시트 반환
    - .xls  : 모든 시트 읽기 후 첫 번째 시트 반환
    - .csv  : CSV 자체를 첫 번째 시트처럼 반환
    """

    input_file_path = make_input_file_path(file_path, base_file_name)
    _, file_extension = os.path.splitext(base_file_name)

    file_extension = file_extension.lower()

    # -------------------------------------------------
    # 1. xlsx 파일 처리
    # -------------------------------------------------
    if file_extension == ".xlsx":
        sheets = read_xlsx_all_sheets(input_file_path)
        first_sheet_data = read_and_clean_first_sheet(sheets)

        return first_sheet_data

    # -------------------------------------------------
    # 2. xls 파일 처리
    # -------------------------------------------------
    if file_extension == ".xls":
        sheets = read_xls_all_sheets(input_file_path)
        first_sheet_data = read_and_clean_first_sheet(sheets)

        return first_sheet_data

    # -------------------------------------------------
    # 3. csv 파일 처리
    # -------------------------------------------------
    if file_extension == ".csv":
        first_sheet_data = read_csv_file(input_file_path)

        return first_sheet_data

    # -------------------------------------------------
    # 4. 지원하지 않는 파일 형식
    # -------------------------------------------------
    raise ValueError(
        f"Unsupported file format: {file_extension}. "
        "Only '.xls', '.xlsx', and '.csv' are supported."
    )



def read_csv_file(csv_file_path):
    """
    CSV 파일을 읽어 데이터프레임으로 반환한다.

    네이버/엑셀 CSV는 인코딩이 utf-8-sig, cp949, euc-kr 중 하나일 수 있으므로
    순서대로 시도한다.
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
                csv_file_path,
                dtype=str,
                encoding=encoding,
                sep=None,
                engine="python",
            )

            dataframe.columns = [
                str(column).strip()
                for column in dataframe.columns
            ]

            dataframe = dataframe.dropna(how="all")
            dataframe = dataframe.fillna("")

            return dataframe

        except UnicodeDecodeError as error:
            last_error = error
            continue

    raise ValueError(
        f"CSV 파일을 읽는 중 인코딩 문제가 발생했습니다: {last_error}"
    )


def clean_excel_value(value):
    """
    엑셀 셀 값을 문자열로 정리한다.
    """

    if value is None:
        return ""

    text = str(value).strip()

    if text.lower() in ["nan", "none"]:
        return ""

    return text


def clean_product_no(value):
    """
    엑셀에서 읽은 상품번호를 문자열로 정리한다.

    엑셀에서 상품번호가 숫자형으로 읽히면
    8751431770.0 형태가 될 수 있으므로 끝의 .0을 제거한다.
    """

    text = clean_excel_value(value)

    if not text:
        return ""

    if text.endswith(".0"):
        text = text[:-2]

    return text.strip()


def validate_review_input_columns(dataframe):
    """
    리뷰 확인에 필요한 필수 열이 있는지 확인한다.
    """

    required_columns = [
        "상품번호(스마트스토어)",
        "판매자상품코드",
    ]

    missing_columns = [
        column_name
        for column_name in required_columns
        if column_name not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"스마트스토어 리뷰 확인에 필요한 열이 없습니다: {missing_columns}"
        )


def extract_review_targets_from_dataframe(dataframe, store_name):
    """
    엑셀 데이터프레임에서 리뷰 확인 대상 상품 목록을 추출한다.

    추출 기준:
    - 상품번호(스마트스토어)가 있어야 한다.
    - 판매자상품코드가 있어야 한다.
    - 채널 열이 있는 경우 '스마트스토어'만 사용한다.

    반환 예:
    [
        {
            "store_name": "misosupu",
            "seller_product_code": "SP-3MR_20230",
            "smartstore_product_no": "8751431770",
            "group_product_no": "",
            "product_name": "이나우스 일회용 용기 접시 200mm 10개입",
            "smartstore_only_product_name": "이나우스 일회용 용기 접시 200mm 10개입",
            "channel": "스마트스토어",
        }
    ]
    """

    validate_review_input_columns(dataframe)

    review_targets = []

    for _, row in dataframe.iterrows():
        smartstore_product_no = clean_product_no(
            row.get("상품번호(스마트스토어)", "")
        )

        seller_product_code = clean_excel_value(
            row.get("판매자상품코드", "")
        )

        group_product_no = clean_product_no(
            row.get("그룹상품번호", "")
        )

        product_name = clean_excel_value(
            row.get("상품명", "")
        )

        channel = clean_excel_value(
            row.get("채널", "")
        )

        smartstore_only_product_name = clean_excel_value(
            row.get("스마트스토어전용 상품명", "")
        )

        # 채널 열이 있고 스마트스토어가 아니면 제외
        if channel and channel != "스마트스토어":
            continue

        # 상품번호가 없으면 URL 생성이 불가능하므로 제외
        if not smartstore_product_no:
            continue

        # 판매자상품코드가 없으면 결과 정리에 불리하므로 제외
        if not seller_product_code:
            continue

        review_targets.append(
            {
                "store_name": store_name,
                "seller_product_code": seller_product_code,
                "smartstore_product_no": smartstore_product_no,
                "group_product_no": group_product_no,
                "product_name": product_name,
                "smartstore_only_product_name": smartstore_only_product_name,
                "channel": channel,
            }
        )

    return review_targets

