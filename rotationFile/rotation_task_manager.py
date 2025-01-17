from utils.global_logger import logger

from utils.validate.validate_dataframe import validate_data_integrity
from rotationFile.rotation_excel_edit_util import remove_empty_rows,remove_food_category_rows, remove_duplicate_rows
from rotationFile.rotation_excel_edit_util import remove_options_rows, clean_search_keywords, update_column_value

def process_first_sheet(tasks, sheet_data):
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
        logger.log(f"첫 번째 시트 작업 시작 ({len(tasks)}개 작업 실행).", level="INFO", also_to_report=True, separator="1line")
        
        # 최초 입력 데이터프레임 복사
        result_sheet_data = sheet_data.copy()
    

        for i, (task_func, task_type, task_description, args) in enumerate(tasks):

            logger.log(f"{i + 1}번 작업 시작: {task_description}", level="INFO", also_to_report=True, separator="dash-1line")
                    

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



            # 중간 상태 저장
            # sheet_data_before.to_excel(f"debug_before_{task_name}.xlsx", index=False)
            # sheet_data.to_excel(f"debug_after_{task_name}.xlsx", index=False)


        logger.log(f"result_sheet_data: {result_sheet_data.index}", level="DEBUG")
        logger.log("자동환 순환파일 작성 작업이 모두 성공적으로 완료되었습니다.", level="INFO", also_to_report=True, separator="dash-1line")
        return result_sheet_data

    except Exception as e:
        logger.log(f"디버깅: {task_description} 작업 중 에러 발생: {e}", level="ERROR")
        raise ValueError(f"{task_description} 작업에서 문제가 발생했습니다: {e}")


def generate_tasks_from_config(market_config, details_config):
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
        logger.log(f"✅작업추가: {task_description}", also_to_report=True, separator="dash-1line")
        logger.log(f"   -함수: {task_func.__name__}, -작업유형: {task_type}, -전달된 값: {args} ", level="DEBUG",also_to_report=False, separator="1line")

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
                    logger.log(f"⏩ 태스크 건너뜀: json 파일의 {key} 설정이 False로 지정됨", level="INFO", also_to_report=True, separator="dash-1line")

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
                logger.log(f"⏩ 태스크 건너뜀: update_column_value 설정이 False로 지정됨", level="INFO", also_to_report=True, separator="dash-1line")

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