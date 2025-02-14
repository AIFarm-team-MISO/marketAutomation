from utils.global_logger import logger

import os
import pandas as pd
from utils.excel.excel_utils import make_input_file_path, make_output_file_path
import config.settings as settings

from config.settings import FILE_EXTENSION_xls, FILE_EXTENSION_xlsx, CURRENT_MARKET_NAME
from utils.excel.excel_utils import make_input_file_path, make_output_file_path, read_xls_all_sheets, save_excel_with_sheets,read_and_clean_first_sheet,read_xlsx_all_sheets
from utils.excel.excel_utils import remove_rows_gododata, save_excel_for_godo, set_dual_column_headers, save_excel_for_godo_as_xls, save_excel_for_godo_as_xls_fixed

from rotationFile.rotation_excel_edit_util import input_column_with_str,remove_food_category_rows, remove_duplicate_rows
from rotationFile.rotation_excel_edit_util import remove_options_rows, clean_search_keywords, update_column_value

def make_rotation_godo(file_path, base_file_name):
    '''
    1. < 카테고리 번호* >열 비어있는 행삭제
    2. < 상품명* >열 비어있는 행삭제
    3. < 카테고리 번호* >열이 음식카테고리인 경우 행삭제
    4. < 상품명* >열이 중복된 경우 행삭제
    5. < 선택사항 타입 >열 비어있지 않은경우 제거
    
    6. < 검색어(태그) >열 의 문자열에서(예:귀후비개,귀파개,led,라이트,손전등) 중복 키워드 제거, 숫자 및 특수문자 제거, 문자열을 29바이트 내외로 조정
    7. < 요약정보 상품군 코드* > 35로 모두변경
    8. < 요약정보 전항목 상세설명 참조 > "Y" 로 모두변경
'''

    logger.prepend_report_file_name(base_file_name)

    try:

        # 읽을 파일경로 출력 파일 이름 설정
        excel_file_path = make_input_file_path(file_path, base_file_name)
        output_file_name = make_output_file_path(file_path, base_file_name, "_godo_output", FILE_EXTENSION_xls)
        _, file_extension = os.path.splitext(base_file_name)

    
        # 모든 시트 읽기(파일확장명에 따라)
        if file_extension.lower() == ".xlsx":
            sheets = read_xlsx_all_sheets(excel_file_path)  # .xlsx 파일 처리
        elif file_extension.lower() == ".xls":
            sheets = read_xls_all_sheets(excel_file_path)  # .xls 파일 처리
        else:
            raise ValueError(f"Unsupported file format: {file_extension}. Only '.xls' and '.xlsx' are supported.")
        
        

        # 첫 번째 시트를 읽고 비어 있는 행 제거
        first_sheet_name, first_sheet_data = remove_rows_gododata(sheets)


        modify_sheet = input_column_with_str(first_sheet_data, "카테고리 코드", '3')

        #상위 5줄 출력
        logger.log(modify_sheet.head(5))

        save_excel_for_godo_as_xls_fixed(sheets, output_file_name, modify_sheet, first_sheet_name)

        


    except Exception as e:
        logger.log(f"고도몰 순환파일 자동화중 에러가 발생: {e}", level="ERROR")
        raise