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

    else: # 편집된 시트데이터가 넘어온 경우, 첫 번째 시트 및 정제처리가 필요없음 : 자동화실행
        first_sheet_data = sheets

    if task_type=="single":
        # 대상시트에서 '폴더명' 이름 가져오기
        folder_name, split_folder_name = get_folder_name(first_sheet_data, column_name="폴더명")

        # 순환파일 JSON 설정파일 로드 
        config = load_config(ROTATION_JSON_PATH)

        market_config = config.get(split_folder_name, {})
        if not market_config:  # market_config이 빈 딕셔너리 또는 None일 경우
            raise ValueError(f"JSON에 마켓 이름 '{split_folder_name}'이(가) 없습니다.")
        
        market_name, channel_name = get_market_name(split_folder_name)
        # 설정파일 값을 변경
    else:
        
        market_name = settings.CURRENT_MARKET_NAME

    if market_name == "쿠팡" or market_name == "11번가":
        name_strength = 99
    else:  #쿠팡, 11번가 이외의 마켓 일경우
        name_strength = 49

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
    #run_filtering_item_process(filterd_list, "상품명가공", task_type)
    run_filtering_item_process(filterd_list, "상품명가공", "single")
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


    # ▶️ 시트에 가공상품명 적용 
    if len(modified_sheet) != len(gpt_optimized_name_list):
        raise ValueError(
            f"Sheet row count ({len(modified_sheet)}) does not match optimized_name_list length ({len(gpt_optimized_name_list)})."
        )

    modified_sheet = modified_sheet.copy()
    modified_sheet["가공결과"] = gpt_optimized_name_list

    # ▶️ "판매자관리코드" 열 문자열 앞에 opt_type 추가
    modified_sheet["판매자 관리코드"] = modified_sheet["판매자 관리코드"].apply(lambda x: f"{opt_type+"-"}{x}" if pd.notnull(x) else x)

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

    #가공타입을 판매자관리코드에 접두사로 추가 
    modified_sheet = update_seller_codes(modified_sheet, "판매자 관리코드", opt_type)

    #기존 상품명열을 삭제하고 가공상품명으로 대체 
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




