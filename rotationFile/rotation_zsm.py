import pandas as pd
from utils.global_logger import logger

import os
from utils.excel.excel_process_utils import update_excel_column
from utils.excel.excel_utils import column_letter_to_index, make_input_file_path, make_output_file_path

from config.settings import FILE_EXTENSION_xls, FILTERED_URL_FILE, FILE_EXTENSION_xlsx, FILE_EXTENSION_JSON, CONVERT_URL_FILE
from utils.excel.excel_utils import make_input_file_path, make_output_file_path, read_xls_all_sheets, save_excel_with_sheets, read_xlsx_all_sheets, read_and_clean_first_sheet
# from imageFilter.excel.excel_handler_xlsx import process_imageFiltering_excel_file_xlsx
from utils.json.json_util import convert_excel_to_json, load_config
from utils.validate.validate_dataframe import validate_data_integrity
from imageFilter.excel.excel_handler_xlsx import process_imageFiltering_excel_file_xlsx
from utils.excel.excel_split import split_excel_by_rows
from utils.report.report_handler import initialize_report_file, add_str_log, update_process_report, add_separator_line

# 현재 파일 위치 기준으로 JSON 파일 경로 설정
current_dir = os.path.dirname(__file__)
config_path = os.path.join(current_dir, "rotationInfo.json")

# '폴더명' 열번호
folder_column_index = '폴더명'
content = '테스트'

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

def make_rotation_excel(file_path, base_file_name):

    # while True:
    #     logger.log_choices(choices, "기본 폴더 생성")
    #     user_input = input("Enter your choice: ").strip()

    #     if not user_input:  # Exit if the user presses Enter without typing anything
    #         print("선택이 없어 종료합니다.")
    #         break

    #     handle_selection(user_input, file_path)

    try:

        # 읽을 파일경로 출력 파일 이름 설정
        excel_file_path = make_input_file_path(file_path, base_file_name)
        output_file_name = make_output_file_path(file_path, base_file_name, "_rotate_output", FILE_EXTENSION_xlsx)

        # 모든 시트 읽기
        sheets = read_xls_all_sheets(excel_file_path)

        # 첫 번째 시트를 읽고 비어 있는 행 제거
        first_sheet_name, first_sheet_data = read_and_clean_first_sheet(sheets)

        logger.log_separator()
        # 대상시트에서 '폴더명' 이름 가져오기
        folder_name, split_folder_name = get_folder_name(first_sheet_data, column_name="폴더명")

        # 리포트 생성
        report_path = initialize_report_file(current_dir, base_file_name+"rotation_report", ".txt")
        logger.log(f"{base_file_name} 의 리포트 파일 생성완료")

        logger.log_separator()

        # 순환파일 JSON 설정파일 로드 
        config = load_config(config_path)

        market_config = config.get(split_folder_name, {})
        if not market_config:  # market_config이 빈 딕셔너리 또는 None일 경우
            raise ValueError(f"JSON에 마켓 이름 '{split_folder_name}'이(가) 없습니다.")

        # 설정 파일에 따라 작업 생성
        tasks = generate_tasks_from_config(market_config, details_config, report_path)

        try:
            # todo :  각폴더명에 따른 내용을 json 파일에 기록하자
            #          공통된 부분은 모두 bool 타입으로 기록하고 이미지필터링 파일나눔도 json에 기록해 받아와 체크한뒤 실행하도록 변경하자 
            # 컨트롤 타워 실행
            modify_df = process_first_sheet(tasks, first_sheet_data, report_path)

        except ValueError as e:
            logger.log(f"태스크 작업중 에러발생 : {e}", level="ERROR")
            exit(1)
        
        # market_config(json)에서 이미지 필터링 여부 확인
        image_filtering = market_config.get("image_filtering", False)
        add_str_log(report_path, "이미지필터링유무 : " + str(image_filtering))

        # 이미지필터링 
        if image_filtering: #이미지 필터링이 true 라면
            image_filtered_df = process_imageFiltering_excel_file_xlsx(file_path, base_file_name, report_path, task_type="auto", sheets=modify_df)
        
        else:
            logger.log(f"{folder_name}은 이미지필터링 제외.", level="INFO")
            add_str_log(report_path, f"{folder_name}은 이미지필터링 제외")
            

        # modify_df의 행 개수를 확인하여 분할 저장 여부 결정
        if modify_df.shape[0] > 5000:
            logger.log(f"{folder_name} 의 행갯수가 5000개를 넘어 {modify_df.shape[0]}행 이므로 행분할 실시.", level="INFO")
            add_str_log(report_path, f"{folder_name} 의 행갯수가 5000개를 넘어 {modify_df.shape[0]}행 이므로 행분할 실시.")


            split_excel_by_rows(report_path, file_path, base_file_name)
        else:
            # 모든 시트 저장
            save_excel_with_sheets(sheets, output_file_name, image_filtered_df, first_sheet_name)
            add_str_log(report_path, "엑셀저장완료")


    except Exception as e:
        logger.log(f"순환파일 자동화중 에러가 발생: {e}", level="ERROR")
        raise


