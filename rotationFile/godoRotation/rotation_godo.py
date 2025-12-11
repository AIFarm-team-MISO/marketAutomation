from utils.global_logger import logger

import os
import pandas as pd
from utils.excel.excel_utils import make_input_file_path, make_output_file_path
import config.settings as settings

from config.settings import FILE_EXTENSION_xls, FILE_EXTENSION_xlsx, CURRENT_MARKET_NAME
from utils.excel.excel_utils import make_input_file_path, make_output_file_path, read_xls_all_sheets, save_excel_with_sheets,read_and_clean_first_sheet,read_xlsx_all_sheets
from utils.excel.excel_utils import remove_rows_gododata, save_excel_for_godo, set_dual_column_headers, save_excel_for_godo_as_xls_fixed

from rotationFile.rotation_excel_edit_util import input_ship_column,remove_food_category_rows, remove_duplicate_rows
from rotationFile.rotation_excel_edit_util import remove_options_rows, clean_search_keywords, update_column_value
from utils.excel.excel_get_data import get_folder_name, get_market_name
from utils.json.json_util import load_config
from imageFilter.excel.excel_handler_xlsx import godo_imageFiltering_excel
from productNaming.name_handler import godo_process_namingChange_excel_file
from utils.excel.excel_split import godo_split_excel_by_rows
from rotationFile.rotation_market_process import godo_market_process



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
        

        # ✅ 1. 첫 번째 행을 보관하면서 첫 번째 시트 데이터 가져오기
        first_sheet_name, first_row_values, first_sheet_data = remove_rows_gododata(sheets)


        # [고도몰-파타르시스]_파라브러_GPT_가격대마진
        # ✅ 2. 마켓명 셋팅
        logger.log(f"파일이름:  {base_file_name}", also_to_report=True, separator="none")
        platform_name, market, domename = extract_market_and_supplier(base_file_name)
        logger.log(f"플랫폼 : {platform_name}, 마켓명: {market}, 도매이름: {domename}", also_to_report=True, separator="none")
        settings.CURRENT_MARKET_NAME = platform_name # 설정파일 값을 변경


        # ✅ 마켓별 초기설정
        processed_sheet_data = godo_market_process(first_sheet_data, platform_name, market, domename)



        # ✅ 3. 배송관련 데이터 입력 : 초기셋팅 완료 
        shiping_code = get_shiping_code(market, domename)  
        modify_sheet = input_ship_column(processed_sheet_data, "배송비 고유번호", int(shiping_code))

        # ✅ 4.이미지 필터링 : '이미지명' 칼럼 에서 값을 가져와 이미지내용을 필터해서 받아온값으로 이미지리스트를 만들어야함 
        image_filtered_df = godo_imageFiltering_excel(file_path, base_file_name, modify_sheet)
        
        # ✅ 5.상품명 가공 
        naming_process_df = godo_process_namingChange_excel_file(file_path, base_file_name, 'GPT조합', task_type="auto", sheets=image_filtered_df)

        # ✅ 6. 행분할 및 엑셀저장 
        godo_split_excel_by_rows(
            file_path, 
            base_file_name, 
            task_type="auto", 
            sheets=sheets, 
            modify_data=naming_process_df, 
            first_sheet_name=first_sheet_name, 
            first_row_values = first_row_values
        )

        # ✅ 7. 엑셀저장 
        # 고도몰-블루채널 관리자페이지의 마켓별 배송비 번호 셋팅, 배송,교환등 번호확인  -> 마켓설정파일 추가 
        


        

        


    except Exception as e:
        logger.log(f"고도몰 순환파일 자동화중 에러가 발생: {e}", level="ERROR")
        raise

def get_shiping_code(market_name, supplier_name):
    """
    마켓명과 도매이름에 따라 카테고리 코드를 결정하는 함수.

    :param market_name: 추출된 마켓명 (예: "파타르시스")
    :param supplier_name: 추출된 도매이름 (예: "파라브러")
    :return: 카테고리 코드 (예: "3")
    """
    category_mapping = {
        "파타르시스": {
            "파라브러": "1",
            "필우": "6",
            "비온": "11",
            "셀프": "8",
            "젠트": "7", 
            "3MR-생건": "9"
        },
        "블루채널": {
            "파라브러": "1",
            "더드림": "6",
            "글로벌": "7",
            "젠트": "8",
            "비온": "9",
            "친구": "10",
            "3MR-생건": "9",
            "도매토피아-GT": "5"
        },
    }

    # 마켓명과 도매이름이 일치하는 경우 반환, 없으면 기본값 반환
    return category_mapping.get(market_name, {}).get(supplier_name, "1")  # 기본값 "1"

import re
import os



def extract_market_and_supplier(file_name):
    """
    파일명에서 플랫폼명, 마켓명, 도매이름을 추출하는 함수.

    :param file_name: 원본 파일명 (예: "[고도몰-파타르시스]_파라브러_GPT_가격대마진.xls")
    :return: (플랫폼명, 마켓명, 도매이름) 튜플 (예: ("고도몰", "파타르시스", "파라브러"))
    """
    # 1. 확장자 제거
    file_name_without_ext, _ = os.path.splitext(file_name)

    # 2. '_' 기준으로 분리
    parts = file_name_without_ext.split('_')

    if len(parts) < 2:
        raise ValueError(f"잘못된 파일명 형식: {file_name}")

    # 3. 마켓명과 플랫폼명 추출 (대괄호 제거 및 '-' 기준으로 분리)
    market_part = parts[0]  # 예: "[고도몰-파타르시스]"
    market_match = re.search(r"\[(.*?)\]", market_part)

    if not market_match:
        raise ValueError(f"마켓명을 찾을 수 없음: {file_name}")

    # "고도몰-파타르시스"에서 플랫폼과 마켓 분리
    market_full = market_match.group(1)  # 예: "고도몰-파타르시스"
    market_parts = market_full.split('-')

    if len(market_parts) != 2:
        raise ValueError(f"플랫폼과 마켓명을 분리할 수 없음: {market_full}")

    platform_name = market_parts[0]  # 예: "고도몰"
    market_name = market_parts[1]    # 예: "파타르시스"

    # 4. 도매이름 추출 (두 번째 '_' 이후 값)
    supplier_name = parts[1]  # 예: "파라브러"

    return platform_name, market_name, supplier_name


