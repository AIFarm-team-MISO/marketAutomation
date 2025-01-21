
import json
from utils.global_logger import logger

from config.settings import FILE_EXTENSION_xls, FILTERED_URL_FILE, FILE_EXTENSION_JSON, CONVERT_URL_FILE
from utils.excel.excel_utils import make_input_file_path, make_output_file_path
import pandas as pd


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


def filter_json_by_product_code(json_file_path, filtered_json_file_path, product_code_prefix):
    """
    JSON 파일에서 특정 product_code 접두사를 가진 데이터만 필터링하여 새로운 JSON 파일로 저장.

    Parameters:
        json_file_path (str): 원본 JSON 파일 경로.
        filtered_json_file_path (str): 필터링된 JSON 파일 저장 경로.
        product_code_prefix (str): 필터링할 product_code의 접두사.

    Returns:
        None
    """
    try:
        # JSON 파일 읽기
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # 필터링된 데이터 생성
        filtered_data = {
            url: details
            for url, details in data.items()
            if details["product_code"].startswith(product_code_prefix)
        }

        # 필터링 결과 확인
        if not filtered_data:
            print(f"[INFO] '{product_code_prefix}'로 시작하는 product_code가 없습니다.")
        else:
            print(f"[INFO] '{product_code_prefix}'로 시작하는 product_code 항목 수: {len(filtered_data)}")

        # 필터링된 JSON 파일 저장
        with open(filtered_json_file_path, 'w', encoding='utf-8') as filtered_file:
            json.dump(filtered_data, filtered_file, ensure_ascii=False, indent=4)

        print(f"[INFO] 필터링된 JSON 파일 저장 완료: {filtered_json_file_path}")

    except FileNotFoundError:
        print(f"[ERROR] 원본 JSON 파일을 찾을 수 없습니다: {json_file_path}")
    except KeyError as e:
        print(f"[ERROR] JSON 파일 구조에 문제가 있습니다: {e}")
    except Exception as e:
        print(f"[ERROR] 필터링 중 오류 발생: {e}")
        raise


    # 엑셀 이관작업 
    # json_output_file_name = make_output_file_path(CONVERT_URL_FILE, base_file_name, "convert", FILE_EXTENSION_JSON)
    # print("json_output_file_name : " + json_output_file_name)
    # convert_excel_to_json(FILTERED_URL_FILE, json_output_file_name)

    
def main():
    """
    JSON 파일에서 특정 product_code 접두사를 가진 데이터를 필터링하고 저장하는 메인 함수.
    """
    # 사용자 입력 또는 기본 설정
    json_file_path = input("원본 JSON 파일 경로를 입력하세요: ") or "data/image_filter.json"
    filtered_json_file_path = input("필터링된 JSON 파일 저장 경로를 입력하세요: ") or "data/filtered_image_filter.json"
    product_code_prefix = input("필터링할 product_code 접두사를 입력하세요: ") or "SNW_"

    try:
        # 필터링 함수 실행
        # filter_json_by_product_code(json_file_path, filtered_json_file_path, product_code_prefix)


        json_output_file_name = make_output_file_path(CONVERT_URL_FILE, "base_file_name", "convert", FILE_EXTENSION_JSON)
        print("json_output_file_name : " + json_output_file_name)
        convert_excel_to_json(FILTERED_URL_FILE, json_output_file_name)



    except Exception as e:
        print(f"[ERROR] 프로그램 실행 중 오류 발생: {e}")

if __name__ == "__main__":
    main()