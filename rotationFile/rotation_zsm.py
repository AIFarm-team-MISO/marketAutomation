from utils.global_logger import logger


import pandas as pd
import os
from utils.excel.excel_utils import make_input_file_path, make_output_file_path
import config.settings as settings

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

# 현재 파일 위치 기준으로 JSON 파일 경로 설정
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, "rotationInfo.json")

# '폴더명' 열번호
folder_column_index = '폴더명'
content = '테스트'

'''

    - details_config 사용이유 -

    1. 기본값 제공:
    details_config는 JSON 설정이 간단하거나 불완전할 경우 기본값을 제공하기 위해 존재
    예를 들어, description이나 type이 JSON에 명시되지 않은 경우에도, details_config에서 기본값을 가져와 처리할 수 있음
    이 기능이 유용한 경우는 JSON 설정 파일이 여러 마켓/폴더에 대해 공통적으로 사용되고, 각 마켓마다 세부 설정을 누락했을 가능성이 있기 때문
    그리고 json 각값을 bool 타입으로 적어두는 경우 기본값을 셋팅할수 있다. 

    
    2. 코드 유지보수:
    details_config를 사용하면 각 작업의 메타데이터(type, description)를 코드에서 관리 가능
    JSON 파일을 변경하지 않고도 새로운 작업을 추가하거나 수정할 수 있음

'''
details_config = {
    "remove_empty_rows": {
        "description": "비어있는 {column} 행 제거",
        "type": "deletion"  # 삭제 작업
    },
    "remove_food_category_rows": {
        "description": "'{column}' 열에서 음식 카테고리 제거",
        "type": "deletion"
    },
    "remove_duplicate_rows": {
        "description": "'{column}' 열에서 중복 제거 (방법: {method})",
        "type": "deletion"
    },
    "remove_options_rows": {
        "description": "'{column}' 열에서 옵션 제거",
        "type": "deletion"
    },
    "clean_search_keywords": {
        "description": "태그 처리",
        "type": "modification"  # 수정 작업
    },
    "update_column_value": {
        "type": "modification",
        "description": "{column} 열 값을 '{value}'로 변경",
        "default_columns": [
            ("요약정보 상품군 코드*", 35),
            ("요약정보 전항목 상세설명 참조", "Y")
        ]
    }
}