# # 초기 사전 상태 저장
    # initial_dictionary_snapshot = {
    #     key: set(data.get("기본상품명", []))
    #     for key, data in dictionary.items()
    # }

    # initial_existing_count = 0  # 사전에 이미 등록된 기본상품명 수
    # added_to_dictionary_count = 0  # 사전에 새로 추가된 기본상품명 수

    # # 처리되지 못한 기본상품명을 저장할 리스트
    # missing_after_processing = []  #이 리스트에 저장되지 않은 상품명을 추적
    # # 임계치 설정
    # MISSING_THRESHOLD = 5  # 사전에 기록되지 않은 상품명이 이 값을 초과하면 종료

    # total_items = len(naming_list)
    # for index, original_name in enumerate(naming_list, start=1):
    #     logger.log(f"▶️ [{index}/{total_items}] '{original_name}' 처리 시작", level="INFO")

    #     # 진행률 표시
    #     # print_progress_bar(index, total_items)
        
    #     # ▶️기본상품명을 통해 GPT데이터 생성 : 기존데이터 재사용 혹은 GPT호출에 의한 새로운데이터
    #     gptData = extract_keywords(original_name, dictionary)

    #     if gptData is not None:
    #         # 디버깅: 각 gpt_data 출력
    #         logger.log_dict(f" - {original_name}- 에 대한 gpt_data", gptData)
    #         logger.log_separator()
    #         extract_namingData_list.append(gptData)


    #         # 상품명이 사전 및 GPT필터링 이후 제대로 사전에 기록 되었는지 확인 하고 카운트
    #         # 사전에서 기본상품명 존재여부 확인 extract_keywords 실행전
    #         is_existing = any(
    #             original_name in initial_dictionary_snapshot.get(key, set())
    #             for key in initial_dictionary_snapshot
    #         )

    #         # 이미 사전에 등록된 기본상품명이라면
    #         if is_existing:
    #             initial_existing_count += 1  

    #         # 사전에 새로 추가된 기본상품명 이라면
    #         else:
    #             is_added = any(
    #                 original_name in set(data.get("기본상품명", []))
    #                 for key, data in dictionary.items()
    #             )

    #             if is_added:
    #                 added_to_dictionary_count += 1  # 사전에 새로 추가된 기본상품명
    #             else: # extract_keywords처리 후에도 사전에 기록되지 않은 상품명 추적
    
    #                 missing_after_processing.append(original_name)

    #                 # 임계치 초과 확인 : 사전에 추가되지 않은 상품명의 갯수를 확인 
    #                 if len(missing_after_processing) >= MISSING_THRESHOLD:
    #                     logger.log(
    #                         f"❌ 임계치 초과: 사전에 기록되지 않은 상품명 수가 {MISSING_THRESHOLD}개를 초과했습니다. 프로그램을 종료합니다.",
    #                         level="CRITICAL"
    #                     )
    #                     logger.log(f"❌ 기록되지 않은 상품명: {missing_after_processing}", level="ERROR")
    #                     raise SystemExit("프로그램이 종료되었습니다. 문제를 확인하세요.")

    #     else:
    #         logger.log(f"⚠️ {original_name}에 대한 namingData가 없습니다.", level="WARNING")


    # # 기존 상품명 리스트와 만들어진 GPT데이터의 길이를 비요: 최초갯수와 같지않으면 실행종료 
    # if len(naming_list) != len(extract_namingData_list):
    #     error_message = (
    #         f"❌ 데이터 불일치: 기본상품명 리스트의 길이 ({len(naming_list)}) "
    #         f"와 extract_namingData_list의 길이 ({len(extract_namingData_list)})가 다릅니다."
    #     )
    #     logger.log(error_message, level="ERROR")
    #     raise ValueError(error_message)  # 프로그램 종료     
    

    # # 최종 결과 프로그레스바 출력
    # # print_progress_bar(total_items, total_items)
    # # sys.stdout.write("\n")  # 로그 메시지가 진행률 바를 덮지 않도록 처리

    # # 최종 통계 출력
    # logger.log(f"✅ 모든 데이터 처리 완료! 기존데이터 / 처리된 데이터 수: {len(extract_namingData_list)} / {len(naming_list)}", level="INFO")
    # logger.log(f"✅ 사전에 이미 존재했던 기본상품명 수: {initial_existing_count}", level="INFO")
    # logger.log(f"✅ 사전에 새로 추가된 기본상품명 수: {added_to_dictionary_count}", level="INFO")
    # # logger.log(f"✅ 최종 사전 내 총 기본상품명 수: {sum(len(data.get('기본상품명', [])) for data in dictionary.values())}", level="INFO")

    # #만약 사전에 기록되지 않은경우 ->  처리되지 못한 기본상품명 출력
    # if missing_after_processing:
    #     logger.log(
    #         f"❌ 처리 후에도 사전에 기록되지 않은 상품명 수: {len(missing_after_processing)}",
    #         level="ERROR"
    #     )
    #     logger.log(f"❌ 기록되지 않은 상품명 리스트: {missing_after_processing}", level="ERROR")

        # logger.log_list('메인키워드를 통한 네이버검색 시작', extract_namingData_list)
    # print('\n')
    # logger.log_separator()
    # logger.log('메인키워드를 통한 네이버검색 시작')
    # logger.log_separator()
    
    #  # 각 상품명에 대해 네이버 API 호출하여 최적화된 이름 생성
    # final_optimized_name_list = []  # 최종 결과를 담을 리스트
    # basic_product_names = []  # 기본상품명 리스트

    # for namingData in extract_namingData_list:

    #     # 현재 namingData에는 딕셔너리 값이 하나만 있으므로 메인키워드 데이터에 바로 접근
    #     main_keyword = list(namingData.keys())[0]  # 첫 번째 키 가져오기
    #     product_data = namingData[main_keyword]

    #     # 기본상품명 가져오기
    #     basic_product_name = product_data["기본상품명"]
    #     logger.log(f"검색타입 : {opt_tpye} , 처리 중인 메인 키워드: {main_keyword}, 상품명: {basic_product_name}")

    #      # 기본상품명 리스트에 저장
    #     basic_product_names.append(basic_product_name)

    #     optimized_name = generate_optimized_names(basic_product_name, opt_tpye, dictionary)  # 네이버 API 호출 및 이름 최적화
    #     final_optimized_name_list.append(optimized_name)

    