from utils.global_logger import logger


import pandas as pd
import os
from utils.excel.excel_utils import make_input_file_path, make_output_file_path
import config.settings as settings

from config.settings import FILE_EXTENSION_xlsx, CURRENT_MARKET_NAME

from config.settings import FILE_EXTENSION_xlsx, CURRENT_MARKET_NAME
from utils.excel.excel_utils import make_input_file_path, make_output_file_path, read_xls_all_sheets, save_excel_with_sheets,read_and_clean_first_sheet,read_xlsx_all_sheets
from utils.json.json_util import load_config
from imageFilter.excel.excel_handler_xlsx import process_imageFiltering_excel_file_xlsx
from utils.excel.excel_split import split_excel_by_rows
from rotationFile.rotation_task_manager import generate_tasks_from_config, process_first_sheet
from productNaming.name_handler import process_namingChange_excel_file
from rotationFile.rotation_excel_edit_util import clear_column_data, add_prefix_to_column
from rotationFile.rotation_excel_edit_util import update_column_to_9999, adjust_column_by_percentage, swap_image_column
from utils.excel.excel_get_data import get_folder_name, get_market_name
from rotationFile.rotation_market_process import market_process
from utils.excel.excel_utils import get_naver_modified_excel, save_excel_for_godo, set_dual_column_headers, save_excel_modified_naver_xlsx

def add_prefix_to_seller_code(df, column_name="판매자 상품코드", prefix="SP-"):
    """
    특정 열의 값 앞에 접두사를 추가하고, 기존 문자열에 '-'가 포함된 경우 '-' 앞쪽 문자열을 제거하는 함수.

    ✅ 주요 기능:
    1. 문자열에 '-'가 포함된 경우, '-' 앞의 내용을 제거한 후 접두사 추가 (예: "ABC-123" → "SP-123")
    2. 해당 열의 모든 값 앞에 접두사 추가 (예: "SP-" + 기존 값)

    :param df: 데이터프레임 (DataFrame)
    :param column_name: 변경할 열 이름 (기본값: "판매자 상품코드")
    :param prefix: 추가할 접두사 (기본값: "SP-")
    :return: 변경된 데이터프레임
    """
    try:
        # ✅ 특정 열이 존재하는지 확인
        if column_name not in df.columns:
            raise ValueError(f"❌ '{column_name}' 열이 데이터프레임에 존재하지 않습니다.")

        # ✅ '-'가 포함된 경우 '-' 앞의 문자열 제거 후 접두사 추가
        def process_code(value):
            value = str(value)  # 문자열 변환
            if '-' in value:
                value = value.split('-', 1)[1]  # 첫 번째 '-' 이후의 문자열만 남김
            return prefix + value  # 접두사 추가

        # ✅ 변경된 값 적용
        df[column_name] = df[column_name].apply(process_code)

        # ✅ 변경 완료 로그 출력
        logger.log(f"✅ '{column_name}' 열 값 변경 완료. (예시: {df[column_name].iloc[0]})", level="INFO")

        return df

    except Exception as e:
        logger.log(f"❌ '{column_name}' 접두사 추가 중 오류 발생: {e}", level="ERROR")
        raise


def change_product_excel(first_sheet_data):
    """
    상품 데이터에 여러 가지 필터를 적용하는 함수.

    ✅ 주요 기능:
    1. "판매자 상품코드" 열에 "SP-" 접두사 추가

    (추후 다른 필터 기능 추가 예정)

    :param first_sheet_data: 첫 번째 시트의 데이터프레임
    :return: 변경된 데이터프레임
    """
    try:
        # ✅ "판매자 상품코드" 접두사 추가 함수 호출
        first_sheet_data = add_prefix_to_seller_code(first_sheet_data)

        # ✅ 다른 필터 기능 추가 예정

        return first_sheet_data

    except Exception as e:
        logger.log(f"❌ 상품 데이터 변경 중 오류 발생: {e}", level="ERROR")
        raise




def make_optimize_product_excel(file_path, base_file_name):

    # 리포트 파일명 생성
    logger.prepend_report_file_name(base_file_name)

    # 읽을 파일경로 출력 파일 이름 설정
    excel_file_path = make_input_file_path(file_path, base_file_name)
    output_file_path = make_output_file_path(file_path, base_file_name, "_rotatet_output", FILE_EXTENSION_xlsx)
    _, file_extension = os.path.splitext(base_file_name)


    # 모든 시트 읽기(파일확장명에 따라)
    if file_extension.lower() == ".xlsx":
        sheets = read_xlsx_all_sheets(excel_file_path)  # .xlsx 파일 처리
    elif file_extension.lower() == ".xls":
        sheets = read_xls_all_sheets(excel_file_path)  # .xls 파일 처리
    else:
        raise ValueError(f"Unsupported file format: {file_extension}. Only '.xls' and '.xlsx' are supported.")

    # ✅ 1. 첫 번째 행을 보관하면서 첫 번째 시트 데이터 가져오기
    first_sheet_name, first_row_values, first_sheet_data = get_naver_modified_excel(sheets)

    # 마켓별 초기설정
    processed_sheet_data = change_product_excel(first_sheet_data)


    # 📄 **엑셀 파일 저장 (모든 시트 포함)**
    save_excel_modified_naver_xlsx(sheets, output_file_path, first_row_values, processed_sheet_data, first_sheet_name)