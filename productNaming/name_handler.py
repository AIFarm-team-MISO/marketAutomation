from utils.global_logger import logger

import os
import sys
import pandas as pd
from imageFilter.excel.file_handler import read_excel_file, save_excel_file
from config.settings import FILE_EXTENSION_xls
from config.settings import FILE_EXTENSION_xlsx, ROTATION_JSON_PATH
from config.settings import CURRENT_MARKET_NAME

from utils.excel.excel_utils import apply_filter_and_sort_xls, insert_column_before, apply_row_color_by_condition, update_seller_codes,rename_and_delete_columns, rename_and_modify_columns
from utils.excel.excel_utils import column_letter_to_index

from imageFilter.excel.url_filter import save_filtered_urls
from keywordOptimization.naver_api import generate_optimized_names
from keywordOptimization.product_info import ProductInfo, ProcessedProductInfo
from keywordOptimization.keyword_filter_never import apply_filters

from keywordDictionary.dictionary_loader import load_dictionary, save_dictionary, filtered_naming_in_dictionary
from keywordDictionary.keyword_extractor import extract_keywords
from keywordOptimization.gpt_result_generating import gpt_result_generate_name
from utils.progress.calculate_progress import calculate_estimates, run_filtering_item_process, print_progress_bar
from utils.excel.excel_utils import make_input_file_path, make_output_file_path, read_xls_all_sheets, save_excel_with_sheets,read_and_clean_first_sheet, read_xlsx_all_sheets
from utils.excel.excel_process_utils import insert_excel_column, sort_sheet, colum_highlight_sheet, delete_rows_by_condition, colum_highlight_sheet
from productNaming.nameing_validate import validate_name_code_list
from utils.validate.validate_index import validate_data_order
from utils.excel.excel_get_data import get_column_values_with_validation
from productNaming.naming_gpt_process import process_naming_list_with_gpt
from utils.json.json_util import load_config
from utils.excel.excel_get_data import get_folder_name, get_market_name

import config.settings as settings
# 현재 파일 위치 기준으로 JSON 파일 경로 설정
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, "rotationInfo.json")


import pandas as pd

'''
    현재의 데이터(예시) 
    gpt_data = {
        "기본상품명": "군인장병 야간독서등",
        "제품군": "독서등",
        "용도": ["야간독서", "군인장병"],
        "사양": ["LED"],
        "스타일": [],
        "기타 카테고리": [],
        "연관검색어": ["군인독서등", "야간독서조명", "LED독서등", "밤독서등", "야간스탠드"],
        "브랜드키워드": [],
        "고정키워드": ["군인장병", "야간독서등"]
        "네이버연관검색어": ["스탠드조명", "독서등"]
        "패턴": ["야간", "침대"]
    }
'''