def generate_tasks_from_config(market_config, details_config, report_path):
    """
    JSON 설정에서 작업 목록을 생성합니다.

    Parameters:
        market_config (dict): 각마켓에 대한 JSON 설정 (작업별로 상세 설정 포함).
        details_config (dict): json값이 bool 값일 경우의 디폴트매개변수값 및 태스크타입정보

    Returns:
        list: 생성된 작업 목록.
    """
    tasks = []

    # 함수 참조 매핑 (JSON 키를 함수에 매핑)
    function_mapping = {
        "remove_empty_rows": remove_empty_rows,
        "remove_food_category_rows": remove_food_category_rows,
        "remove_duplicate_rows": remove_duplicate_rows,
        "remove_options_rows": remove_options_rows,
        "clean_search_keywords": clean_search_keywords,
        "update_column_value": update_column_value
    }

    def add_task(task_func, task_type, task_description, *args):
        """
        태스크를 리스트에 추가하고 로그로 기록.

        Parameters:
            task_func (function): 실행할 함수 참조.
            task_type (str): 작업 유형 ('deletion', 'modification', etc.).
            task_description (str): 작업 설명.
            *args: 함수에 전달할 추가 인수.
        """

        # 매개변수 출력
        #params = inspect.signature(task_func).parameters
        #logger.log(f"   - 매개변수: {[param for param in params]}", level="DEBUG")
        
        tasks.append((task_func, task_type, task_description, args))
        logger.log(f"✅작업추가: {task_description}")
        logger.log(f"   -함수: {task_func.__name__}, -작업유형: {task_type}, -전달된 값: {args} ", level="DEBUG")

        add_str_log(report_path, "작업추가: " + task_description)
        
    def add_task_from_config(key, default_column):
        """
        JSON 설정의 특정 키를 처리하여 태스크를 추가.

        Parameters:
            key (str): 설정의 키(함수명).
            default_column (str, optional): 기본 열 이름.
            default_method (str, optional): 기본 메서드 값 (예: 'remove_all').
        """
        if key in market_config:
            value = market_config[key]

            # 함수 기본 타입값을 지정 
            task_type = details_config[key].get("type")

            # json파일에 Boolean 설정되어 있는경우 
            if isinstance(value, bool):
                if value:
                    column = default_column if default_column else key
                    description = details_config[key]["description"].replace("{column}", column)
                    add_task(function_mapping[key], task_type, description, column)
                else:
                    logger.log(f"⏩ 태스크 건너뜀: json 파일의 {key} 설정이 False로 지정됨", level="INFO")

            # 설정값이 존재하는 경우
            elif isinstance(value, list):
                for entry in value:
                    if isinstance(entry, str):
                        
                        #리스트 안의 str 처리 
                        column = entry # 각 함수에 넘겨질 첫번째 매개변수
                        description = details_config[key]["description"].replace("{column}", column) #각 함수의 기본문자와 json내용을 조합
                        add_task(function_mapping[key], task_type, description, column)

                    ### 현재 json 값이 리스트이며 리스트의 값들이 dict 형식일때 ###
                    elif isinstance(entry, dict):
                        
                        # 리스트 안의 딕셔너리 처리
                        column = entry.get("column", default_column)
                        description = entry.get("description", details_config[key]["description"].replace("{column}", column))
                        add_task(function_mapping[key], task_type, description, column)

            elif isinstance(entry, dict):  # 리스트의 항목이 딕셔너리일 때
                
                column = entry.get("column", default_column)  # 'column' 값을 가져옴, 없으면 기본값 사용
                description = entry.get("description", details_config[key]["description"].replace("{column}", column))  # 'description'을 가져옴, 없으면 기본값 사용
                add_task(function_mapping[key], task_type, description, column)

            else:
                logger.log(f"⚠️ 태스크 스킵됨: {key}의 설정 형식이 유효하지 않음", level="WARNING")

    # JSON 설정 키별 태스크 추가
    logger.log("🛠️ JSON 설정 기반 태스크 추가 시작", level="INFO")
    # logger.log(f"현재 JSON 설정: {market_config}", level="DEBUG")

    # 태스크 정의
    add_task_from_config("remove_empty_rows", default_column="카테고리 번호*")
    add_task_from_config("remove_food_category_rows", default_column="카테고리 번호*")
    add_task_from_config("remove_duplicate_rows", default_column="상품명*")
    add_task_from_config("remove_options_rows", default_column="선택사항 타입")
    add_task_from_config("clean_search_keywords", default_column="검색어(태그)")

    # update_column_value 처리: 두 개의 매개변수를 동적으로 전달해야 하므로 따로 처리
    if "update_column_value" in market_config:
        value = market_config["update_column_value"]

        # Boolean 설정 처리
        if isinstance(value, bool):
            if value:
                # 기본 열 이름 및 값 설정
                default_columns = details_config["update_column_value"].get("default_columns", [])
                for column, new_value in default_columns:
                    description = details_config["update_column_value"]["description"].replace("{column}", column).replace("{value}", str(new_value))
                    add_task(function_mapping["update_column_value"], "modification", description, column, new_value)
            else:
                logger.log(f"⏩ 태스크 건너뜀: update_column_value 설정이 False로 지정됨", level="INFO")

        # 딕셔너리 처리
        elif isinstance(value, dict):
            for column, new_value in value.items():
                description = details_config["update_column_value"]["description"].replace("{column}", column).replace("{value}", str(new_value))
                add_task(function_mapping["update_column_value"], "modification", description, column, new_value)

        else:
            logger.log(f"⚠️ 태스크 스킵됨: update_column_value의 설정 형식이 유효하지 않음", level="WARNING")


    logger.log("✅ 모든 태스크가 성공적으로 추가되었습니다.", level="INFO")
    # logger.log(f"생성된 태스크: {[task[2] for task in tasks]}", level="DEBUG")

    return tasks

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

