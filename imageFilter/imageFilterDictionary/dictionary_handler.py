from utils.global_logger import logger

from config.settings import IMAGE_FILTER_DICTIONARY_PATH

import json
from typing import List, Tuple

def load_dictionary(url_list):
    """
    기존 필터링된 URL 목록과 주어진 URL 리스트를 비교하여 결과를 반환하는 함수.

    Parameters:
    - FILTERED_URL_FILE (str): 기존 필터링된 URL 목록이 저장된 JSON 파일 경로
    - url_list (list): 이미지 URL 리스트

    Returns:
    - result (list): 
        ("중복-문자있음", image_url)        : 이전에 문자 있음으로 필터링된 이미지
        ("중복-문자없음", image_url)        : 이전에 문자 없음으로 필터링된 이미지
        ("새로운이미지", image_url)        : 기존에 필터링되지 않은 이미지
    """
    # 반환할 리스트 초기화
    result = []

    # 기존에 저장된 URL 데이터를 로드
    try:
        with open(IMAGE_FILTER_DICTIONARY_PATH, 'r', encoding='utf-8') as file:
            existing_data = json.load(file)
    except FileNotFoundError: 
        print(f"필터링 모음 JSON 파일이 존재하지 않습니다. 새로 생성합니다: {IMAGE_FILTER_DICTIONARY_PATH}")
        existing_data = {}       
        
        # 빈 JSON 파일 생성
        with open(IMAGE_FILTER_DICTIONARY_PATH, 'w', encoding='utf-8') as file:
            json.dump(existing_data, file, ensure_ascii=False, indent=4)
            print(f"[INFO] 빈 JSON 파일이 생성되었습니다: {IMAGE_FILTER_DICTIONARY_PATH}")
  
        # 구현이 끝난후에는 사전이 없으면 프로그램 종료하도록 변경하자!!! 
        # raise FileNotFoundError(f"[ERROR] 필터링 사전 파일이 없습니다. 프로그램을 종료합니다. 파일경로 : {IMAGE_FILTER_DICTIONARY_PATH}")

    # URL 리스트와 기존 목록 비교
    for image_url in url_list:
        if image_url in existing_data:
            if existing_data[image_url]["filtered_status"] == "문자있음":
                result.append(("중복-문자있음", image_url))
            elif existing_data[image_url]["filtered_status"] == "문자없음":
                result.append(("중복-문자없음", image_url))
        else:
            result.append(("새로운이미지", image_url))

    return result


def save_image_filter_dictionary(filtered_urls: List[Tuple[str, str, str]], no_text_urls: List[Tuple[str, str]]):
    """
    필터링된 URL 데이터를 JSON 파일로 저장 (중복 방지).

    Parameters:
        filtered_urls (list): 문자 있는 URL 데이터 (판매자 코드, URL, 필터링 텍스트).
        no_text_urls (list): 문자 없는 URL 데이터 (판매자 코드, URL).
        filtered_url_file (str): JSON 파일 경로.
    """
    # 기존 데이터를 로드
    try:
        with open(IMAGE_FILTER_DICTIONARY_PATH, 'r', encoding='utf-8') as file:
            existing_data = json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"[ERROR] 필터링 사전 파일이 없어 사전 업데이트에 실패하였습니다. 프로그램을 종료합니다. 파일경로 : {IMAGE_FILTER_DICTIONARY_PATH}")
    except json.JSONDecodeError:
        raise FileNotFoundError(f"[ERROR] 필터링 사전 파일이 손상되어 사전 업데이트에 실패하였습니다. 프로그램을 종료합니다. 파일경로 : {IMAGE_FILTER_DICTIONARY_PATH}")

    # 새 데이터를 추가
    new_data = {}
    for seller_code, url, detected_text in filtered_urls:
        if url not in existing_data:  # 중복 방지
            new_data[url] = {
                "product_code": seller_code,
                "filtered_status": "문자있음",
                "filtered_text": detected_text,
            }

    for seller_code, url in no_text_urls:
        if url not in existing_data:  # 중복 방지
            new_data[url] = {
                "product_code": seller_code,
                "filtered_status": "문자없음",
            }

    # 기존 데이터에 새 데이터 병합
    existing_data.update(new_data)

    # JSON 파일 저장
    with open(IMAGE_FILTER_DICTIONARY_PATH, 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)

    print(f"[INFO] JSON 파일로 저장 완료: {IMAGE_FILTER_DICTIONARY_PATH}")
