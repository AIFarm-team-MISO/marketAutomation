from utils.global_logger import logger

import os
import pandas as pd
from utils.excel.excel_utils import make_input_file_path, make_output_file_path
from utils.excel.excel_utils import read_xls_all_sheets, save_excel_with_sheets, read_xlsx_all_sheets
from config.settings import FILE_EXTENSION_xls, FILE_EXTENSION_xlsx, FILTERED_URL_FILE
from imageFilter.excel.image_processing_xlsx import process_image_urls_xlsx
from utils.excel.excel_process_utils import insert_excel_column, sort_sheet, colum_highlight_sheet, delete_rows_by_condition, colum_highlight_sheet
from utils.excel.excel_process_utils import insert_excel_columns_with_values, extract_main_image_urls
from utils.validate.validate_dataframe import validate_data_integrity
from utils.excel.excel_utils import read_and_clean_first_sheet
from imageFilter.imageFilterDictionary.dictionary_handler import load_dictionary, save_image_filter_dictionary


# 현재 파일 위치 기준으로 JSON 파일 경로 설정
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, "rotationInfo.json")

def process_imageFiltering_excel_file_xlsx(file_path, base_file_name, task_type="single", sheets=None):
    """
    이미지 필터링 작업을 처리하는 함수 (단독 작업 및 자동화 작업 지원)
    :param file_path: 파일 경로
    :param base_file_name: 기본 파일 이름
    :param task_type: 작업 타입 ("single" 또는 "auto")
    """

    existing_column_name = "목록 이미지*"
    new_column_name = "필터링결과"

    # 파일 확장자 확인 
    if sheets is None: # 단독실행일경우 
        excel_file_path = make_input_file_path(file_path, base_file_name)
        # output_file_name = make_output_file_path(file_path, base_file_name, "_image_filtered_output", FILE_EXTENSION_xlsx)
        _, file_extension = os.path.splitext(base_file_name)

    
        # 모든 시트 읽기(파일확장명에 따라)
        if file_extension.lower() == ".xlsx":
            sheets = read_xlsx_all_sheets(excel_file_path)  # .xlsx 파일 처리
        elif file_extension.lower() == ".xls":
            sheets = read_xls_all_sheets(excel_file_path)  # .xls 파일 처리
        else:
            raise ValueError(f"Unsupported file format: {file_extension}. Only '.xls' and '.xlsx' are supported.")
        
        first_sheet_name, first_sheet_data = read_and_clean_first_sheet(sheets)

    else: # 시트가 제공된 경우, 첫 번째 시트 및 정제처리가 필요없음 : 자동화실행일 경우  
        first_sheet_data = sheets


    # logger.log(f"first_sheet_data: {first_sheet_data.index}", level="DEBUG")

    logger.log_separator()
    logger.log('🖼️  엑셀 칼럼 삽입 처리 🖼️')

    # 열 삽입
    modified_sheet = insert_excel_column(
        first_sheet_data=first_sheet_data,  # 첫 번째 시트 사용
        existing_column_name=existing_column_name,
        new_column_name=new_column_name,
        position="before",
        offset=1
    )

    image_column_name = "목록 이미지*"
    seller_code_column_index = "판매자 관리코드"

    # 이미지 필터링 
    filtered_sheets  = process_image_urls_xlsx(modified_sheet, image_column_name, seller_code_column_index, task_type)
    
    # 중복-문자있음 위로 정렬
    filtered_sort_sheets = sort_sheet(filtered_sheets, '필터링결과', "중복-문자있음")

    if task_type=="single":

        # 강조처리 파일명 생성 
        # 강조작업을 할 파일이름 : 정렬이후 "중복-문자있음" 행 빨간색 강조, 이후 엑셀파일에 저장됨
        highlight_output_file_name = make_output_file_path(file_path, base_file_name, "_image_filtered_highlight_output", FILE_EXTENSION_xlsx)
        colum_highlight_sheet(sheets, filtered_sort_sheets, '필터링결과', "중복-문자있음", highlight_output_file_name)

        logger.log(f" 이미지 필터링 : {task_type} 작업이 성공적으로 완료되었습니다.", level="INFO", also_to_report=True, separator="2line")
        
    elif task_type=="auto":

        #강조처리삭제 파일명 생성, 이곳 활성화시에는 validate_data_integrity(무결성)필요
        filtered_sort_complete_sheets, rows_to_delete_count = delete_rows_by_condition(filtered_sort_sheets, '필터링결과', "중복-문자있음")
        
        # 무결성 검증 호출
        validate_data_integrity(
            initial_count=len(filtered_sort_sheets),                        #최초갯수
            filtered_sort_complete_sheets=filtered_sort_complete_sheets,    #결과시트
            processed_count=rows_to_delete_count,                           #처리된갯수
            task_name="중복-문자있음 행삭제",                                 #처리명
            task_type="deletion"                                            #처리타입
        )

        # 자동화 작업: 작업 완료 메시지만 출력
        logger.log(f" 이미지 필터링  : {task_type} 작업이 성공적으로 완료되었습니다.", level="INFO", also_to_report=True, separator="2line")

        # 결과 반환
        return filtered_sort_complete_sheets
    