def debug_single_task(task, sheet_data, task_type, task_name="unnamed_task"):
    """
    특정 작업을 독립적으로 실행하며 디버깅
    :param task: 실행할 작업 함수
    :param sheet_data: 작업 대상 데이터프레임
    :param task_name: 작업 이름 (기본값: unnamed_task)
    :param operation_type: 작업 유형 ('deletion', 'addition', 'modification')
    :return: 작업이 완료된 데이터프레임

        # 태스트에 담긴 함수 디버그 : 단일함수 테스트 
        # modify_df = debug_single_task(
        #     lambda df: remove_empty_rows(df, "카테고리 번호*"), # 반환값을 그대로 전달
        #     first_sheet_data, "deletion", "비어있는 카테고리 행제거"
        # )

    """

    try:
        logger.log_separator()
        logger.log(f"{task_name} 작업 시작.", level="INFO")
        sheet_data_before = sheet_data.copy()

        # 작업 실행
        result = task(sheet_data)
        result_sheet_data, processed_count = result

        '''
            - 무결성 검증 - 
            최초 갯수에서 처리된 갯수를 뺀 결과가 작업이후의 갯수와 같은지를 판별 
        
        '''
        # 무결성 검증 호출
        validate_data_integrity(
            initial_count=len(sheet_data_before), #최초갯수
            filtered_sort_complete_sheets=result_sheet_data,  #결과데이터프레임
            processed_count=processed_count,      #처리된갯수
            task_name=task_name,                  #처리명
            task_type=task_type                   #처리타입
        )

        # 중간 상태 저장
        sheet_data_before.to_excel(f"debug_before_{task_name}.xlsx", index=False)
        sheet_data.to_excel(f"debug_after_{task_name}.xlsx", index=False)

        logger.log(
            f"{task_name} 작업 완료."
            f"최초 데이터 수 : {len(sheet_data_before)}, 처리된 데이터 수: {processed_count}, 남은 데이터 수: {len(result_sheet_data)}",
            level="INFO"
        )


        return result_sheet_data

    except Exception as e:
        logger.log(f"디버깅: {task_name} 작업 중 에러 발생: {e}", level="ERROR")
        raise ValueError(f"{task_name} 작업에서 문제가 발생했습니다: {e}")


