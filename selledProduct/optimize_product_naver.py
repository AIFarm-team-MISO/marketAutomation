import random
from utils.global_logger import logger

import re
import pandas as pd
import os
from utils.excel.excel_utils import make_input_file_path, make_output_file_path
import config.settings as settings

from config.settings import FILE_EXTENSION_xlsx, CURRENT_MARKET_NAME

from config.settings import FILE_EXTENSION_xlsx, CURRENT_MARKET_NAME
from utils.excel.excel_utils import make_input_file_path, make_output_file_path, read_xls_all_sheets, save_excel_with_sheets,read_and_clean_first_sheet,read_xlsx_all_sheets
from utils.json.json_util import load_config
from imageFilter.excel.excel_handler_xlsx import process_imageFiltering_excel_file_xlsx
from utils.excel.excel_split import split_excel_by_rows
from rotationFile.rotation_task_manager import generate_tasks_from_config, process_first_sheet
from productNaming.name_handler import process_namingChange_excel_file
from rotationFile.rotation_excel_edit_util import clear_column_data, add_prefix_to_column
from rotationFile.rotation_excel_edit_util import update_column_to_9999, adjust_column_by_percentage, swap_image_column
from utils.excel.excel_get_data import get_folder_name, get_market_name
from rotationFile.rotation_market_process import market_process
from utils.excel.excel_utils import get_naver_modified_excel, save_excel_for_godo, set_dual_column_headers, save_excel_modified_naver_xlsx


def filter_words_in_product_name(df, column_name="상품명", remove_words=None):
    """
    특정 열의 문자열에서 지정된 단어들이 포함된 경우 제거하는 함수.

    ✅ 주요 기능:
    1. 특정 단어가 단독으로 존재하는 경우 제거 (예: "한정", "할인")
    2. 특정 단어가 복합 단어 속에 포함된 경우에도 제거 (예: "기간한정데칼" → "기간데칼")
    3. 불필요한 공백을 정리하여 반환

    :param df: 데이터프레임 (DataFrame)
    :param column_name: 필터링할 열 이름 (기본값: "상품명")
    :param remove_words: 제거할 단어 리스트 (기본값: ["한정", "할인"])
    :return: 변경된 데이터프레임
    """
    try:
        if remove_words is None:
            remove_words = ["한정", "할인"]  # 기본 제거 단어 리스트

        # ✅ 특정 열이 존재하는지 확인
        if column_name not in df.columns:
            raise ValueError(f"❌ '{column_name}' 열이 데이터프레임에 존재하지 않습니다.")

        # ✅ 문자열에서 특정 단어를 모두 제거하는 함수
        def clean_product_name(name):
            name = str(name)  # 문자열 변환
            for word in remove_words:
                # 단독으로 존재하는 경우 제거 (공백 또는 문장 경계 기준)
                name = re.sub(rf"\b{word}\b", "", name)
                # 복합 단어 안에서도 제거
                name = name.replace(word, "")
            return re.sub(r"\s+", " ", name).strip()  # 연속된 공백 제거 후 반환

        # ✅ 변경된 값 적용
        df[column_name] = df[column_name].apply(clean_product_name)

        # ✅ 변경 완료 로그 출력
        logger.log(f"✅ '{column_name}' 열 값 필터링 완료.", level="INFO")

        return df

    except Exception as e:
        logger.log(f"❌ '{column_name}' 필터링 중 오류 발생: {e}", level="ERROR")
        raise

