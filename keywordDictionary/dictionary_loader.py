import json
import pandas as pd
import os
from typing import Dict
from keywordOptimization.product_info import KeywordInfo

# Logger 클래스 가져오기
from utils.log_utils import Logger

# Logger 초기화
logger = Logger(log_file="logs/debug.log", enable_console=True)

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