def process_namingChange_excel_file(file_path, base_file_name, opt_type, task_type="single", sheets=None):
    """
    Parameters:
    - file_path (str): 엑셀 파일이 위치한 폴더 경로
    - base_file_name (str): 엑셀 파일 이름 (확장자 제외)
    - opt_type (str) : 가공형태 'GPT조합',  '상위검색'등 상품명 가공타입
    - task_type (str) : single 개별실행, auto 자동실행
    - sheets : 시트가 있는경우 자동실행

    """ 

    # 가공타입 설정 : 현재 GPT 연관검색어 
    opt_type = opt_type

    logger.log(f"▶️ 상품명가공시작 ▶️ 가공타입 : {opt_type} , 작업타입 : {task_type} ", level="INFO", also_to_report=True, separator="2line")
    
    # 파일 실행타입에 따른 시트데이터 생성
    if sheets is None: # 단독실행으로 편집된 시트데이터가 없는경우
        excel_file_path = make_input_file_path(file_path, base_file_name)
        output_file_name = make_output_file_path(file_path, base_file_name, "_namingChange_output", FILE_EXTENSION_xlsx)
        _, file_extension = os.path.splitext(base_file_name)

    
        # 모든 시트 읽기(파일확장명에 따라)
        if file_extension.lower() == ".xlsx":
            sheets = read_xlsx_all_sheets(excel_file_path)  # .xlsx 파일 처리
        elif file_extension.lower() == ".xls":
            sheets = read_xls_all_sheets(excel_file_path)  # .xls 파일 처리
        else:
            raise ValueError(f"Unsupported file format: {file_extension}. Only '.xls' and '.xlsx' are supported.")
        
        first_sheet_name, first_sheet_data = read_and_clean_first_sheet(sheets)

        # 대상시트에서 '폴더명' 이름 가져오기
        folder_name, split_folder_name, dome_name = get_folder_name(first_sheet_data, column_name="폴더명")

        # 순환파일 JSON 설정파일 로드 
        config = load_config(ROTATION_JSON_PATH)

        market_config = config.get(split_folder_name, {})
        if not market_config:  # market_config이 빈 딕셔너리 또는 None일 경우
            raise ValueError(f"JSON에 마켓 이름 '{split_folder_name}'이(가) 없습니다.")
        
        market_name, channel_name = get_market_name(split_folder_name)

    else: # 편집된 시트데이터가 넘어온 경우, 첫 번째 시트 및 정제처리가 필요없음 : 자동화실행
        first_sheet_data = sheets

        # 설정파일 값을 변경
        market_name = settings.CURRENT_MARKET_NAME
        

    if market_name == "쿠팡" or market_name == "11번가" or market_name == "고도몰":
        name_strength = 100
    elif market_name == "톡스토어":
        name_strength = 70
    else:  #쿠팡, 11번가 이외의 마켓 스마트스토어 등일경우
        name_strength = 50

    logger.log(f"상품명가공 플랫폼 : {market_name} , 글자수 : {name_strength}", also_to_report=True, separator="none")


    # ▶️ '상품명*' 앞에 새로운 열(가공결과) 삽입 (가공상품명의 결과를 추가하기 위해)
    modified_sheet = insert_excel_column(
        first_sheet_data=first_sheet_data,  # 첫 번째 시트 사용
        existing_column_name="상품명*",
        new_column_name="가공결과",
        position="before",
        offset=1
    )

    # 상품명 키워드사전 로드
    dictionary = load_dictionary()
    
    # 시트에서 상품명리스트 가져옴 
    naming_list = get_column_values_with_validation(modified_sheet, "상품명*")

    # 사전데이터와 비교한결과 튜플리스트 예: [("새로운문자열", naming_str) ,("새로운문자열", naming_str) ]
    filterd_list = filtered_naming_in_dictionary(dictionary, naming_list)
    # logger.log_list("필터링된 리스트", filterd_list, level="INFO") #필터링된 리스트

    # ▶️ gpt 비용, 시간 확인, 프로그램실행유무
    run_filtering_item_process(filterd_list, "상품명가공", task_type)
    #run_filtering_item_process(filterd_list, "상품명가공", "single")
    # run_filtering_item_process(filterd_list, "상품명가공", "auto")
    
    # 기본상품명 분석(메인과 보조키워드 추출) 및 연관검색어 추출
    logger.log(f"⏩ 기본상품명 분석(메인과 보조키워드 추출) 및 연관검색어 추출작업시작 ", level="INFO", also_to_report=True, separator="none")
    total_items, initial_existing_count, added_to_dictionary_count, extract_namingData_list = process_naming_list_with_gpt(dictionary, naming_list, missing_threshold=1)


    logger.log("▶️ GPT의 결과에 따른 가공 상품명 조합시작 ▶️", also_to_report=True, separator="2line")
    gpt_optimized_name_list = []  # 최종 결과를 담을 리스트
    basic_product_names = []  # 기본상품명 리스트

    for gptData in extract_namingData_list:

        try:
            # 현재 namingData에는 딕셔너리 값이 하나만 있으므로 메인키워드 데이터에 바로 접근
            main_keyword = list(gptData.keys())[0]  # 첫 번째 키 가져오기
            product_data = gptData[main_keyword]

            # 기본상품명 가져오기
            basic_product_name = product_data["기본상품명"]
            logger.log(f"검색타입 : {opt_type} , 처리 중인 메인 키워드: {main_keyword}, 상품명: {basic_product_name}")

            # 기본상품명 리스트에 저장
            basic_product_names.append(basic_product_name)

            # ▶️ 최적화된 상품명 생성
            optimized_name = gpt_result_generate_name(basic_product_name, dictionary, name_strength) 
            gpt_optimized_name_list.append(optimized_name)
        
        except Exception as e:  # 모든 예외 처리
            logger.log(f"⚠️ 상품명조합 중 예외 발생: {e}. namingData: {gptData}", level="ERROR")
            raise ValueError(f"⚠️ 상품명조합 중 예외 발생: {e}. namingData: {gptData}")

    '''
        - 기존시트에 가공상품명을 넣을때 지킬사항 -
        1. 기존에 편집된 시트데이터 modified_sheet는 상품명이 입력될때까지 변경이 일어나면 안된다
        2. modified_sheet에서 추출된 naming_list가  gpt_optimized_name_list로 만들어지기까지 리스트의 갯수에 변동이 있으면 안된다

        *** 위의 전제가 없다면 이후 기존상품명에 가공된 상품명이 매칭 안될 가능성이 있음
            단 modified_sheet에 가공상품명이 담긴 후에는 modified_sheet를 편집해도 문제가 없음 

    '''
    # 시트에 가공상품명 적용 전 검증로직 
    if len(modified_sheet) != len(gpt_optimized_name_list):
        raise ValueError(
            f"기존시트 데이터의 길이가 ({len(modified_sheet)}) 가공상품명 데이터 길이 ({len(gpt_optimized_name_list)} 와 매칭안됨)."
        )


    # ▶️ 시트에 가공상품명 적용 
    modified_sheet = modified_sheet.copy()
    modified_sheet["가공결과"] = gpt_optimized_name_list

    # ▶️ "판매자관리코드" 열 문자열 앞에 opt_type 추가 (만약 같은 접두사가 붙어있다면 붙이지 않음)
    modified_sheet["판매자 관리코드"] = modified_sheet["판매자 관리코드"].apply(
    lambda x: f"{opt_type}-{x}" if pd.notnull(x) and not str(x).startswith(f"{opt_type}-") else x
)


    # # ▶️ 작업 유형이 "single"인 경우 열 이름 변경 및 기존 열 삭제
    # if task_type == "auto":
    #     modified_sheet = modified_sheet.drop(columns=["상품명*"], errors="ignore")
    #     modified_sheet = modified_sheet.rename(columns={"가공결과": "상품명*"})

    #처리 완료 로그 출력
    logger.log(f"📌 상품명가공 처리결과.", level="INFO", also_to_report=True, separator="none")
    logger.log(f"💬 총 {total_items}개의 상품명 처리완료.", level="INFO", also_to_report=True, separator="none")
    logger.log(f"💬 사전에 이미 존재했던 기본상품명 수: {initial_existing_count}", level="INFO", also_to_report=True, separator="none")
    logger.log(f"💬 새로 추가된 기본상품명 수: {added_to_dictionary_count}", level="INFO", also_to_report=True, separator="none")
    logger.log_message_with_list("💡 기본상품명 :", basic_product_names, level="INFO", also_to_report=True)
    logger.log_message_with_list("🌟 가공결과 :", gpt_optimized_name_list, level="INFO", also_to_report=True)

    #가공타입을 판매자관리코드에 접두사로 추가 - 필요업음, 중복작업
    # modified_sheet = update_seller_codes(modified_sheet, "판매자 관리코드", opt_type)

    #기존 상품명열을 삭제하고 가공상품명으로 대체 - 필요업음, 중복작업
    # modified_sheet = rename_and_delete_columns(modified_sheet, "가공결과", "상품명*", "상품명*")

    # 가공상품명 열이름을 상품명 열이름으로 대체
    modified_sheet = rename_and_modify_columns(
        dataframe=modified_sheet,
        target_column="가공결과",           # A 열의 이름을 변경
        new_column_name="상품명*",         # A -> B
        change_column_name="기존상품명*"   # B -> B_new
    )
    
    if task_type == "auto":
        return modified_sheet
    else:
        save_excel_with_sheets(sheets, output_file_name, modified_sheet, first_sheet_name)