def add_prefix_to_seller_code(df, column_name, prefix):
    """
    특정 열의 값 앞에 접두사를 추가하고, 기존 문자열에 '-'가 포함된 경우 '-' 앞쪽 문자열을 제거하는 함수.

    ✅ 주요 기능:
    1. 문자열에 '-'가 포함된 경우, '-' 앞의 내용을 제거한 후 접두사 추가 (예: "ABC-123" → "SP-123")
    2. 해당 열의 모든 값 앞에 접두사 추가 (예: "SP-" + 기존 값)

    :param df: 데이터프레임 (DataFrame)
    :param column_name: 변경할 열 이름 (기본값: "판매자 상품코드")
    :param prefix: 추가할 접두사 (기본값: "SP-")
    :return: 변경된 데이터프레임
    """
    try:
        # ✅ 특정 열이 존재하는지 확인
        if column_name not in df.columns:
            raise ValueError(f"❌ '{column_name}' 열이 데이터프레임에 존재하지 않습니다.")

        # ✅ '-'가 포함된 경우 '-' 앞의 문자열 제거 후 접두사 추가
        def process_code(value):
            value = str(value)  # 문자열 변환
            if '-' in value:
                value = value.split('-', 1)[1]  # 첫 번째 '-' 이후의 문자열만 남김
            return prefix + value  # 접두사 추가

        # ✅ 변경된 값 적용
        df[column_name] = df[column_name].apply(process_code)

        # ✅ 변경 완료 로그 출력
        logger.log(f"✅ '{column_name}' 열 값 변경 완료. ", level="INFO")

        return df

    except Exception as e:
        logger.log(f"❌ '{column_name}' 접두사 추가 중 오류 발생: {e}", level="ERROR")
        raise


from openpyxl.utils import get_column_letter

def get_excel_column_mapping(df):
    """
    DataFrame의 컬럼명을 AZ 형식(A, B, C ...)으로 변환하는 함수.
    
    :param df: DataFrame
    :return: { 'A': '상품명', 'B': '판매가', ... } 형태의 매핑 딕셔너리
    """
    return {get_column_letter(i+1): col for i, col in enumerate(df.columns)}

def get_column_by_excel_letter(df, letter, excel_mapping=None):
    """
    AZ 형식(A, B, C ...)으로 DataFrame 컬럼명을 가져오는 함수.
    
    :param df: DataFrame
    :param letter: 엑셀 컬럼 (예: "C")
    :param excel_mapping: AZ 형식의 컬럼 매핑 (기본값: None → 내부에서 생성)
    :return: DataFrame 컬럼명 (예: "즉시할인 값(기본할인)")
    """
    if excel_mapping is None:
        excel_mapping = get_excel_column_mapping(df)  # 매핑이 없으면 생성
    
    if letter.upper() not in excel_mapping:
        raise ValueError(f"❌ '{letter}'는 데이터프레임에 없는 컬럼입니다.")
    
    return excel_mapping[letter.upper()]

def calculate_margin_price(original_price):
    """
    가격대별 마진율을 적용하여 새로운 판매가를 계산하는 함수.

    ✅ 주요 기능:
    1. 가격대에 따라 마진율을 다르게 적용
    2. 새로운 판매가 계산 (원가 × (1 + 마진율))
    
    :param original_price: 원가 (int)
    :return: 새로운 판매가 (int)
    """
    if original_price < 1:
        return 0  # 유효하지 않은 가격

    if original_price <= 1000:
        margin_rate = 1.5  # 150%
    elif original_price <= 10000:
        margin_rate = 1.1  # 100%
    elif original_price <= 20000:
        margin_rate = 0.75  # 75%
    else:
        margin_rate = 0.5  # 50%

    return round(original_price * (1 + margin_rate))  # 최종 가격 계산

def round_to_nearest_ten(value):
    """
    숫자를 가장 가까운 10단위로 반올림하는 함수.
    
    예:
    - 2154 → 2150
    - 2167 → 2170
    - 8793 → 8790
    """
    return round(value / 10) * 10

