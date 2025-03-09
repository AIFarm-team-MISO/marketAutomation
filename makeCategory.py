import pandas as pd
import json
import os

# 변환 실행 (엑셀 파일 경로 입력)
excel_file_path = r"F:\work\#쇼핑몰\#대량등록\#상품순환 엑셀파일\#카테고리사전\category_20250309_152239.xlsx"

def convert_excel_to_json(excel_file):
    """
    네이버 카테고리 엑셀 파일을 JSON 파일로 변환하는 함수.
    :param excel_file: 입력 엑셀 파일 경로
    """
    print("🔄 엑셀 파일을 불러오는 중...")

    # 1️⃣ 엑셀 파일 불러오기
    df = pd.read_excel(excel_file, dtype={"카테고리번호": str})  # 카테고리번호를 문자열로 유지
    print(f"✅ 엑셀 파일 불러오기 완료! 총 {len(df)}개의 카테고리 데이터 발견")

    # 2️⃣ JSON 데이터 생성 (카테고리번호 기반)
    category_dict = {}
    all_keywords = set()  # 모든 카테고리 키워드를 저장할 집합 (중복 방지)

    for _, row in df.iterrows():
        category_number = row["카테고리번호"]  # Key: 카테고리 번호

        # 3️⃣ 각 카테고리 단계별 키워드 분리
        대분류 = row["대분류"].split("/") if pd.notna(row["대분류"]) else []
        중분류 = row["중분류"].split("/") if pd.notna(row["중분류"]) else []
        소분류 = row["소분류"].split("/") if pd.notna(row["소분류"]) else []
        세분류 = row["세분류"].split("/") if pd.notna(row["세분류"]) else []

        # 4️⃣ 전체 카테고리 키워드 리스트 생성
        카테고리키워드리스트 = 대분류 + 중분류 + 소분류 + 세분류  # 모든 분류 키워드 포함
        all_keywords.update(카테고리키워드리스트)  # 전체 키워드 저장 (중복 방지)

        # 5️⃣ JSON 데이터 구성
        category_dict[category_number] = {
            "카테고리키워드리스트": 카테고리키워드리스트,
            "대분류": 대분류,
            "중분류": 중분류,
            "소분류": 소분류,
            "세분류": 세분류,
            "매칭키워드": []  # 초기에는 빈 리스트, 이후 API 결과로 업데이트 가능
        }

    # 6️⃣ 모든 카테고리 키워드를 JSON에 추가
    category_dict["모든키워드"] = list(all_keywords)  # 집합(set) → 리스트 변환

    # 7️⃣ JSON 파일 저장 경로 설정 (엑셀 파일과 동일한 폴더에 저장)
    json_file = os.path.join(os.path.dirname(excel_file), "naver_category_dic.json")

    # 8️⃣ JSON 파일 저장
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(category_dict, f, ensure_ascii=False, indent=4)

    print(f"✅ JSON 파일 변환 완료! 저장 경로: {json_file}")

if __name__ == "__main__":
    print("🚀 네이버 카테고리 엑셀 → JSON 변환을 시작합니다...")

    convert_excel_to_json(excel_file_path)
    
    print("🎯 모든 작업이 완료되었습니다!")
