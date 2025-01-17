from utils.global_logger import logger

from config.settings import EXCEL_IMAGE_FILTER_PATH, CATEGORY_CHECK_EXCEL_PATH, NAMING_EXCEL_PATH, CODE_EXCEL_PATH, EXCEL_FILTER_PATH, EXCEL_SPLIT_PATH
# from imageFilter.excel.excel_handler import process_imageFiltering_excel_file #이전 이미지 필터링함수
from imageFilter.excel.excel_handler_xlsx import process_imageFiltering_excel_file_xlsx
from rotationAuto.login.zsm_login import login_and_navigate, close_driver
from rotationAuto.workflow.page_workflow import navigate_to_download_page
from rotationAuto.workflow.page_workflow import select_radio_button
from rotationAuto.workflow.page_workflow import click_download_button
from productNaming.name_handler import process_namingChange_excel_file
from utils.prefix_to_excel import process_add_prefix_to_excel_in_folder_with_sheets
from utils.check_food_category import process_folder_for_category_check
from utils.excel.excel_get_name import process_all_excel_files
from rotationFile.rotation_zsm import make_rotation_excel
from utils.excel.excel_split import split_excel_by_rows



def zsm_login():
    # 로그인 및 드라이버 설정
    driver = login_and_navigate()

    # 메인 페이지에서 "상품DB 다운로드" 버튼을 클릭하여 다음 페이지로 이동
    print(f'상품DB 다운로드 페이지 이동시작')
    navigate_to_download_page(driver)

    # 해당 타이틀에 맞는 라디오 버튼을 클릭
    print(f'라디오 버튼을 클릭 이동시작')
    select_radio_button(driver, '!!상품원본!!글로벌')

    # 상품 DB 다운로드 버튼 클릭
    print(f'다운로드 버튼을 클릭 이동시작')
    click_download_button(driver)
    # 드라이버 종료
    close_driver(driver)

def execute_process(process_type, process_mapping):
    """
    처리 유형과 매핑 정보를 기반으로 파일 경로를 가져오고, 해당 유형의 함수를 실행합니다.

    Parameters:
    - process_type (str): 처리 유형 ("이미지 필터링", "상품명 가공" 등).
    - process_mapping (dict): 처리 유형과 경로, 함수 매핑 정보.
    """
    # 처리 유형이 매핑에 없는 경우 오류 출력
    if process_type not in process_mapping:
        logger.log(f"알 수 없는 처리 유형: {process_type}")
        return
    

    # 선택된 처리 유형에 따른 경로와 함수 가져오기
    selected_path = process_mapping[process_type]["path"]  # 파일 경로
    selected_function = process_mapping[process_type]["function"]  # 실행할 함수
    args = process_mapping[process_type]["args"]  # 위치 인자
    kwargs = process_mapping[process_type]["kwargs"]  # 키워드 인자

    # 디버깅용 출력: 선택된 경로와 함수 확인
    # logger.log(f"선택된 처리 유형: {process_type}")
    # logger.log(f"파일 경로: {selected_path}")

    logger.log(f"🖼️  처리 유형: {process_type} 🖼️  경로내 파일처리 시작! ", also_to_report=True, separator='1line')


    # 파일 리스트 가져오기
    try:
        

        file_list = process_all_excel_files(selected_path)  # 지정된 경로에서 파일 리스트 가져오기

        logger.log(f'파일리스트 : {file_list}', also_to_report=True)

    except Exception as e:
        logger.log(f"파일 리스트를 가져오는 중 오류 발생: {e}", also_to_report=True, separator='2line')
        return

    # 각 파일 처리
    for file_path, base_file_name in file_list:
        try:
            # print(f"파일 처리 중: {base_file_name}")  # 현재 처리 중인 파일 출력
            selected_function(file_path, base_file_name, *args, **kwargs)  # 함수 실행 (동적으로 인자 전달)
        except Exception as e:
            logger.log(f"{file_path} 처리 중 오류 발생: {e}", also_to_report=True)  # 개별 파일 처리 오류 출력



if __name__ == "__main__":
    # zsm_login()
    

    process_mapping = {
        "음식 카테고리 체크": {
            "path": CATEGORY_CHECK_EXCEL_PATH,  # 처리할 파일 경로
            "function": process_folder_for_category_check,  # 실행할 함수
            "args": [],  # 위치 인자
            "kwargs": {}  # 키워드 인자
        },
        "이미지 필터링": {
            "path": EXCEL_IMAGE_FILTER_PATH,  # 처리할 파일 경로
            "function": process_imageFiltering_excel_file_xlsx,  # 실행할 함수
            # "function": process_imageFiltering_excel_file,  
            "args": [""],  # 위치 인자
            "kwargs": {}  # 키워드 인자
        },
        "상품명 가공": {
            "path": NAMING_EXCEL_PATH,  # 처리할 파일 경로
            "function": process_namingChange_excel_file,  # 실행할 함수
            "args": ['GPT조합'],  # 위치 인자
            "kwargs": {}  # 키워드 인자
        },
        "도매토피아 가공": {
            "path": CODE_EXCEL_PATH,  # 처리할 파일 경로
            "function": process_add_prefix_to_excel_in_folder_with_sheets,  # 실행할 함수
            "args": ['B', 'GT_'],  # 위치 인자
            "kwargs": {}  # 키워드 인자
        },
        "순환 파일 테스트": {
            "path": EXCEL_FILTER_PATH,  # 처리할 파일 경로
            "function": make_rotation_excel,  # 실행할 함수
            "args": [],  # 위치 인자
            "kwargs": {}  # 키워드 인자
        },
            "파일분할 테스트": {
            "path": EXCEL_SPLIT_PATH,  # 처리할 파일 경로
            "function": split_excel_by_rows,  # 실행할 함수
            "args": [],  # 위치 인자
            "kwargs": {}  # 키워드 인자
        }
    }

    while True:
        # 선택지 정의
        choices = {
            "0": "음식 카테고리 체크",
            "1": "이미지 필터링",
            "2": "상품명 가공",
            "3": "도매토피아 가공",
            "4": "순환 파일 테스트",
            "44": "파일분할 테스트"
        }

        # Logger를 사용해 선택지 출력
        logger.log_choices(choices, "자동화")


        # 사용자 입력 받기
        choice = input("선택 (아무것도 입력하지 않으면 종료): ").strip()
        

        # 입력이 없는 경우 프로그램 종료
        if not choice:
            logger.log("프로그램을 종료합니다. 선택이 이루어지지 않았습니다.", level="INFO")
            break

        # 유효한 선택 확인
        valid_choices = choices.keys()  # 유효한 선택지 키

        if choice not in valid_choices:
            print("잘못된 선택입니다. 다시 시도하세요.")
            continue

        # 선택에 따라 프로세스 실행
        execute_process(choices[choice], process_mapping)

        # 작업 완료 메시지 출력 후 종료
        logger.log("작업이 완료되었습니다. 프로그램을 종료합니다.", level="INFO", also_to_report=True, separator='2line')
        break


    

    
    