def apply_discount(df):
    """
    AZ 형식(A, B, C ...)의 엑셀 컬럼명을 사용하여 각 행마다 랜덤 할인율을 적용하는 함수.
    
    ✅ 주요 기능:
    1. AZ 형식의 열(A, B, C ...)을 실제 데이터프레임 컬럼명으로 변환
    2. "판매가"를 숫자로 변환 후 가격대별 마진율 적용하여 기본 판매가 설정
    3. "할인율(45~49%)"을 각 행마다 랜덤으로 적용하여 "변경된 판매가" 계산
    4. "즉시할인 값(기본할인)"을 계산 (기존 판매가 - 변경된 판매가)
    5. "즉시할인 단위(기본할인)"을 "원"으로 설정
    6. 최종적으로 변경된 데이터를 데이터프레임에 반영
    
    :param df: DataFrame (엑셀 데이터)
    :return: 할인율이 적용된 데이터프레임
    """
    try:
        # ✅ AZ 컬럼 매핑 가져오기
        excel_mapping = get_excel_column_mapping(df)

        # ✅ AZ 형식의 열을 실제 컬럼명으로 변환 (매핑을 재사용)
        price_column = get_column_by_excel_letter(df, "F", excel_mapping)
        discount_value_column = get_column_by_excel_letter(df, "AZ", excel_mapping)
        discount_unit_column = get_column_by_excel_letter(df, "BA", excel_mapping)

        # ✅ "판매가" 열을 숫자로 변환 후 원래 값 저장
        df["_original_price"] = df[price_column].astype(str)  
        numeric_price = pd.to_numeric(df[price_column], errors='coerce').fillna(0)


        # ✅ 가격대별 마진율을 적용한 새로운 기준 가격 계산
        margin_price = numeric_price.apply(calculate_margin_price)


        # ✅ 각 행별 랜덤 할인율 생성 (45% ~ 49% 범위)
        random_discount_rates = [random.randint(45, 49) for _ in range(len(df))]

        # ✅ 새로운 가격 계산 (각 행의 랜덤 할인율 적용) → 할인 공식 수정 (나누기)
        discounted_price = (margin_price / (1 - pd.Series(random_discount_rates) / 100)).round(0).astype(int)


        # ✅ 즉시할인 값 계산 (양수로 변환)
        discount_amount = abs(margin_price - discounted_price).astype(int)

        # ✅ 새로운 가격과 즉시할인 값을 10단위로 반올림하여 마지막 자리 0으로 설정
        discounted_price = discounted_price.apply(round_to_nearest_ten)
        discount_amount = discount_amount.apply(round_to_nearest_ten)

        # ✅ 즉시할인 값 저장
        df[discount_value_column] = discount_amount

        # ✅ 즉시할인 단위는 "원"으로 설정
        df[discount_unit_column] = "원"

        # ✅ 숫자로 변환한 값 → 다시 문자열로 복원
        df[price_column] = discounted_price.astype(str)

        # ✅ 최종 판매가격 = 할인 후 가격 (반올림 적용됨)
        final_price = discounted_price - discount_amount

        # ✅ 임시 컬럼 삭제
        df.drop(columns=["_original_price"], inplace=True, errors='ignore')

        # ✅ 디버깅 로그 추가 (최초 5개 샘플 확인)
        debug_df = pd.DataFrame({
            "원가": numeric_price.head(),
            "마진율 적용 가격": margin_price.head(),
            "적용된 랜덤 할인율": random_discount_rates[:5],  
            "새로운 가격 (반올림)": discounted_price.head(),
            "할인가 (반올림)": discount_amount.head(),
            "최종 판매가격": final_price.head()  
        })

        logger.log(f"🔍 할인 계산 검증 (최초 5개 샘플):\n{debug_df}", level="DEBUG")

        # ✅ 변경 완료 로그 출력
        logger.log(f"✅ '{price_column}', 즉시할인값, 할인율 변경 적용 완료.", level="INFO")

        return df

    except Exception as e:
        logger.log(f"❌ 할인 적용 중 오류 발생: {e}", level="ERROR")
        raise


def update_validity_date(df, validity_column="유효일자", new_date="2034-04-01"):
    """
    데이터프레임의 특정 열(유효일자)을 '2034-04-01'로 변경하는 함수.

    ✅ 주요 기능:
    1. 특정 컬럼명을 사용하여 '유효일자' 컬럼을 찾음
    2. 유효일자 컬럼의 모든 값을 '2034-04-01'로 변경
    3. 변경된 값을 데이터프레임에 적용

    :param df: DataFrame (엑셀 데이터)
    :param validity_column: 유효일자가 들어있는 컬럼명 (기본값: "유효일자")
    :param new_date: 변경할 유효일자 값 (기본값: "2034-04-01")
    :return: 유효일자가 변경된 데이터프레임
    """
    try:
        # ✅ 유효일자 컬럼이 존재하는지 확인 후 변경
        if validity_column in df.columns:
            df[validity_column] = new_date  # 모든 행을 '2034-04-01'로 변경
            logger.log(f"✅ '{validity_column}' 컬럼의 모든 값을 '{new_date}'로 변경 완료.", level="INFO")
        else:
            logger.log(f"⚠️ 유효일자 컬럼('{validity_column}')이 데이터프레임에 존재하지 않습니다.", level="WARNING")

        return df

    except Exception as e:
        logger.log(f"❌ 유효일자 변경 중 오류 발생: {e}", level="ERROR")
        raise

