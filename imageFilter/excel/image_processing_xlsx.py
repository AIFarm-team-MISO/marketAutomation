import sys
from utils.global_logger import logger

import pandas as pd
from imageFilter.excel.image_processing import load_filtered_urls
from imageFilter.ocr_google.myImageFiltering import is_text_in_image

from imageFilter.imageFilterDictionary.dictionary_handler import load_dictionary, save_image_filter_dictionary
from utils.progress.calculate_progress import calculate_estimates, run_filtering_item_process, print_progress_bar, initialize_summary, log_for_process_bar,finish_progressbar_summary,finalize_progress_bar


'''
{
  "https://example.com/image1.jpg": {
    "product_code": "ZEN_14",
    "filtered_status": "문자있음",
    "filtered_text": ["filtered Text 1", "filtered Text 2"]
  },
  "https://example.com/image2.jpg": {
    "product_code": "판매자코드1",
    "filtered_status": "문자없음"
  },

'''

def process_image_urls_xlsx(sheet, image_column_name, seller_code_column_name, task_type="single"):
    """
    이미지 URL을 처리하여 문자 여부에 따라 필터링된 URL과 관련 데이터를 분류하는 함수.

    Parameters:
        sheet (pd.DataFrame): 엑셀 시트 데이터프레임.
        image_column_index (int): 이미지 URL이 위치한 열 인덱스.
        seller_code_column_index (int): 판매자 관리 코드가 위치한 열 인덱스.
        filtered_url_file (str): 기존 필터링된 URL 목록 파일 경로.

    Returns:
        dict: 필터링 결과, 문자 있음/없음 URL 목록, 새로운 URL 통계 정보.
    """
    logger.log_separator()
    logger.log("🖼️   이미지 URL 처리 시작 🖼️", level="INFO")
    logger.log(f"이미지필터링 작업타입: {task_type}", level="INFO", also_to_report=True, separator="none")

    try:
        # URL 리스트 생성
        url_list = extract_urls_from_column(sheet, image_column_name, task_type)

        logger.log(f"이미지 갯수 : {len(url_list)} ", level="INFO", also_to_report=True, separator="none")
        # logger.log_list("이미지 URL ", url_list, level="INFO")

        filtered_result = load_dictionary(url_list)
        logger.log_list("filtered_result ", filtered_result, level="INFO")


        # 상태별 개수 초기화
        count_text_present = 0  # "문자있음" 개수
        count_text_absent = 0   # "문자없음" 개수
        count_new_image = 0     # "새로운이미지" 개수
        logger.log("📌 URL 사전대조 결과", level="INFO", also_to_report=True, separator="dash-1line")
        
        for status, image_url in filtered_result:
            # logger.log(f"상태: {status}, URL: {image_url}")
            status = status.strip().lower()  # 공백 제거 및 소문자 변환

            # 상태별 카운트
            if status == "중복-문자있음":
                count_text_present += 1
            elif status == "중복-문자없음":
                count_text_absent += 1
            elif status == "새로운이미지":
                count_new_image += 1
            else:
                logger.log(f"⚠️ 예상치 못한 상태: {status}", level="WARNING")

        # 상태별 개수 로그 출력
        logger.log(f"총 '문자있음' 개수: {count_text_present}", level="INFO", also_to_report=True, separator="none")
        logger.log(f"총 '문자없음' 개수: {count_text_absent}", level="INFO", also_to_report=True, separator="none")
        logger.log(f"총 '새로운이미지' 개수: {count_new_image}", level="INFO", also_to_report=True, separator="none")

        sheet = image_filtering_process(filtered_result, sheet, seller_code_column_name, image_column_name, task_type)

        
        return sheet


    except Exception as e:
        logger.log(f"이미지 URL 처리(process_image_urls_xlsx) 중 오류 발생: {e}", level="ERROR")
        raise


