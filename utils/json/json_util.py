from utils.global_logger import logger

import json
import pandas as pd

    # 엑셀 이관작업 
    # json_output_file_name = make_output_file_path(CONVERT_URL_FILE, base_file_name, "convert", FILE_EXTENSION_JSON)
    # print("json_output_file_name : " + json_output_file_name)
    # convert_excel_to_json(FILTERED_URL_FILE, json_output_file_name)

def load_config(config_file):
    """
    JSON 설정 파일을 로드합니다.
    :param config_file: JSON 파일 경로
    :return: 설정 데이터 딕셔너리
    """
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.log(f"⚠️ 설정 파일 로드 중 에러 발생: {e}", level="ERROR")
        raise

def read_excel_all_sheets(file_path):
    """
    엑셀 파일의 모든 시트를 읽어 딕셔너리로 반환합니다.

    Parameters:
        file_path (str): 엑셀 파일 경로

    Returns:
        dict: {sheet_name: pandas.DataFrame}
    """
    return pd.read_excel(file_path, sheet_name=None)

def convert_excel_to_json(excel_file_path, json_file_path):
    """
    엑셀 파일 데이터를 JSON 파일로 변환합니다.

    Parameters:
        excel_file_path (str): 엑셀 파일 경로
        json_file_path (str): 생성할 JSON 파일 경로

    Returns:
        None
    """
    # 모든 시트 읽기
    sheets = read_excel_all_sheets(excel_file_path)

    # JSON 데이터 저장용 딕셔너리
    json_data = {}

    # 통계 변수 초기화
    count_with_text = 0
    count_without_text = 0

    # 문자있음 시트 처리
    if '문자있음' in sheets:
        df_with_text = sheets['문자있음']
        for _, row in df_with_text.iterrows():
            seller_code = row[0]  # 판매자 관리 코드
            url = row[1]          # URL
            filtered_text = row[2]  # 필터링된 문자

            json_data[url] = {
                "product_code": seller_code,
                "filtered_status": "문자있음",
                "filtered_text": filtered_text
            }
            count_with_text += 1

    # 문자없음 시트 처리
    if '문자없음' in sheets:
        df_without_text = sheets['문자없음']
        for _, row in df_without_text.iterrows():
            seller_code = row[0]  # 판매자 관리 코드
            url = row[1]          # URL

            json_data[url] = {
                "product_code": seller_code,
                "filtered_status": "문자없음"
            }
            count_without_text += 1

    # JSON 파일로 저장
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(json_data, json_file, ensure_ascii=False, indent=4)

    print(f"[INFO] JSON 파일로 저장 완료: {json_file_path}")
    print(f"[INFO] 문자있음 갯수: {count_with_text}개")
    print(f"[INFO] 문자없음 갯수: {count_without_text}개")

    print(f"[INFO] JSON 파일로 저장 완료: {json_file_path}")