def update_delivery_code(df, delivery_column, new_delivery_code):
    """
    데이터프레임의 특정 열(택배사코드)을 입력된 값으로 변경하는 함수.

    ✅ 주요 기능:
    1. 특정 컬럼명을 사용하여 '택배사코드' 컬럼을 찾음
    2. 해당 컬럼의 모든 값을 사용자가 입력한 '택배사코드' 값으로 변경
    3. 변경된 값을 데이터프레임에 적용

    :param df: DataFrame (엑셀 데이터)
    :param delivery_column: 택배사코드가 들어있는 컬럼명 (기본값: "택배사코드")
    :param new_delivery_code: 변경할 택배사코드 값 (기본값: "CJ대한통운")
    :return: 택배사코드가 변경된 데이터프레임


    대한통운 : CJGLS
    롯데택배 : HYUNDAI
    한진택배 : HANJIN
    우체국택배 : EPOST

    """
    try:
        # ✅ 택배사코드 컬럼이 존재하는지 확인 후 변경
        if delivery_column in df.columns:
            df[delivery_column] = new_delivery_code  # 모든 행을 새로운 택배사코드로 변경
            logger.log(f"✅ '{delivery_column}' 컬럼의 모든 값을 '{new_delivery_code}'로 변경 완료.", level="INFO")
        else:
            logger.log(f"⚠️ 택배사코드 컬럼('{delivery_column}')이 데이터프레임에 존재하지 않습니다.", level="WARNING")

        return df

    except Exception as e:
        logger.log(f"❌ 택배사코드 변경 중 오류 발생: {e}", level="ERROR")
        raise


def update_point_unit(df, new_point=50, point_value_column_letter="BK", point_unit_column_letter="BL", new_point_unit="원"):
    """
    데이터프레임의 특정 열(상품구매시 포인트 지급 값 & 지급 단위, BK & BL 열)을 입력된 값으로 변경하는 함수.

    ✅ 주요 기능:
    1. AZ 형식(A, B, C ...)의 엑셀 컬럼명을 실제 컬럼명으로 변환
    2. 특정 컬럼을 찾아 모든 값을 사용자가 입력한 포인트 지급 값(BK)과 지급 단위(BL)로 변경
    3. 포인트 지급 단위 컬럼(BL)은 기본적으로 '원'으로 설정
    4. 변경된 값을 데이터프레임에 적용

    :param df: DataFrame (엑셀 데이터)
    :param new_point: 변경할 포인트 지급 값 (기본값: 0)
    :param point_value_column_letter: 포인트 지급 값이 들어있는 AZ 형식의 컬럼명 (기본값: "BK")
    :param point_unit_column_letter: 포인트 지급 단위가 들어있는 AZ 형식의 컬럼명 (기본값: "BL")
    :param new_point_unit: 변경할 포인트 지급 단위 값 (기본값: "원")
    :return: 포인트 지급 값 및 단위가 변경된 데이터프레임
    """
    try:
        # ✅ AZ 컬럼 매핑 가져오기
        excel_mapping = get_excel_column_mapping(df)

        # ✅ AZ 형식의 열을 실제 컬럼명으로 변환 (BK & BL 열을 실제 컬럼명으로 변경)
        point_value_column = get_column_by_excel_letter(df, point_value_column_letter, excel_mapping)
        point_unit_column = get_column_by_excel_letter(df, point_unit_column_letter, excel_mapping)

        # ✅ 포인트 지급 값 컬럼(BK)이 존재하는지 확인 후 변경
        if point_value_column in df.columns:
            df[point_value_column] = new_point  # 모든 행을 new_point 값으로 변경
            logger.log(f"✅ '{point_value_column}' 컬럼의 모든 값을 '{new_point}'으로 변경 완료.", level="INFO")
        else:
            logger.log(f"⚠️ 포인트 지급 값 컬럼('{point_value_column}')이 데이터프레임에 존재하지 않습니다.", level="WARNING")

        # ✅ 포인트 지급 단위 컬럼(BL)이 존재하는지 확인 후 변경
        if point_unit_column in df.columns:
            df[point_unit_column] = new_point_unit  # 모든 행을 '원'으로 변경
            logger.log(f"✅ '{point_unit_column}' 컬럼의 모든 값을 '{new_point_unit}'로 변경 완료.", level="INFO")
        else:
            logger.log(f"⚠️ 포인트 지급 단위 컬럼('{point_unit_column}')이 데이터프레임에 존재하지 않습니다.", level="WARNING")

        return df

    except Exception as e:
        logger.log(f"❌ 포인트 지급 값 및 단위 변경 중 오류 발생: {e}", level="ERROR")
        raise