def image_filtering_process(filtered_result, sheet, seller_code_column_name, image_column_name, task_type="single"):
    """
    이미지 필터링 프로세스 실행.

    Parameters:
        filtered_result (list): 필터링된 결과 (상태, URL).
        sheet (pd.DataFrame): 엑셀 시트 데이터프레임.
        seller_code_column_name (str): 판매자 관리 코드 열 이름.

    Returns:
        pd.DataFrame: 필터링 결과가 반영된 데이터프레임.
    """

    process_type = "이미지필터링"

    run_filtering_item_process(filtered_result, process_type, task_type)


    logger.log_separator()
    logger.log("🔄 이미지 필터링 프로세스 시작", level="INFO")

    try:
        # URL 필터링 결과 분류
        data, filtered_urls, no_text_urls, stats = filter_and_classify_urls(filtered_result, sheet, seller_code_column_name)

        # 필터링 결과 저장
        save_image_filter_dictionary(filtered_urls, no_text_urls)


        # # 데이터프레임의 인덱스 확인
        # logger.log(f"현재 데이터프레임 인덱스: {sheet.index}", level="DEBUG")
        # # 인덱스를 0부터 시작하도록 재설정
        # sheet.reset_index(drop=True, inplace=True)
        logger.log(f"변경된 데이터프레임 인덱스: {sheet.index}", level="DEBUG")


        '''
            - 데이터 무결성 체크 -
            data 에는 필터링의 결과 (예: 중복-문자있음) 가 들어있고 
            이데이터가 기존의 데이터의 위치에 정확히 들어가야 하기 때문에
            sheet의 각행에 있는 url과 data의 url을 비교 

            : 결론적으로 각행에서 이미지url만 가져가서 비교후 다시 결과와 함께 
            동일한 행에 넣어주어야 되기 때문에 이작업이 필요.
        
        '''
        # 필터링 결과를 데이터프레임에 기록
        for idx, (status, image_url) in enumerate(data):
            try:

                        # 🔍 디버그 로그
                logger.log(f"🔍 [디버그] {idx + 1}번째 행 처리 중 - 상태: {status}, 이미지 URL: {image_url}", level="DEBUG")

                # ✅ 안전한 접근 (iloc 사용)
                if idx >= len(sheet):
                    logger.log(f"⚠️ [경고] 유효하지 않은 인덱스 접근: {idx} (총 {len(sheet)}개 행)", level="WARNING")
                    continue

                # 📸 이미지 URL 가져오기
                cell_url = sheet.iloc[idx][image_column_name] if pd.notna(sheet.iloc[idx][image_column_name]) else ""

                # 🔄 URL 비교
                normalized_image_url = str(image_url).strip().lower()
                normalized_cell_url = str(cell_url).strip().lower()

                # ✅ 무결성 검사 및 필터링 결과 기록
                if normalized_image_url == normalized_cell_url:
                    sheet.at[sheet.index[idx], "필터링결과"] = status
                    logger.log(f"✅ [성공] 행 {idx + 1}: '{status}' 기록 완료.", level="INFO")
                else:
                    logger.log(f"⚠️ [불일치] 행 {idx + 1}: 기대값과 실제값 불일치", level="WARNING")


            except KeyError as ke:
                logger.log(f"❌ [키에러] 행 {idx  + 1} - {ke}", level="ERROR")
                raise
            except IndexError as ie:
                logger.log(f"❌ [인덱스에러] 행 {idx  + 1} - {ie}", level="ERROR")
                raise
            except Exception as e:
                logger.log(f"❌ [예외 발생] 행 {idx  + 1} - {type(e).__name__}: {e}", level="ERROR")
                raise



        logger.log("✅ 모든 필터링 결과가 성공적으로 기록되었습니다.", level="INFO")


        return sheet


    except Exception as e:
        logger.log(f"❌ 에러 발생: {e}", level="ERROR")
        raise



