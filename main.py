from utils.global_logger import logger

from config.settings import EXCEL_IMAGE_FILTER_PATH, CATEGORY_CHECK_EXCEL_PATH, NAMING_EXCEL_PATH, CODE_EXCEL_PATH, EXCEL_FILTER_PATH, EXCEL_SPLIT_PATH,SELLED_PRODUCT_NAVER_PATH
from config.settings import EXCEL_GODOMOLL_PATH
from config.web_automation_settings import REVIEW_PRODUCTS_PATH
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
from rotationFile.godoRotation.rotation_godo import make_rotation_godo
from selledProduct.optimize_product_naver import make_optimize_product_excel
from utils.web_automation.smartstore_review_checker.checker_main import smartstore_review_checker



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

import os


def execute_process(process_type, process_mapping):
    """
    선택한 자동화 작업에 맞는 경로와 함수를 가져와
    해당 경로 안의 파일을 순차적으로 처리한다.

    주요 기능
    ----------
    1. process_type에 해당하는 작업 설정 확인
    2. 작업 대상 경로에서 파일 목록 수집
    3. 엑셀 임시 잠금파일(~$) 제외
    4. 기존 출력파일 제외
    5. 작업별 허용 확장자만 처리
    6. 동일 파일 중복 제거
    7. 파일별 처리 함수 실행
    8. 개별 파일 오류 발생 시 다음 파일 계속 처리

    process_mapping 예시
    --------------------
    process_mapping = {
        "네이버 팔린거 최적화": {
            "path": NAVER_OPTIMIZE_PATH,
            "function": make_optimize_product_excel,
            "args": [],
            "kwargs": {},
            "extensions": (".xls", ".xlsx"),
            "exclude_keywords": (
                "_rotatet_output",
                "_output",
            ),
        }
    }

    Parameters
    ----------
    process_type : str
        실행할 작업 이름.

    process_mapping : dict
        작업별 경로, 함수, 인자, 허용 확장자 등을 담은 딕셔너리.

    Returns
    -------
    None
    """

    # ==============================================================
    # 1. 작업 유형 확인
    # ==============================================================

    if process_type not in process_mapping:
        logger.log(
            f"❌ 알 수 없는 처리 유형: {process_type}",
            level="ERROR",
            also_to_report=True,
        )
        return

    # 현재 선택된 작업의 설정값
    process_config = process_mapping[process_type]

    # 필수 설정
    selected_path = process_config.get("path")
    selected_function = process_config.get("function")

    # 선택 설정
    args = process_config.get("args", [])
    kwargs = process_config.get("kwargs", {})

    # 작업별 허용 확장자
    #
    # 설정하지 않으면 모든 확장자를 허용한다.
    allowed_extensions = process_config.get("extensions")

    # 기존 결과파일을 구분하기 위한 문자열
    exclude_keywords = process_config.get(
        "exclude_keywords",
        (
            "_rotatet_output",
            "_output",
        ),
    )

    # ==============================================================
    # 2. 작업 설정 검증
    # ==============================================================

    if not selected_path:
        logger.log(
            f"❌ '{process_type}' 작업의 경로가 설정되지 않았습니다.",
            level="ERROR",
            also_to_report=True,
        )
        return

    if not callable(selected_function):
        logger.log(
            f"❌ '{process_type}' 작업 함수가 올바르지 않습니다.",
            level="ERROR",
            also_to_report=True,
        )
        return

    # 확장자는 비교가 편하도록 모두 소문자로 변환
    if allowed_extensions:
        allowed_extensions = tuple(
            extension.lower()
            for extension in allowed_extensions
        )

    logger.log(
        (
            f"🖼️ 처리 유형: {process_type} "
            f"🖼️ 경로 내 파일처리 시작!"
        ),
        level="INFO",
        also_to_report=True,
        separator="1line",
    )

    logger.log(
        f"📂 작업 경로: {selected_path}",
        level="INFO",
        also_to_report=True,
    )

    if allowed_extensions:
        logger.log(
            f"📄 허용 확장자: {allowed_extensions}",
            level="INFO",
            also_to_report=True,
        )

    # ==============================================================
    # 3. 원본 파일 목록 가져오기
    # ==============================================================

    try:
        original_file_list = process_all_excel_files(
            selected_path
        )

    except Exception as e:
        logger.log(
            f"❌ 파일 리스트를 가져오는 중 오류 발생: {e}",
            level="ERROR",
            also_to_report=True,
            separator="2line",
        )
        return

    # 파일 목록이 None으로 반환되는 경우 방어
    if original_file_list is None:
        original_file_list = []

    logger.log(
        f"📄 검색된 원본 파일 수: {len(original_file_list)}개",
        level="INFO",
        also_to_report=True,
    )

    # ==============================================================
    # 4. 처리 대상 파일 필터링
    # ==============================================================

    filtered_file_list = []
    excluded_file_list = []

    # 중복 파일 방지용
    seen_files = set()

    for file_path, base_file_name in original_file_list:

        # 파일명이 문자열이 아닌 경우 방어
        if not isinstance(base_file_name, str):
            excluded_file_list.append(
                (
                    str(base_file_name),
                    "파일명이 문자열이 아님",
                )
            )
            continue

        clean_file_name = base_file_name.strip()

        # 빈 파일명 제외
        if not clean_file_name:
            excluded_file_list.append(
                (
                    clean_file_name,
                    "빈 파일명",
                )
            )
            continue

        # ----------------------------------------------------------
        # 4-1. 엑셀 임시 잠금파일 제외
        #
        # 엑셀 파일을 열어두면 다음 형식의 파일이 생성된다.
        # ~$1.xlsx
        # ----------------------------------------------------------
        if clean_file_name.startswith("~$"):
            excluded_file_list.append(
                (
                    clean_file_name,
                    "엑셀 임시 잠금파일",
                )
            )
            continue

        # ----------------------------------------------------------
        # 4-2. 기존 출력파일 제외
        # ----------------------------------------------------------
        if any(
            keyword in clean_file_name
            for keyword in exclude_keywords
        ):
            excluded_file_list.append(
                (
                    clean_file_name,
                    "기존 출력파일",
                )
            )
            continue

        # ----------------------------------------------------------
        # 4-3. 허용 확장자 검사
        # ----------------------------------------------------------
        _, file_extension = os.path.splitext(
            clean_file_name
        )

        file_extension = file_extension.lower()

        if (
            allowed_extensions
            and file_extension not in allowed_extensions
        ):
            excluded_file_list.append(
                (
                    clean_file_name,
                    f"지원하지 않는 확장자: {file_extension}",
                )
            )
            continue

        # ----------------------------------------------------------
        # 4-4. 동일 파일 중복 제외
        # ----------------------------------------------------------
        full_file_key = os.path.normcase(
            os.path.abspath(
                os.path.join(
                    file_path,
                    clean_file_name,
                )
            )
        )

        if full_file_key in seen_files:
            excluded_file_list.append(
                (
                    clean_file_name,
                    "중복 파일",
                )
            )
            continue

        seen_files.add(full_file_key)

        filtered_file_list.append(
            (
                file_path,
                clean_file_name,
            )
        )

    # ==============================================================
    # 5. 필터링 결과 로그
    # ==============================================================

    if excluded_file_list:
        logger.log(
            f"⏭ 처리 제외 파일 수: {len(excluded_file_list)}개",
            level="INFO",
            also_to_report=True,
        )

        for excluded_name, excluded_reason in excluded_file_list:
            logger.log(
                (
                    f"⏭ 파일 제외: {excluded_name}"
                    f" / 사유: {excluded_reason}"
                ),
                level="DEBUG",
                also_to_report=True,
            )

    logger.log(
        f"✅ 최종 처리 대상 파일 수: {len(filtered_file_list)}개",
        level="INFO",
        also_to_report=True,
    )

    logger.log(
        f"파일리스트: {filtered_file_list}",
        level="INFO",
        also_to_report=True,
    )

    # 처리할 파일이 없는 경우 종료
    if not filtered_file_list:
        logger.log(
            "⚠ 처리할 대상 파일이 없습니다.",
            level="WARNING",
            also_to_report=True,
            separator="2line",
        )
        return

    # ==============================================================
    # 6. 파일별 작업 실행
    # ==============================================================

    success_count = 0
    failure_count = 0

    for index, (
        file_path,
        base_file_name,
    ) in enumerate(
        filtered_file_list,
        start=1,
    ):

        logger.log(
            (
                f"📄 파일 처리 시작 "
                f"[{index}/{len(filtered_file_list)}]"
                f" : {base_file_name}"
            ),
            level="INFO",
            also_to_report=True,
            separator="dash-1line",
        )

        try:
            # process_mapping에서 지정한 함수 실행
            selected_function(
                file_path,
                base_file_name,
                *args,
                **kwargs,
            )

            success_count += 1

            logger.log(
                (
                    f"✅ 파일 처리 완료 "
                    f"[{index}/{len(filtered_file_list)}]"
                    f" : {base_file_name}"
                ),
                level="INFO",
                also_to_report=True,
            )

        except Exception as e:
            failure_count += 1

            logger.log(
                (
                    f"❌ 파일 처리 중 오류 발생"
                    f"\n- 파일 경로: {file_path}"
                    f"\n- 파일명: {base_file_name}"
                    f"\n- 오류: {e}"
                ),
                level="ERROR",
                also_to_report=True,
            )

            # 한 파일에서 오류가 발생해도
            # 나머지 파일 처리를 계속 진행한다.
            continue

    # ==============================================================
    # 7. 전체 작업 결과 출력
    # ==============================================================

    logger.log(
        (
            f"✅ 처리 유형 작업 종료: {process_type}"
            f"\n- 전체 대상: {len(filtered_file_list)}개"
            f"\n- 처리 성공: {success_count}개"
            f"\n- 처리 실패: {failure_count}개"
            f"\n- 처리 제외: {len(excluded_file_list)}개"
        ),
        level="INFO",
        also_to_report=True,
        separator="2line",
    )