def godo_imageFiltering_excel(file_path, base_file_name,sheets):
    """
    이미지 필터링 작업을 처리하는 함수 (단독 작업 및 자동화 작업 지원)
    :param file_path: 파일 경로
    :param base_file_name: 기본 파일 이름
    :param task_type: 작업 타입 ("single" 또는 "auto")
    """

    logger.log_separator()
    logger.log('🖼️  고도몰 이미지필터링 작업 시작 🖼️')

    task_type = "single"

    base_image_cloumn = "이미지명"
    filter_image_column_name = "썸네일이미지"
    filtered_result_column_name = "필터링결과"
    seller_code_column_index = "자체상품코드"

    # ✅ 1. 이미지 컬럼 추가 : 기존 이미지명 앞에 필터링결과 및 썸네일이미지 컬럼 추가
    updated_sheets = insert_excel_columns_with_values(sheets, base_image_cloumn, filter_image_column_name, filtered_result_column_name)


    # ✅ 2. 이미지 필터링 
    filtered_sheets  = process_image_urls_xlsx(updated_sheets, filter_image_column_name, seller_code_column_index, task_type)
    
    # ✅ 3. 중복-문자있음 위로 정렬
    filtered_sort_sheets = sort_sheet(filtered_sheets, filtered_result_column_name, "중복-문자있음")

    # ✅ 4. "중복-문자있음" 행삭제 :이곳 활성화시에는 validate_data_integrity(무결성)필요
    filtered_sort_complete_sheets, rows_to_delete_count = delete_rows_by_condition(filtered_sort_sheets, filtered_result_column_name, "중복-문자있음")
    
    # ✅ 5. 무결성 검증 호출
    validate_data_integrity(
        initial_count=len(filtered_sort_sheets),                        #최초갯수
        filtered_sort_complete_sheets=filtered_sort_complete_sheets,    #결과시트
        processed_count=rows_to_delete_count,                           #처리된갯수
        task_name="중복-문자있음 행삭제",                                 #처리명
        task_type="deletion"                                            #처리타입
    )
    # ✅ 6. **필터링된 컬럼 제거** (여기 추가!)
    columns_to_remove = [filter_image_column_name, filtered_result_column_name]

    for col in columns_to_remove:
        if col in filtered_sort_complete_sheets.columns:
            filtered_sort_complete_sheets.drop(columns=[col], inplace=True)
            logger.log(f"🗑️ '{col}' 컬럼 제거 완료.", level="INFO")

    # 자동화 작업: 작업 완료 메시지만 출력
    logger.log(f" 이미지 필터링  : {task_type} 작업이 성공적으로 완료되었습니다.", level="INFO", also_to_report=True, separator="2line")
    


    return filtered_sort_complete_sheets