def make_rotation_excel(file_path, base_file_name):
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

    # while True:
    #     logger.log_choices(choices, "기본 폴더 생성")
    #     user_input = input("Enter your choice: ").strip()

    #     if not user_input:  # Exit if the user presses Enter without typing anything
    #         print("선택이 없어 종료합니다.")
    #         break

    #     handle_selection(user_input, file_path)

    # 리포트 파일명 생성
    logger.prepend_report_file_name(base_file_name)

    try:

        # 읽을 파일경로 출력 파일 이름 설정
        excel_file_path = make_input_file_path(file_path, base_file_name)
        output_file_name = make_output_file_path(file_path, base_file_name, "_rotatet", FILE_EXTENSION_xlsx)
        _, file_extension = os.path.splitext(base_file_name)

    
        # 모든 시트 읽기(파일확장명에 따라)
        if file_extension.lower() == ".xlsx":
            sheets = read_xlsx_all_sheets(excel_file_path)  # .xlsx 파일 처리
        elif file_extension.lower() == ".xls":
            sheets = read_xls_all_sheets(excel_file_path)  # .xls 파일 처리
        else:
            raise ValueError(f"Unsupported file format: {file_extension}. Only '.xls' and '.xlsx' are supported.")

        # 첫 번째 시트를 읽고 비어 있는 행 제거
        first_sheet_name, first_sheet_data = read_and_clean_first_sheet(sheets)

        # 대상시트에서 '폴더명' 이름 가져오기
        folder_name, split_folder_name = get_folder_name(first_sheet_data, column_name="폴더명")
        logger.log(f"folder_name : {folder_name}")
        logger.log(f"split_folder_name : {split_folder_name}")


        # 순환파일 JSON 설정파일 로드 
        config = load_config(config_path)

        market_config = config.get(split_folder_name, {})
        if not market_config:  # market_config이 빈 딕셔너리 또는 None일 경우
            raise ValueError(f"JSON에 마켓 이름 '{split_folder_name}'이(가) 없습니다.")
        
        market_name, channel_name = get_market_name(split_folder_name)


        # 설정파일 값을 변경
        settings.CURRENT_MARKET_NAME = market_name
        logger.log(f"작업중인 마켓 : {market_name}")

        if market_name == "쿠팡":
            # 브랜드명을 모두지움
            processed_sheet_data = clear_column_data(first_sheet_data, "브랜드")

        elif market_name == "도매토피아":
            # [도매토피아-GT]
            # 판매자관리코드 접두사만듬 
            modify_sellercode = add_prefix_to_column(first_sheet_data, "판매자 관리코드", channel_name)
            modify_count = update_column_to_9999(modify_sellercode, "수량*") #수량변경
            modify_price = adjust_column_by_percentage(modify_count, "판매가*", 5, "인하") #판매가변경
            processed_sheet_data = swap_image_column(modify_price, '목록 이미지*', '이미지2')


        elif market_name == "네이버":
            # 네이버는 json에 네이버용 도매토피아 만들어야됨 아마.. [네이버-GT]등으로
            processed_sheet_data = add_prefix_to_column(first_sheet_data, "판매자 관리코드", channel_name)
        else:
            processed_sheet_data = first_sheet_data  # 원본 데이터 그대로 사용




        # 설정 파일에 따라 작업 생성
        tasks = generate_tasks_from_config(market_config, details_config)

        try:
            # todo :  각폴더명에 따른 내용을 json 파일에 기록하자
            #          공통된 부분은 모두 bool 타입으로 기록하고 이미지필터링 파일나눔도 json에 기록해 받아와 체크한뒤 실행하도록 변경하자 
            # 컨트롤 타워 실행
            modify_df = process_first_sheet(tasks, processed_sheet_data)

        except ValueError as e:
            logger.log(f"태스크 작업중 에러발생 : {e}", level="ERROR")
            exit(1)
        
        # market_config(json)에서 이미지 필터링 여부 확인
        image_filtering = market_config.get("image_filtering", False)
        logger.log(f"{split_folder_name} 이미지필터링유무: " + str(image_filtering), also_to_report=True, separator="1line")

        # 이미지필터링 
        if image_filtering: #이미지 필터링이 true 라면
            image_filtered_df = process_imageFiltering_excel_file_xlsx(file_path, base_file_name, task_type="auto", sheets=modify_df)
        
        else:
            image_filtered_df = modify_df
            logger.log(f"{split_folder_name}은 이미지필터링 제외.", level="INFO", also_to_report=True, separator="none")


        # save_excel_with_sheets(sheets, output_file_name, image_filtered_df, first_sheet_name)



        naming_process_df = process_namingChange_excel_file(file_path, base_file_name, 'GPT조합', task_type="auto", sheets=image_filtered_df)
            

        # modify_df의 행 개수를 확인하여 분할 저장 여부 결정
        if naming_process_df.shape[0] > 5000:
            logger.log(f"{folder_name} 의 행갯수가 5000개를 넘어 {naming_process_df.shape[0]}행 이므로 행분할 실시.", level="INFO", also_to_report=True, separator="2line")

            split_excel_by_rows(file_path, base_file_name)
        else:
            # 모든 시트 저장
            save_excel_with_sheets(sheets, output_file_name, naming_process_df, first_sheet_name)
            


    except Exception as e:
        logger.log(f"순환파일 자동화중 에러가 발생: {e}", level="ERROR")
        raise





choices = {
    "0": "단일파일 폴더 생성",
    ".": "모든마켓 폴더 생성",
    "1": "스마트스토어",
    "2": "옥션/지마켓",
    "3": "11번가/쿠팡",
    "4": "고도몰"
}

def handle_selection(selection, base_path):
    """Handle user selection to create folders."""
    if selection == "0":
        print(f"{base_path}에 모든 마켓 폴더를 생성합니다...")
        # Add logic for creating all folders
    elif selection == "1":
        print(f"{base_path}에 스마트스토어 폴더를 생성합니다...")
        # Add logic for Smart Store
    elif selection == "2":
        print(f"{base_path}에 옥션/지마켓 폴더를 생성합니다...")
        # Add logic for OK/G Market
    elif selection == "3":
        print(f"{base_path}에 11번가/쿠팡 폴더를 생성합니다...")
        # Add logic for 11th Street / Coupang
    elif selection == "4":
        print(f"{base_path}에 고도몰 폴더를 생성합니다...")
        # Add logic for Godo Mall
    else:
        print("유효하지 않은 선택입니다. 다시 시도해주세요.")


