import os
import sys
import pandas as pd
from imageFilter.excel.file_handler import read_excel_file, save_excel_file
from config.settings import FILE_EXTENSION_xls
from utils.excel.excel_utils import apply_filter_and_sort_xls, insert_column_before, apply_row_color_by_condition, update_seller_codes
from utils.excel.excel_utils import column_letter_to_index

from imageFilter.excel.url_filter import save_filtered_urls
from keywordOptimization.naver_api import generate_optimized_names
from keywordOptimization.product_info import ProductInfo, ProcessedProductInfo
from keywordOptimization.keyword_filter_never import apply_filters

from keywordDictionary.dictionary_loader import load_dictionary, save_dictionary
from keywordDictionary.keyword_extractor import extract_keywords
from keywordOptimization.gpt_result_generating import gpt_result_generate_name
from utils.progress.calculate_progress import calculate_estimates, run_filtering_item_process, print_progress_bar



from utils.log_utils import Logger

# logs 디렉터리에 로그 파일이 생성됩니다.
logger = Logger(log_file="logs/debug.log", enable_console=True)

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


def process_namingChange_excel_file(file_path, file_name, flag):
    """

    1. 폴더에 있는 기존 파일을 복사해 내용을 수정하여 output 파일(순환파일) 을 생성함
    2. 기존에 이미지필터링을 통과했는지 확인하여 필터링 실행여부를 결정, 필터링 실행후 필터링 모음파일에 저장

    Parameters:
    - file_path (str): 엑셀 파일이 위치한 폴더 경로
    - file_name (str): 엑셀 파일 이름 (확장자 제외)
    - flag (str) : 가공형태 '연관검색',  '상위검색'등 네이버에 전달한 검색형태 

    - tuple: (엑셀 sheet, 복사된 writable_book, writable_sheet)
      - sheet: 최초 폴더의 있는 엑셀의 첫 번째 시트를 나타내는 객체, 데이터를 읽기 위해 사용
      - writable_book: 기존 엑셀 파일을 복사하여 수정 가능한 형태로 만든 workbook 객체. 
                       데이터를 변경하거나 저장하기 위해 사용
      - writable_sheet: writable_book 내의 첫 번째 시트를 나타내는 객체. 
                        이 시트를 통해 셀 데이터를 수정하거나 추가할 수 있음.

    """ 

    sheet, writable_book, writable_sheet = read_excel_file(file_path, file_name, FILE_EXTENSION_xls)
    if sheet is None:
        return

    name_column_index = 'E'       # '상품명*' 열번호 (썸네일) 이후 이앞열에 열을 추가하므로 결과적으로 이열에 가공내용이 들어감
    number_column_index='B'       # '판매자코드' 열번호 
    name_column_index_int = column_letter_to_index(name_column_index)
    number_column_index_int = column_letter_to_index(number_column_index)

    # 가공타입 설정 : 현재 연관검색어 
    opt_tpye = flag

    # '상품명*' 앞에 새로운 열 삽입 (가공상품명의 결과를 추가하기 위해)
    insert_column_before(sheet, writable_sheet, name_column_index, "가공결과")


    # 기본상품명 리스트 생성 (3행부터 시작)
    naming_list = [
        sheet.cell_value(idx, name_column_index_int) 
        for idx in range(2, sheet.nrows)  # 데이터가 3행부터 시작하므로 인덱스를 2부터 시작
        if pd.notna(sheet.cell_value(idx, name_column_index_int))
    ]
    logger.log_separator()

    # 총 상품 개수 로그 및 저장
    total_items = sheet.nrows - 2
    # 행 개수를 직접 로그 출력
    logger.log(f"처리할 기본상품명 행 갯수: {total_items}", level="DEBUG")
    # logger.log_list("기본상품명가공 목록", naming_list)
    logger.log_separator()

    # 키워드사전 로드
    dictionary = load_dictionary()

    # 사전 내용을 로그에 출력
    # logger.log_dict("키워드 사전 데이터", dictionary)
    # logger.log_separator()

    task_type = "상품명가공"
    # gpt 비용, 시간 확인, 프로그램실행유무
    if run_filtering_item_process(naming_list, dictionary, task_type):

        # 초기 사전 상태 저장
        initial_dictionary_snapshot = {
            key: set(data.get("기본상품명", []))
            for key, data in dictionary.items()
        }

        # 기본상품명 분석, 메인과 보조키워드 추출
        extract_namingData_list = []
        initial_existing_count = 0  # 사전에 이미 등록된 기본상품명 수
        added_to_dictionary_count = 0  # 사전에 새로 추가된 기본상품명 수
        # 처리되지 못한 기본상품명을 저장할 리스트
        missing_after_processing = []  # >> 이 리스트에 저장되지 않은 상품명을 추적
        # 임계치 설정
        MISSING_THRESHOLD = 50  # 사전에 기록되지 않은 상품명이 이 값을 초과하면 종료

        for index, original_name in enumerate(naming_list, start=1):
            logger.log(f"▶️ [{index}/{total_items}] '{original_name}' 처리 시작", level="INFO")

            # 진행률 표시
            print_progress_bar(index, total_items)
            
            # 기본상품명으로 사전데이터를 얻음 
            namingData = extract_keywords(original_name, dictionary)

            if namingData is not None:
                # 디버깅: 각 gpt_data 출력
                logger.log_dict(f" - {original_name}- 에 대한 gpt_data", namingData)
                logger.log_separator()
                extract_namingData_list.append(namingData)


                # 사전에서 기본상품명 여부 확인 (extract_keywords 호출 전 상태 기준)
                is_existing = any(
                    original_name in initial_dictionary_snapshot.get(key, set())
                    for key in initial_dictionary_snapshot
                )

                if is_existing:
                    initial_existing_count += 1  # 이미 사전에 등록된 기본상품명
                else:
                    # 사전에 새로 추가된 기본상품명 확인 (extract_keywords 호출 후 상태 기준)
                    is_added = any(
                        original_name in set(data.get("기본상품명", []))
                        for key, data in dictionary.items()
                    )

                    if is_added:
                        added_to_dictionary_count += 1  # 사전에 새로 추가된 기본상품명
                    else:
                        # 처리 후에도 사전에 기록되지 않은 상품명 추적
                        missing_after_processing.append(original_name)

                        # 임계치 초과 확인
                        if len(missing_after_processing) >= MISSING_THRESHOLD:
                            logger.log(
                                f"❌ 임계치 초과: 사전에 기록되지 않은 상품명 수가 {MISSING_THRESHOLD}개를 초과했습니다. 프로그램을 종료합니다.",
                                level="CRITICAL"
                            )
                            logger.log(f"❌ 기록되지 않은 상품명: {missing_after_processing}", level="ERROR")
                            raise SystemExit("프로그램이 종료되었습니다. 문제를 확인하세요.")



            else:
                logger.log(f"⚠️ {original_name}에 대한 namingData가 없습니다.", level="WARNING")


        # extract_namingData_list와 기본상품명 리스트 길이 비교: 최초갯수와 같지않으면 실행종료 
        if len(naming_list) != len(extract_namingData_list):
            error_message = (
                f"❌ 데이터 불일치: 기본상품명 리스트의 길이 ({len(naming_list)}) "
                f"와 extract_namingData_list의 길이 ({len(extract_namingData_list)})가 다릅니다."
            )
            logger.log(error_message, level="ERROR")
            raise ValueError(error_message)  # 프로그램 종료     
        

        # 최종 결과 출력
        print_progress_bar(total_items, total_items)
        sys.stdout.write("\n")  # 로그 메시지가 진행률 바를 덮지 않도록 처리

        # 최종 통계 출력
        logger.log(f"✅ 모든 데이터 처리 완료! 처리된 데이터 수: {len(extract_namingData_list)} / {len(naming_list)}", level="INFO")
        logger.log(f"✅ 사전에 이미 존재했던 기본상품명 수: {initial_existing_count}", level="INFO")
        logger.log(f"✅ 사전에 새로 추가된 기본상품명 수: {added_to_dictionary_count}", level="INFO")
        # logger.log(f"✅ 최종 사전 내 총 기본상품명 수: {sum(len(data.get('기본상품명', [])) for data in dictionary.values())}", level="INFO")

        #만약 사전에 기록되지 않은경우 ->  처리되지 못한 기본상품명 출력
        if missing_after_processing:
            logger.log(
                f"❌ 처리 후에도 사전에 기록되지 않은 상품명 수: {len(missing_after_processing)}",
                level="ERROR"
            )
            logger.log(f"❌ 기록되지 않은 상품명 리스트: {missing_after_processing}", level="ERROR")


    
    else:
        print("프로그램을 중단했습니다.")
        sys.exit()  # 프로그램 종료
    
    

    # logger.log_list('GPT의 결과에 데이터', extract_namingData_list)
    print('\n')
    logger.log_separator()
    logger.log('GPT의 결과에 따른 조합시작')
    logger.log_separator()


    gpt_optimized_name_list = []  # 최종 결과를 담을 리스트
    basic_product_names = []  # 기본상품명 리스트

    for namingData in extract_namingData_list:

        try:
            # 현재 namingData에는 딕셔너리 값이 하나만 있으므로 메인키워드 데이터에 바로 접근
            main_keyword = list(namingData.keys())[0]  # 첫 번째 키 가져오기
            product_data = namingData[main_keyword]

            # 기본상품명 가져오기
            basic_product_name = product_data["기본상품명"]
            logger.log(f"검색타입 : {opt_tpye} , 처리 중인 메인 키워드: {main_keyword}, 상품명: {basic_product_name}")

            # 기본상품명 리스트에 저장
            basic_product_names.append(basic_product_name)

            # 최적화된 상품명 생성
            optimized_name = gpt_result_generate_name(basic_product_name, dictionary) 
            gpt_optimized_name_list.append(optimized_name)
        
        except Exception as e:  # 모든 예외 처리
            logger.log(f"⚠️ 예외 발생: {e}. namingData: {namingData}", level="ERROR")
            basic_product_names.append('#오류#')
            continue



    

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

    

    # 결과를 확인하거나 이후 단계에서 사용
    logger.log_separator()
    logger.log_processed_data(basic_product_names, gpt_optimized_name_list, title="네이버 연관검색, 필터링 이후 가공상품명가공 리스트")

    logger.log(f"💾가공상품명 엑셀 기록시작")
    logger.log_separator()
    # 엑셀에 가공상품명에 가공된 상품명을 입력
    for new_idx, name in enumerate(gpt_optimized_name_list):
        logger.log(f"💾{opt_tpye}상품명: {name} (글자 수: {len(name)})", level="INFO")
        writable_sheet.write(new_idx + 2, name_column_index_int, name)  # 각 데이터를 엑셀의 해당 열에 기록

    # 가공타입을 판매자관리코드에 접두사로 추가 
    update_seller_codes(sheet, writable_sheet, number_column_index_int, opt_tpye)

    # 가공된 상품명 열을 노란색으로 칠함 
    apply_row_color_by_condition(
        writable_sheet=writable_sheet,
        target_column=name_column_index_int,
        final_optimized_naming_list=gpt_optimized_name_list,
        color_name="yellow"
    )

    # 결과 파일 저장 (output 파일(순환파일) 생성)
    output_file_path = os.path.join(file_path, f"{file_name}_output.xls")
    save_excel_file(writable_book, output_file_path)