def get_folder_name(sheet_data, column_name="폴더명"):
    """
    시트 데이터에서 지정된 열(column_name)의 첫 번째 값에서 '_'로 구분된 첫 번째 부분을 추출합니다.
    폴더명이 없는 경우 속행합니다.

    Parameters:
        sheet_data (pd.DataFrame): 작업 대상 데이터프레임.
        column_name (str): 폴더명이 포함된 열 이름 (기본값: '폴더명').

    Returns:
        str: '_'로 구분된 첫 번째 부분의 값 (없을 경우 빈 문자열 반환).
    """
    try:
        # 지정된 열(column_name)이 존재하는지 확인
        if column_name not in sheet_data.columns:
            logger.log(f"⚠️ 열 '{column_name}'이(가) 데이터프레임에 존재하지 않습니다. 속행합니다.", level="WARNING")
            return ""

        # 첫 번째 값 가져오기
        folder_name = sheet_data[column_name].iloc[0] if not sheet_data.empty else ""

        # 값이 NaN인 경우 처리
        if pd.isna(folder_name):
            logger.log(f"⚠️ 폴더명이 비어 있습니다. 속행합니다.", level="WARNING")
            return ""

        # '_'로 나누어 첫 번째 부분 추출
        split_parts = folder_name.split("_")
        if split_parts:
            extracted_folder_name = split_parts[0].strip()  # 첫 번째 부분 추출 후 공백 제거
            # logger.log(f"추출된 폴더명: {extracted_folder_name}", level="INFO")
            
            return folder_name, extracted_folder_name
        else:
            logger.log(f"⚠️ 폴더명 '{folder_name}'에서 '_'로 구분된 부분을 찾을 수 없습니다. 속행합니다.", level="WARNING")
            return ""

    except Exception as e:
        logger.log(f"폴더명을 가져오는 중 에러 발생: {e}", level="ERROR")
        return ""
    
def split_market_name(folder_name):
    """
    폴더명을 '-'로 나누어 각각 리스트에 담아 반환하며, 대괄호([ ])와 같은 특수문자를 제거합니다.

    Parameters:
        folder_name (str): 분리할 폴더명 문자열.

    Returns:
        list: '-'로 나누어진 모든 부분을 담은 리스트 (없으면 빈 리스트 반환).
    """
    try:
        if not folder_name:
            logger.log(f"⚠️ 폴더명이 비어 있습니다.", level="WARNING")
            return []

        # 특수문자 제거 및 '-'로 나누기
        cleaned_folder_name = folder_name.replace("[", "").replace("]", "").strip()
        parts = [part.strip() for part in cleaned_folder_name.split("-") if part.strip()]
        if parts:
            logger.log(f"폴더명 분리: '{folder_name}' -> Parts: {parts}", level="INFO")
            return parts
        else:
            logger.log(f"⚠️ 폴더명을 '-'로 나눌 수 없습니다: '{folder_name}'", level="WARNING")
            return []

    except Exception as e:
        logger.log(f"폴더명을 분리하는 중 에러 발생: {e}", level="ERROR")
        return []





def remove_empty_rows(dataframe, column_name):
    """
    특정 열이 비어있는 행을 삭제하는 함수
    :param dataframe: 데이터프레임
    :param column_name: 기준 열 이름
    :return: 수정된 데이터프레임, 삭제된 행 수
    """
    try:
        initial_count = len(dataframe)  # 초기 행 수
        dataframe = dataframe[dataframe[column_name].notna()]  # 비어있지 않은 행 필터링
        removed_count = initial_count - len(dataframe)  # 삭제된 행 수 계산
        logger.log(f"{column_name} 열에서 {removed_count}개의 행 삭제", level="INFO")

        return dataframe, removed_count
    except Exception as e:
        raise ValueError(f"{column_name} 열에서 비어있는 행을 삭제하는 중 문제가 발생했습니다: {e}")

from config.settings import FOOD_CATEGORIES_NUMBERS
def remove_food_category_rows(dataframe, column_name):
    """
    카테고리 번호가 음식 카테고리인 행을 삭제하는 함수
    :param dataframe: 데이터프레임
    :param column_name: 기준 열 이름
    :return: 수정된 데이터프레임, 삭제된 행 수
    """
    try:
        initial_count = len(dataframe)  # 초기 행 수
        dataframe = dataframe[~dataframe[column_name].isin(FOOD_CATEGORIES_NUMBERS)]  # 음식 카테고리를 제외
        removed_count = initial_count - len(dataframe)  # 삭제된 행 수 계산
        logger.log(f"{column_name} 열에서 음식 카테고리 {removed_count}개의 행이 삭제되었습니다.", level="INFO")

        return dataframe, removed_count
    except Exception as e:
        raise ValueError(f"{column_name} 열에서 음식 카테고리 행을 삭제하는 중 문제가 발생했습니다: {e}")