def extract_urls_from_column(sheet, image_column_name, task_type="single"):
    """
    특정 열에서 유효한 URL 리스트를 추출.

    Parameters:
        sheet (pd.DataFrame): 엑셀 시트 데이터프레임.
        image_column_name (str): 이미지 URL이 위치한 열 이름.

    Returns:
        list: 유효한 URL 리스트.
    """
    if image_column_name not in sheet.columns:
        raise ValueError(f"열 '{image_column_name}'이(가) 데이터프레임에 존재하지 않습니다.")


    # # 컬럼명 출력
    # logger.log(f"컬럼명: {sheet.columns.tolist()}", level="INFO")

    # # 첫 번째 데이터 행 출력
    # logger.log(f"첫 번째 데이터 행: {sheet.iloc[0]}", level="INFO")

    # # 데이터프레임 전체 샘플 출력
    # logger.log(f"데이터프레임 샘플:\n{sheet.head(5)}", level="INFO")


    # URL 리스트 추출
    url_list = []
    image_column_index = sheet.columns.get_loc(image_column_name)  # 이미지 열의 인덱스 가져오기

    # 데이터프레임에서 유효한 URL을 순회하며 추출
    for idx in range(sheet.shape[0]):  # DataFrame의 모든 행을 순회
        cell_value = sheet.iloc[idx, image_column_index]  # 현재 행의 이미지 열 값 가져오기

        # 셀이 비어있지 않고, 문자열로 변환한 값이 "http"로 시작하는지 확인
        if pd.notna(cell_value) and str(cell_value).startswith("http"):
            url_list.append(cell_value)  # 유효한 URL이면 리스트에 추가

    # URL 리스트 길이를 로그로 출력
    # logger.log(f"추출된 URL 갯수: {len(url_list)}", level="INFO")


    return url_list