def godo_process_namingChange_excel_file(file_path, base_file_name, opt_type, task_type="single", sheets=None):
    """
    Parameters:
    - file_path (str): 엑셀 파일이 위치한 폴더 경로
    - base_file_name (str): 엑셀 파일 이름 (확장자 제외)
    - opt_type (str) : 가공형태 'GPT조합',  '상위검색'등 상품명 가공타입
    - task_type (str) : single 개별실행, auto 자동실행
    - sheets : 시트가 있는경우 자동실행

    """ 

    # 가공타입 설정 : 현재 GPT 연관검색어 
    opt_type = opt_type

    logger.log(f"▶️ 상품명가공시작 ▶️ 가공타입 : {opt_type} , 작업타입 : {task_type} ", level="INFO", also_to_report=True, separator="2line")
    
    first_sheet_data = sheets

    # 설정파일 값을 변경
    market_name = settings.CURRENT_MARKET_NAME
        
    if market_name == "쿠팡" or market_name == "11번가" or market_name == "고도몰":
        name_strength = 100
    elif market_name == "톡스토어":
        name_strength = 70
    else:  #쿠팡, 11번가 이외의 마켓 스마트스토어 등일경우
        name_strength = 50

    logger.log(f"상품명가공 플랫폼 : {market_name} , 글자수 : {name_strength}", also_to_report=True, separator="none")


    # ▶️ 1.  '상품명*' 앞에 새로운 열(가공결과) 삽입 (가공상품명의 결과를 추가하기 위해)
    modified_sheet = insert_excel_column(
        first_sheet_data=first_sheet_data,  # 첫 번째 시트 사용
        existing_column_name="상품명_기본",
        new_column_name="가공결과",
        position="before",
        offset=1
    )

    # 상품명 키워드사전 로드
    dictionary = load_dictionary()
    
    # 시트에서 상품명리스트 가져옴 
    naming_list = get_column_values_with_validation(modified_sheet, "상품명_기본")

    # 사전데이터와 비교한결과 튜플리스트 예: [("새로운문자열", naming_str) ,("새로운문자열", naming_str) ]
    filterd_list = filtered_naming_in_dictionary(dictionary, naming_list)
    # logger.log_list("필터링된 리스트", filterd_list, level="INFO") #필터링된 리스트

    # ▶️ gpt 비용, 시간 확인, 프로그램실행유무
    run_filtering_item_process(filterd_list, "상품명가공", task_type)
    #run_filtering_item_process(filterd_list, "상품명가공", "single")
    # run_filtering_item_process(filterd_list, "상품명가공", "auto")
    
    # 기본상품명 분석(메인과 보조키워드 추출) 및 연관검색어 추출
    logger.log(f"⏩ 기본상품명 분석(메인과 보조키워드 추출) 및 연관검색어 추출작업시작 ", level="INFO", also_to_report=True, separator="none")
    total_items, initial_existing_count, added_to_dictionary_count, extract_namingData_list = process_naming_list_with_gpt(dictionary, naming_list, missing_threshold=1)


    logger.log("▶️ GPT의 결과에 따른 가공 상품명 조합시작 ▶️", also_to_report=True, separator="2line")
    gpt_optimized_name_list = []  # 최종 결과를 담을 리스트
    basic_product_names = []  # 기본상품명 리스트

    for gptData in extract_namingData_list:

        try:
            # 현재 namingData에는 딕셔너리 값이 하나만 있으므로 메인키워드 데이터에 바로 접근
            main_keyword = list(gptData.keys())[0]  # 첫 번째 키 가져오기
            product_data = gptData[main_keyword]

            # 기본상품명 가져오기
            basic_product_name = product_data["기본상품명"]
            logger.log(f"검색타입 : {opt_type} , 처리 중인 메인 키워드: {main_keyword}, 상품명: {basic_product_name}")

            # 기본상품명 리스트에 저장
            basic_product_names.append(basic_product_name)

            # ▶️ 최적화된 상품명 생성
            optimized_name = gpt_result_generate_name(basic_product_name, dictionary, name_strength) 
            gpt_optimized_name_list.append(optimized_name)
        
        except Exception as e:  # 모든 예외 처리
            logger.log(f"⚠️ 상품명조합 중 예외 발생: {e}. namingData: {gptData}", level="ERROR")
            raise ValueError(f"⚠️ 상품명조합 중 예외 발생: {e}. namingData: {gptData}")

    '''
        - 기존시트에 가공상품명을 넣을때 지킬사항 -
        1. 기존에 편집된 시트데이터 modified_sheet는 상품명이 입력될때까지 변경이 일어나면 안된다
        2. modified_sheet에서 추출된 naming_list가  gpt_optimized_name_list로 만들어지기까지 리스트의 갯수에 변동이 있으면 안된다

        *** 위의 전제가 없다면 이후 기존상품명에 가공된 상품명이 매칭 안될 가능성이 있음
            단 modified_sheet에 가공상품명이 담긴 후에는 modified_sheet를 편집해도 문제가 없음 

    '''
    # 시트에 가공상품명 적용 전 검증로직 
    if len(modified_sheet) != len(gpt_optimized_name_list):
        raise ValueError(
            f"기존시트 데이터의 길이가 ({len(modified_sheet)}) 가공상품명 데이터 길이 ({len(gpt_optimized_name_list)} 와 매칭안됨)."
        )


    # ▶️ 시트에 가공상품명 적용 
    modified_sheet = modified_sheet.copy()
    modified_sheet["가공결과"] = gpt_optimized_name_list

    # ▶️ "판매자관리코드" 열 문자열 앞에 opt_type 추가 (만약 같은 접두사가 붙어있다면 붙이지 않음)
    modified_sheet["자체상품코드"] = modified_sheet["자체상품코드"].apply(
    lambda x: f"{opt_type}-{x}" if pd.notnull(x) and not str(x).startswith(f"{opt_type}-") else x
)


    # # ▶️ 작업 유형이 "single"인 경우 열 이름 변경 및 기존 열 삭제
    # if task_type == "auto":
    #     modified_sheet = modified_sheet.drop(columns=["상품명*"], errors="ignore")
    #     modified_sheet = modified_sheet.rename(columns={"가공결과": "상품명*"})

    #처리 완료 로그 출력
    logger.log(f"📌 상품명가공 처리결과.", level="INFO", also_to_report=True, separator="none")
    logger.log(f"💬 총 {total_items}개의 상품명 처리완료.", level="INFO", also_to_report=True, separator="none")
    logger.log(f"💬 사전에 이미 존재했던 기본상품명 수: {initial_existing_count}", level="INFO", also_to_report=True, separator="none")
    logger.log(f"💬 새로 추가된 기본상품명 수: {added_to_dictionary_count}", level="INFO", also_to_report=True, separator="none")
    logger.log_message_with_list("💡 기본상품명 :", basic_product_names, level="INFO", also_to_report=True)
    logger.log_message_with_list("🌟 가공결과 :", gpt_optimized_name_list, level="INFO", also_to_report=True)


    # 가공상품명 열이름을 상품명 열이름으로 대체
    modified_sheet = rename_and_modify_columns(
        dataframe=modified_sheet,
        target_column="가공결과",           # A 열의 이름을 변경
        new_column_name="상품명_기본",         # A -> B
        change_column_name="기존상품명*"   # B -> B_new
    )

    # ✅ **필터링된 컬럼 제거** (복사본 생성 후 제거)
    columns_to_remove = ["기존상품명*"]

    # 데이터프레임 복사
    modified_sheet = modified_sheet.copy()

    # 컬럼 제거
    for col in columns_to_remove:
        if col in modified_sheet.columns:
            modified_sheet.drop(columns=[col], inplace=True)
            logger.log(f"🗑️ '{col}' 컬럼 제거 완료.", level="INFO")
    
    
    return modified_sheet
    