def remove_duplicate_rows(dataframe, column_name, keep_type="remove_all"):
    """
    특정 열에서 중복된 항목을 삭제하는 함수
    :param dataframe: 데이터프레임
    :param column_name: 기준 열 이름
    :param keep_type: 중복 처리 유형 ('keep_one' - 중복중 하나 남김, 'remove_all' - 모두 삭제)
    :return: 수정된 데이터프레임, 삭제된 행 수
    """
    try:
        initial_count = len(dataframe)  # 초기 행 수

        if keep_type == "keep_one":
            # 하나를 남기고 중복 제거
            dataframe = dataframe.drop_duplicates(subset=[column_name])
        elif keep_type == "remove_all":
            # 중복된 항목 모두 삭제
            duplicate_mask = dataframe[column_name].duplicated(keep=False)
            dataframe = dataframe[~duplicate_mask]
        else:
            raise ValueError(f"Invalid keep_type: {keep_type}. Use 'keep_one' or 'remove_all'.")

        removed_count = initial_count - len(dataframe)  # 삭제된 행 수 계산
        logger.log(f"<{column_name}> 열에서 중복된 {removed_count}개의 행이 삭제되었습니다. (처리 방식: {keep_type})", level="INFO")

        return dataframe, removed_count

    except Exception as e:
        raise ValueError(f"{column_name} 열에서 중복된 행을 삭제하는 중 문제가 발생했습니다: {e}")

def remove_options_rows(dataframe, column_name):
    """
    '선택사항 타입' 열에서 옵션이 있는행은 제거 
    :param dataframe: 데이터프레임
    :param column_name: 기준 열 이름
    :return: 수정된 데이터프레임, 삭제된 행 수
    """
    try:
        initial_count = len(dataframe)  # 초기 행 수
        dataframe = dataframe[dataframe[column_name].isna()]  # 비어있는 행 필터링
        removed_count = initial_count - len(dataframe)  # 삭제된 행 수 계산
        logger.log(f"{column_name} 열에서 옵션이 있는 {removed_count}개의 행이 삭제되었습니다.", level="DEBUG")

        return dataframe, removed_count
    except Exception as e:
        raise ValueError(f"{column_name} 열에서 비어있지 않은 행을 삭제하는 중 문제가 발생했습니다: {e}")

def clean_search_keywords(dataframe, column_name):
    """
    검색어 열에서 중복 키워드 제거, 숫자/특수문자 제거, 문자열 길이 조정을 수행하는 함수
    :param dataframe: 데이터프레임
    :param column_name: 기준 열 이름
    :return: 수정된 데이터프레임, 변경된 데이터 수
    """
    try:
        import re

        def clean_keywords(keywords):
            # 중복 제거, 숫자 및 특수문자 제거
            if pd.isna(keywords):
                return ""
            unique_keywords = list(dict.fromkeys(re.sub(r'[^가-힣a-zA-Z,]', '', keywords).split(',')))
            # 문자열 길이 조정
            return ','.join(unique_keywords)[:29]

        # 초기 상태 복사
        original_keywords = dataframe[column_name].copy()

        # 데이터 정리 작업 수행
        dataframe[column_name] = dataframe[column_name].apply(clean_keywords)

        # 변경된 데이터 수 계산
        changed_count = int((original_keywords != dataframe[column_name]).sum())

        logger.log(f"{column_name}열의 검색어가 정리되었습니다. 변경된 데이터 수: {changed_count}", level="DEBUG")
        return dataframe, changed_count
    except Exception as e:
        raise ValueError(f"{column_name} 열의 검색어를 정리하는 중 문제가 발생했습니다: {e}")