def filter_and_classify_urls(filtered_result, sheet, seller_code_column_name):
    """
    필터링된 URL 결과를 분류하고 통계를 생성.

    Parameters:
        filtered_result (list): URL 필터링 결과 리스트.
        sheet (pd.DataFrame): 엑셀 시트 데이터프레임.
        seller_code_column_name (str): 판매자 관리 코드가 위치한 열 이름.

    Returns:
        tuple: 필터링된 데이터, 문자 있음 URL, 문자 없음 URL, 새로운 URL 통계 정보.

    데이터 예시 : 
        filtered_urls :  [
        ('TDD_1000001404', 
        'https://gi.esmplus.com/greatjjuni/DM900/GTI_923/GTI_923_listimg-4.jpg', 
        '상단: FIO, 하단: URYLOVERSMILINGWARMISSTILLKLMIFTURNEDTOFOHESUNWILLPTHEC'), 
        ('TDD_1000001405', 'https://gi.esmplus.com/greatjjuni/DM900/GTI_924/GTI_924_listimg-3.jpg', '상단: 8037654MAT, 하단:')
        ]

        no_text_urls :  [
        ('TDD_1000000464', 'http://gi.esmplus.com/greatjjuni/DM100/GTI_0197/GTI_0197_listimg-2.jpg'), 
        ('TDD_1000000465', 'http://gi.esmplus.com/greatjjuni/DM100/GTI_0195/GTI_0195_listimg.jpg'), 
        ('TDD_1000001402', 'https://gi.esmplus.com/greatjjuni/DM900/GTI_921/GTI_921_listimg-3.jpg'), 
        ('TDD_1000001403', 'https://gi.esmplus.com/greatjjuni/DM900/GTI_922/GTI_922_listimg-4.jpg')
        ]

    """
    data = []
    filtered_urls = []
    no_text_urls = []
    new_url_text_count = 0
    new_url_notext_count = 0

    # 진행률 바 초기화 및 요약 정보 생성
    summary = initialize_summary()

    for i, (status, image_url) in enumerate(filtered_result):

        logger.log(f"▶️ {i+1} : {status}, {image_url} 처리 시작", level="INFO")

        # 진행률 표시
        # print_progress_bar(i, len(filtered_result))


        # DataFrame의 범위 내에서만 접근
        if i >= len(sheet):
            logger.log(f"⚠️ 인덱스 초과: sheet에는 {len(sheet)}개의 행만 존재하지만 {i+1}번째 접근 시도.", level="ERROR")
            raise ValueError(f"데이터프레임 인덱스 초과: {i+1}번째 데이터 처리 중 오류 발생.")
        
        # 판매자 관리 코드 가져오기 (안전한 접근 방식)
        seller_code = None  # 초기값 설정
        # 조건: 열이 존재하고 값이 NaN이 아닌 경우
        if seller_code_column_name in sheet.columns and pd.notna(sheet.iloc[i][seller_code_column_name]):
            seller_code = sheet.iloc[i][seller_code_column_name]
        else:  
            raise ValueError(f"⚠️ 행 {i + 1}에서 '{seller_code_column_name}' 열의 값이 없습니다. 프로그램을 종료합니다.")
        
        logger.log(f"판매자 코드: {seller_code}, URL: {image_url}", level="DEBUG")


        # 개별 작업 처리
        # log_for_process_bar(idx, image_url, summary)



        if status == "중복-문자있음":
            data.append((status, image_url))  # 처리 결과에 추가
            filtered_urls.append((seller_code, image_url, "중복-문자있음"))
        elif status == "중복-문자없음":
            data.append((status, image_url))  # 처리 결과에 추가
            no_text_urls.append((seller_code, image_url))  # 문자 없음 목록에 추가
        else:


            detected_text = is_text_in_image(image_url)

            if detected_text:
                data.append(("중복-문자있음", image_url))  # 문자 있음 상태로 데이터에 추가
                filtered_urls.append((seller_code, image_url, detected_text))  # 문자 있음 목록에 추가
                new_url_text_count += 1
            else:
                data.append(("중복-문자없음", image_url))  # 문자 없음 상태로 데이터에 추가
                no_text_urls.append((seller_code, image_url))  # 문자 없음 목록에 추가
                new_url_notext_count += 1

    stats = {
        "new_url_with_text": new_url_text_count,
        "new_url_without_text": new_url_notext_count,
        "total_new_urls": new_url_text_count + new_url_notext_count,
    }
    
    # 작업 완료 후 요약 정보 출력
    # finish_progressbar_summary(summary, len(filtered_result))

    

    logger.log("📌 URL 필터링 결과", level="INFO", also_to_report=True, separator="dash-1line")
    # 디버깅: 필터링된 URL 통계 출력
    logger.log(f"필터링 최종 목록 갯수: {len(filtered_urls)} + {len(no_text_urls)}개", also_to_report=True, separator="none")
    logger.log(f"최종 문자 있음 URL 목록 갯수: {len(filtered_urls)}개", also_to_report=True, separator="none")
    logger.log(f"최종 문자 없음 URL 목록 갯수: {len(no_text_urls)}개", also_to_report=True, separator="none")
    
    # print("\n[디버그] 문자 있음 필터링된 URL 목록:")
    # for entry in filtered_urls:
    #     print(entry)

    # print("\n[디버그] 문자 없음 필터링된 URL 목록:")
    # for entry in no_text_urls:
    #     print(entry)

    # stats를 활용하여 새롭게 추가된 URL 통계 출력
    logger.log(f"새롭게 추가된 URL 갯수: {stats['total_new_urls']}개", also_to_report=True, separator="dash-1line")
    logger.log(f"새롭게 추가된 URL 중 문자있음 갯수: {stats['new_url_with_text']}개", also_to_report=True, separator="none")
    logger.log(f"새롭게 추가된 URL 중 문자없음 갯수: {stats['new_url_without_text']}개", also_to_report=True, separator="none")



    return data, filtered_urls, no_text_urls, stats