def change_product_excel(first_sheet_data):
    """
    상품 데이터에 여러 가지 필터를 적용하는 함수.

    ✅ 주요 기능:
    1. "판매자 상품코드" 열에 "SP-" 접두사 추가

    (추후 다른 필터 기능 추가 예정)

    :param first_sheet_data: 첫 번째 시트의 데이터프레임
    :return: 변경된 데이터프레임
    """
    remove_words = ["한정", "할인"] 


    try:
        # ✅ "판매자 상품코드" 접두사 추가 함수 호출
        first_sheet_data = add_prefix_to_seller_code(first_sheet_data, "판매자 상품코드", "SP-")

        # ✅ "상품명" 필터링 적용
        first_sheet_data = filter_words_in_product_name(first_sheet_data, "상품명", remove_words)

        # ✅ 할인가격 적용
        first_sheet_data = apply_discount(first_sheet_data)

        # ✅ 유효일자 변경 
        first_sheet_data = update_validity_date(first_sheet_data)

        # ✅ 택배사코드 변경
        first_sheet_data = update_delivery_code(first_sheet_data, "택배사코드", "CJGLS")

        # ✅ 제품구입시 포인트 변경 
        first_sheet_data = update_point_unit(first_sheet_data)


        return first_sheet_data

    except Exception as e:
        logger.log(f"❌ 상품 데이터 변경 중 오류 발생: {e}", level="ERROR")
        raise




def make_optimize_product_excel(file_path, base_file_name):

    # 리포트 파일명 생성
    logger.prepend_report_file_name(base_file_name)

    # 읽을 파일경로 출력 파일 이름 설정
    excel_file_path = make_input_file_path(file_path, base_file_name)
    output_file_path = make_output_file_path(file_path, base_file_name, "_rotatet_output", FILE_EXTENSION_xlsx)
    _, file_extension = os.path.splitext(base_file_name)


    # 모든 시트 읽기(파일확장명에 따라)
    if file_extension.lower() == ".xlsx":
        sheets = read_xlsx_all_sheets(excel_file_path)  # .xlsx 파일 처리
    elif file_extension.lower() == ".xls":
        sheets = read_xls_all_sheets(excel_file_path)  # .xls 파일 처리
    else:
        raise ValueError(f"Unsupported file format: {file_extension}. Only '.xls' and '.xlsx' are supported.")

    # ✅ 1. 첫 번째 행을 보관하면서 첫 번째 시트 데이터 가져오기
    first_sheet_name, first_row_values, first_sheet_data = get_naver_modified_excel(sheets)

    # 마켓별 초기설정
    processed_sheet_data = change_product_excel(first_sheet_data)


    # 📄 **엑셀 파일 저장 (모든 시트 포함)**
    save_excel_modified_naver_xlsx(sheets, output_file_path, first_row_values, processed_sheet_data, first_sheet_name)