if __name__ == "__main__":
    # zsm_login()
    

    process_mapping = {
        "네이버 팔린거 최적화": {
            "path": SELLED_PRODUCT_NAVER_PATH,
            "function": make_optimize_product_excel,
            "args": [],
            "kwargs": {},

            # 네이버 수정용 엑셀 파일만 처리
            "extensions": (
                ".xls",
                ".xlsx",
            ),

            # 이미 생성된 결과파일 제외
            "exclude_keywords": (
                "_rotatet_output",
                "_output",
            ),
        },

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
            "args": ['B', 'GK_'],  # 위치 인자
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
        },
            "고도몰 순환파일": {
            "path": EXCEL_GODOMOLL_PATH,  # 처리할 파일 경로
            "function": make_rotation_godo,  # 실행할 함수
            "args": [],  # 위치 인자
            "kwargs": {}  # 키워드 인자
        },
            "리뷰 필터링 테스트": {
            "path": REVIEW_PRODUCTS_PATH,  # 처리할 파일 경로
            "function": smartstore_review_checker,  # 실행할 함수
            "args": [],  # 위치 인자
            "kwargs": {}  # 키워드 인자
        }
    }

    while True:
        # 선택지 정의
        choices = {
            "00": "네이버 팔린거 최적화",
            "0": "음식 카테고리 체크",
            "1": "이미지 필터링",
            "2": "상품명 가공",
            "3": "도매토피아 가공",
            "4": "순환 파일 테스트",
            "44": "파일분할 테스트",
            "5": "고도몰 순환파일",
            "6": "리뷰 필터링 테스트"
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


    

    
    