def update_column_value(dataframe, column_name, value):
    """
    특정 열의 값을 일괄 변경하는 함수
    :param dataframe: 데이터프레임
    :param column_name: 기준 열 이름
    :param value: 변경할 값
    :return: 수정된 데이터프레임, 변경된 데이터 수
    """
    try:
        # 초기 상태 복사
        original_column = dataframe[column_name].copy()

        # 데이터 타입 강제 변환
        dataframe[column_name] = dataframe[column_name].astype(type(value))

        # 열 값을 일괄 변경
        dataframe[column_name] = value

        # 변경된 데이터 수 계산 (타입 차이 허용)
        changed_count = int((original_column != dataframe[column_name]).sum())

        # 디버깅 로그 추가
        # logger.log(f"변경 전 데이터 타입: {original_column.dtype}", level="DEBUG")
        # logger.log(f"변경 후 데이터 타입: {dataframe[column_name].dtype}", level="DEBUG")
        # logger.log(f"변경 전 데이터: {original_column.unique()}", level="DEBUG")
        # logger.log(f"변경 후 데이터: {dataframe[column_name].unique()}", level="DEBUG")

        if changed_count > 0:
            logger.log(f"{column_name} 열의 값이 모두 '{value}'로 변경되었습니다. 변경된 데이터 수: {changed_count}", level="INFO")
        else:
            logger.log(f"{column_name} 열의 값은 이미 '{value}'로 설정되어 있습니다. 변경된 데이터가 없습니다.", level="INFO")

        return dataframe, changed_count
    except Exception as e:
        raise ValueError(f"{column_name} 열의 값을 변경하는 중 문제가 발생했습니다: {e}")


    

def process_first_sheet(tasks, sheet_data, report_path):
    """
    첫 번째 시트의 여러 작업을 순차적으로 실행하며 디버깅
    :tasks: 실행할 작업 리스트 (각 작업은 callable 함수)
    :sheet_data: 작업 대상 데이터프레임
    :task_type: 작업 유형 ('deletion', 'addition', 'modification')
    :task_name_prefix: 작업 이름 접두어 (기본값: 'Task')
    :report_path (str) : 리포트파일의 경로및 파일명 (예 : f:\marketAutomation\rotationFile\미니멀.xls.txt)

    :return: 모든 작업이 완료된 데이터프레임
    """

    try:
        logger.log_separator()
        logger.log(f"첫 번째 시트 작업 시작 ({len(tasks)}개 작업 실행).", level="INFO")
        logger.log_separator()
        add_str_log(report_path, "엑셀시트 편집 총작업갯수: " + str(len(tasks)) + "개")
        add_separator_line(report_path)

        # 최초 입력 데이터프레임 복사
        result_sheet_data = sheet_data.copy()
        # 작업갯수 파악
        total_processed_count = 0


        for i, (task_func, task_type, task_description, args) in enumerate(tasks):

            logger.log(f"{i + 1}번 작업 시작: {task_description}", level="INFO")
                    

            # 작업 실행 전 데이터 복사 (디버깅 및 무결성 검증용)
            sheet_data_before = result_sheet_data.copy()
            
            
            # 작업 실행
            result_sheet_data, processed_count = task_func(result_sheet_data, *args)

            # logger.log(f'result_sheet_data : {result_sheet_data}')
            # logger.log(f'processed_count : {processed_count}')
            
            # 인덱스 초기화 (행 추가/삭제 작업 이후 반드시 필요)
            result_sheet_data.reset_index(drop=True, inplace=True)

            '''
                - 무결성 검증 - 
                최초 갯수에서 처리된 갯수를 뺀 결과가 작업이후의 갯수와 같은지를 판별 
            
            '''
            # 무결성 검증 호출
            validate_data_integrity(
                initial_count=len(sheet_data_before), #최초갯수
                filtered_sort_complete_sheets=result_sheet_data,  #결과데이터
                processed_count=processed_count,      #처리된갯수
                task_name=task_description,                  #처리명
                task_type=task_type                   #처리타입
            )

            # 처리된 총 갯수 누적
            total_processed_count += processed_count

            update_process_report(report_path, task_type, task_description, len(sheet_data_before), processed_count)

            # 중간 상태 저장
            # sheet_data_before.to_excel(f"debug_before_{task_name}.xlsx", index=False)
            # sheet_data.to_excel(f"debug_after_{task_name}.xlsx", index=False)

            logger.log("------------------------------------------")

        # 최종 리포트 작성
        update_process_report(
            report_path,
            "작업결과 합산",
            "엑셀시트 편집 작업결과",
            len(result_sheet_data) + total_processed_count,  # 최초 데이터 갯수
            total_processed_count,
            success=True
        )

        logger.log(f"result_sheet_data: {result_sheet_data.index}", level="DEBUG")
        logger.log("모든 작업이 성공적으로 완료되었습니다.", level="INFO")
        return result_sheet_data

    except Exception as e:
        logger.log(f"디버깅: {task_description} 작업 중 에러 발생: {e}", level="ERROR")
        raise ValueError(f"{task_description} 작업에서 문제가 발생했습니다: {e}")


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


