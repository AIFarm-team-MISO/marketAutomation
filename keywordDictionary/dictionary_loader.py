import json
import pandas as pd
import os
from typing import Dict
from keywordOptimization.product_info import KeywordInfo
from utils.validate.validate_index import validate_data_order

from utils.global_logger import logger

def filtered_naming_in_dictionary(dictionary, naming_list):
    """
    JSON 사전 데이터를 로드하여 naming_list의 문자열이 "기본상품명" 리스트에 존재하는지 확인하고, 
    naming_list와 결과의 무결성을 검증.

    Args:
        dictionary (dict): JSON 데이터로 로드된 딕셔너리.
        naming_list (list): 확인할 문자열의 리스트.

    Returns:
        list: ("새로운문자열", naming_str) 또는 ("기존문자열", naming_str") 형식의 튜플 리스트.
    """
    try:
        # 1. 입력 데이터 검증
        if not isinstance(dictionary, dict):
            raise ValueError("dictionary는 dict 형식이어야 합니다.")
        
        if not isinstance(naming_list, list):
            raise ValueError("naming_list는 list 형식이어야 합니다.")
        
        if not all(isinstance(item, str) for item in naming_list):
            raise ValueError("naming_list의 모든 항목은 문자열이어야 합니다.")
        
        # 2. 결과 계산
        results = []
        for naming_str in naming_list:
            found = False
            for key, data in dictionary.items():
                if "기본상품명" in data and isinstance(data["기본상품명"], list):
                    base_names = data["기본상품명"]
                    if any(naming_str in base_name for base_name in base_names):
                        results.append(("기존문자열", naming_str))
                        found = True
                        break
            if not found:
                results.append(("새로운문자열", naming_str))
        
        # 3. 무결성 검증: 길이 및 순서 확인
        result_names = [result[1] for result in results]  # 결과 리스트에서 이름만 추출
        
        # 길이 검증
        if len(naming_list) != len(result_names):
            raise ValueError(
                f"❌ 무결성 실패: 결과 리스트 길이({len(result_names)})와 naming_list 길이({len(naming_list)})가 일치하지 않습니다."
            )
        
        # 순서 검증
        if naming_list != result_names:
            raise ValueError(
                f"❌ 무결성 실패: 결과 리스트와 naming_list의 순서가 일치하지 않습니다.\n"
                f"naming_list: {naming_list}\n"
                f"결과 리스트: {result_names}"
            )
        
        # 4. 검증 성공 메시지
        logger.log(f"✅ 사전비교 필터링결과 :  {len(naming_list)}개의 항목에 대해 무결성 확인 완료.", level="INFO")
        return results
    except ValueError as e:
        logger.log(f"❌ filtered_naming_in_dictionary 검증 실패: {e}", level="ERROR")
        raise




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
    
import os
import json
from typing import Dict

import os
import json
import shutil
from datetime import datetime

import os
import json
from typing import Dict

import os
import json
import shutil
from typing import Dict

def save_dictionary(new_data: Dict[str, dict], file_path="keywordDictionary/dictionary.json") -> bool:
    """
    JSON 형식의 키워드 사전을 파일에 저장하고 검증하는 함수.
    저장 중 임시 파일을 활용해 데이터 손실을 방지하고, 작업 상태를 로그로 확인 가능.

    Parameters:
    - new_data (Dict[str, dict]): 저장할 데이터.
    - file_path (str): JSON 파일 경로 (기본값: "keywordDictionary/dictionary.json").

    Returns:
    - bool: 저장 성공 여부.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # 임시파일과 백업파일을 정의
    tmp_file_path = f"{file_path}.tmp"
    backup_file_path = f"{file_path}.backup"

    try:

        # 데이터 손실을 방지하기 위해 임시 파일에 먼저 저장
        with open(tmp_file_path, "w", encoding="utf-8") as tmp_file:
            json.dump(new_data, tmp_file, ensure_ascii=False, indent=4)
        logger.log(f"🟡 임시 파일 생성 완료: {tmp_file_path}", level="INFO")

        # 기존 파일이 있을 경우, 백업 파일을 생성
        if os.path.exists(file_path):
            shutil.copy2(file_path, backup_file_path)
            logger.log(f"🟡 백업 파일 생성 완료: {backup_file_path}", level="INFO")

        # 임시 파일을 원본 파일로 교체하여 저장
        shutil.move(tmp_file_path, file_path)
        logger.log(f"✅ 임시 파일에서 원본 파일로 교체 완료: {file_path}", level="INFO")

        # 저장된 데이터를 다시 읽어 무결성을 검증
        with open(file_path, "r", encoding="utf-8") as file:
            loaded_data = json.load(file)

        if new_data == loaded_data:
            logger.log("✅ 저장된 데이터가 원본과 일치합니다. 무결성 검증 완료.", level="INFO")
            return True
        else:
            logger.log("❌ 저장된 데이터가 원본과 일치하지 않습니다. 무결성 검증 실패.", level="ERROR")
            return False

    except Exception as e:
        # 저장 작업 중 오류가 발생한 경우 처리
        logger.log(f"❌ [오류] 저장 작업 중 문제 발생: {e}", level="ERROR")

        # 복구: 백업 파일이 있으면 복원
        if os.path.exists(backup_file_path):
            shutil.copy2(backup_file_path, file_path)
            logger.log(f"⚠️ 오류 발생! 백업 파일로 복원 완료: {backup_file_path}", level="WARNING")

        # 임시 파일 삭제
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
            logger.log(f"⚠️ 오류 발생! 임시 파일 삭제 완료: {tmp_file_path}", level="WARNING")

        return False

    finally:
        # 저장작업 종료 후 (작업이 성공적으로 완료된 경우)

        # 임시 파일 삭제 (남아 있는 경우 : 작업이 성공적으로 완료되면 임시 파일(.tmp)은 원본 파일로 교체되면서 삭제됨)
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
            logger.log(f"⚠️ 최종 정리: 임시 파일 삭제 완료: {tmp_file_path}", level="INFO")

        # 백업 파일 삭제 (남아 있는 경우)
        if os.path.exists(backup_file_path):
            os.remove(backup_file_path)
            logger.log(f"✅ 최종 정리: 백업 파일 삭제 완료: {backup_file_path}", level="INFO")




def save_dictionary_OLD2(new_data: Dict[str, dict], file_path="keywordDictionary/dictionary.json") -> bool:
    """
    저장 중 데이터 손실 방지를 위해 임시 파일 및 백업 파일 사용.
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
