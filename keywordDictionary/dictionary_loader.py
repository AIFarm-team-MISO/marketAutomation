import pandas as pd
import os
from typing import Dict
from keywordOptimization.product_info import KeywordInfo

def load_dictionary(file_path="keywordDictionary/dictionary.xlsx") -> Dict[str, KeywordInfo]:
    """
    엑셀 파일에서 키워드 사전을 로드하여 KeywordInfo 객체로 변환하는 함수.
    각 메인 키워드에 대해 용도, 사양, 스타일, 기타 카테고리를 분리하여 저장합니다.
    파일이 없을 경우 기본 구조로 생성합니다.
    """
    # 파일이 없을 경우 기본 구조로 생성하고 바로 반환
    if not os.path.exists(file_path):
        print("[디버그] 파일이 없으므로 기본 구조로 새 파일을 생성합니다.")
        
        # 기본 구조 생성
        data = {
            "메인키워드": [],
            "용도": [],
            "사양": [],
            "스타일": [],
            "기타 카테고리": [],
            "고정 키워드": []  # 새로운 '고정 키워드' 열 추가
        }
        
        # 데이터프레임 생성 및 엑셀 저장
        df = pd.DataFrame(data)

        # 파일 생성
        with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="키워드사전")
            writer.sheets["키워드사전"].activate()  # 시트 활성화

        print(f"[디버그] 새 키워드 사전 파일 생성 완료: {file_path}")
        return {}  # 빈 사전을 반환

    # 파일이 있는 경우 로드
    df = pd.read_excel(file_path, sheet_name="키워드사전")
    # print(f"[디버그] 엑셀 파일 열 이름: {df.columns.tolist()}")

    dictionary = {}
    for _, row in df.iterrows():
        main_keyword = row["메인키워드"]
        
        # 메인 키워드가 NaN이거나 빈 문자열인 경우 건너뜀
        if pd.isna(main_keyword) or main_keyword == "":
            continue
        
        # KeywordInfo 객체 생성
        keyword_info = KeywordInfo(
            main_keyword=main_keyword,
            use=row["용도"].split(", ") if pd.notna(row["용도"]) else [],
            spec=row["사양"].split(", ") if pd.notna(row["사양"]) else [],
            style=row["스타일"].split(", ") if pd.notna(row["스타일"]) else [],
            extra=row["기타 카테고리"].split(", ") if pd.notna(row["기타 카테고리"]) else [],
            fixed_keywords=row["고정 키워드"].split(", ") if pd.notna(row["고정 키워드"]) else []  # 고정 키워드 로드
        )
        
        dictionary[main_keyword] = keyword_info  # KeywordInfo 객체를 딕셔너리에 저장

    # print("[디버그] 사전 로드 성공:", dictionary)
    return dictionary

def save_dictionary(dictionary: Dict[str, KeywordInfo], file_path="keywordDictionary/dictionary.xlsx"):
    """
    KeywordInfo 객체로 구성된 키워드 사전을 엑셀 파일로 저장하는 함수.

    Parameters:
    - dictionary (Dict[str, KeywordInfo]): 메인 키워드와 관련 키워드를 가진 KeywordInfo 객체의 딕셔너리
    - file_path (str): 저장할 엑셀 파일 경로 (기본값: "keywordDictionary/dictionary.xlsx")
    """
    # 데이터 구조 설정
    data = {
        "메인키워드": [],  # 한글로 설정
        "용도": [],
        "사양": [],
        "스타일": [],
        "기타 카테고리": [],
        "고정 키워드": []
    }

    # 딕셔너리에서 각 키워드 정보를 가져와 데이터에 추가
    for main_keyword, keyword_info in dictionary.items():
        data["메인키워드"].append(keyword_info.main_keyword)
        data["용도"].append(", ".join(keyword_info.use))
        data["사양"].append(", ".join(keyword_info.spec))
        data["스타일"].append(", ".join(keyword_info.style))
        data["기타 카테고리"].append(", ".join(keyword_info.extra))
        data["고정 키워드"].append(", ".join(keyword_info.fixed_keywords))

    # 폴더 경로가 없을 경우 자동 생성
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # DataFrame을 엑셀 파일로 저장
    df = pd.DataFrame(data)
    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="키워드사전")  # 시트 이름 지정

    print(f"[디버그] 사전 저장 완료: {file_path}")
    print("="*100)




if __name__ == "__main__":
    dictionary = load_dictionary()
    save_dictionary(dictionary)
