import json
import pandas as pd
import os
from typing import Dict
from keywordOptimization.product_info import KeywordInfo

# Logger 클래스 가져오기
from utils.log_utils import Logger

# Logger 초기화
logger = Logger(log_file="logs/debug.log", enable_console=True)

def check_naming_in_item_list(dictionary, naming_list):
    """
    JSON 데이터를 로드하여 naming_list의 문자열이 "기본상품명" 리스트에 존재하는지 확인.

    Args:
        dictionary (dict): JSON 데이터로 로드된 딕셔너리.
        naming_list (list): 확인할 문자열의 리스트.

    Returns:
        list: ("새로운문자열", naming_str) 또는 ("기존문자열", naming_str) 형식의 튜플 리스트.
    """
    results = []

    for naming_str in naming_list:  # naming_list의 순서를 유지
        found = False
        for key, data in dictionary.items():
            # "기본상품명" 키가 있는지 확인
            if "기본상품명" in data and isinstance(data["기본상품명"], list):
                base_names = data["기본상품명"]
                # naming_str이 "기본상품명" 리스트에 존재하는지 확인
                if any(naming_str in base_name for base_name in base_names):
                    results.append(("기존문자열", naming_str))
                    found = True
                    break  # 매칭되면 다음 naming_str로 이동
        if not found:
            results.append(("새로운문자열", naming_str))

    return results

def load_dictionary(file_path="keywordDictionary/dictionary.json") -> Dict[str, dict]:
    """
    JSON 파일에서 키워드 사전을 로드하는 함수.
    파일이 없을 경우 기본 구조로 새 파일을 생성합니다.

    Parameters:
    - file_path (str): JSON 파일 경로 (기본값: "keywordDictionary/dictionary.json").

    Returns:
    - dictionary (Dict[str, dict]): 키워드 사전 딕셔너리.
    """
    # 파일이 없을 경우 기본 구조로 생성
    if not os.path.exists(file_path):
        print("[디버그] 파일이 없으므로 기본 구조로 새 파일을 생성합니다.")
        
        # 빈 딕셔너리 생성
        dictionary = {}

        # 폴더 경로가 없으면 생성
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # 빈 딕셔너리를 JSON 파일로 저장
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(dictionary, file, ensure_ascii=False, indent=4)

        print(f"[디버그] 새 JSON 파일 생성 완료: {file_path}")
        return dictionary

    # 파일이 있는 경우 JSON 파일 로드
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            dictionary = json.load(file)

        print(f"[디버그] JSON 파일 로드 완료: {file_path}")
        return dictionary
    except Exception as e:
        print(f"[오류] JSON 파일 로드 실패: {e}")
        return {}

def save_dictionary(new_data: Dict[str, dict], file_path="keywordDictionary/dictionary.json") -> bool:
    """
    JSON 형식의 키워드 사전을 파일에 저장하고 검증하는 함수.
    저장 후 파일을 다시 읽어 데이터 무결성을 확인.

    Parameters:
    - new_data (Dict[str, dict]): 저장할 데이터.
    - file_path (str): JSON 파일 경로 (기본값: "keywordDictionary/dictionary.json").

    Returns:
    - bool: 저장 성공 여부.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    try:
        # 데이터를 JSON 파일로 저장
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(new_data, file, ensure_ascii=False, indent=4)

        logger.log(f"✅ 데이터가 JSON 파일에 저장되었습니다: {file_path}", level="INFO")

        # 저장 후 검증: 파일을 다시 읽어서 데이터 무결성 확인
        with open(file_path, "r", encoding="utf-8") as file:
            loaded_data = json.load(file)

        # 데이터 일치 검증
        if new_data == loaded_data:
            logger.log("✅ 저장된 데이터가 원본과 일치합니다. 무결성 검증 완료.", level="INFO")
            return True
        else:
            logger.log("❌ 저장된 데이터가 원본과 일치하지 않습니다. 무결성 검증 실패.", level="ERROR")
            return False

    except Exception as e:
        logger.log(f"❌ [오류] JSON 저장 실패: {e}", level="ERROR")
        return False

def save_dictionary_old(new_data: Dict[str, dict], file_path="keywordDictionary/dictionary.json") -> bool:
    """
    JSON 형식의 키워드 사전을 파일에 저장하는 함수. 병합 로직은 호출 측에서 처리하며,
    이 함수는 데이터를 파일에 기록하는 역할만 수행.

    Parameters:
    - new_data (Dict[str, dict]): 저장할 데이터.
    - file_path (str): JSON 파일 경로 (기본값: "keywordDictionary/dictionary.json").

    Returns:
    - bool: 저장 성공 여부.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    try:
        # 데이터를 JSON 파일로 저장
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(new_data, file, ensure_ascii=False, indent=4)

        logger.log(f"데이터가 JSON 파일에 저장되었습니다: {file_path}", level="INFO")
        return True
    except Exception as e:
        logger.log(f"[오류] JSON 저장 실패: {e}", level="ERROR")
        return False








if __name__ == "__main__":
    dictionary = load_dictionary()
    save_dictionary(dictionary)
