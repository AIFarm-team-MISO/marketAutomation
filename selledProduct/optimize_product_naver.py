import random
from utils.global_logger import logger

import re
import pandas as pd
import os
from utils.excel.excel_utils import make_input_file_path, make_output_file_path
import config.settings as settings
from datetime import datetime

from config.settings import FILE_EXTENSION_xlsx, CURRENT_MARKET_NAME
from config.settings import AS_TEMPLETE_PHONE, AS_TEMPLETE_BASIC, AS_TEMPLETE_ETC

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
from utils.shortclip.make_to_shotclip import make_shorts



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

def add_prefix_to_seller_code(df, column_name, prefix, skip_prefixes=None):
    """
    접두사를 붙이되, 특정 접두사들(SP-, SPG-, SR- 등)이 이미 있는 경우는 제외.
    
    :param df: pandas.DataFrame
    :param column_name: 접두사를 붙일 열 이름
    :param prefix: 새로 붙일 접두사 (예: 'SP-')
    :param skip_prefixes: 제외할 접두사 리스트 (예: ['SP-', 'SPG-', 'SR-'])
    :return: 접두사가 적용된 데이터프레임
    """
    try:
        if skip_prefixes is None:
            skip_prefixes = ['SP-', 'SPG-', 'SR-', 'SPSP-']

        if column_name not in df.columns:
            raise ValueError(f"❌ '{column_name}' 열이 존재하지 않습니다.")

        def add_if_not_prefixed(value):
            value_str = str(value).strip()
            for skip in skip_prefixes:
                if value_str.startswith(skip):
                    return value_str
            return prefix + value_str

        df[column_name] = df[column_name].apply(add_if_not_prefixed)

        logger.log(f"✅ '{column_name}' 열에 접두사 '{prefix}' 조건부 추가 완료 (기존 접두사는 제외됨)", level="INFO")
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


def update_validity_date(df, validity_column, new_date):
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


def update_mapping_colums(df):
    """
    데이터프레임의 포인트 관련 컬럼(BK, BL, BM, BN)을 설정하는 함수.
    
    ✅ 주요 기능:
    1. 포인트 지급 값(BK) 및 지급 단위(BL)를 고정값으로 설정
    2. 판매가(F열)를 기준으로 텍스트 포인트(BM), 동영상 포인트(BN)를 구간별로 자동 설정
    3. AZ 컬럼명을 실제 컬럼명으로 변환하여 일괄 처리
    4. 변경된 값을 데이터프레임에 반영하고 로그로 결과 확인
    
    구간별 포인트 지급 로직:
    - 1 ~ 1,000원 : 텍스트포인트 50 / 동영상포인트 100
    - 1,000 ~ 10,000원 : 텍스트포인트 100 / 동영상포인트 200
    - 10,000원 이상 : 텍스트포인트 150 / 동영상포인트 300

    :param df: DataFrame (엑셀 데이터)
    :return: 포인트 관련 컬럼이 변경된 데이터프레임
    """

    # ✅ 내부 변수 설정
    new_point = 50                    # 구매시 포인트 지급 값

    point_value_column_letter = "BK"  # 포인트 지급 값이 들어있는 열 (BK)
    point_unit_column_letter = "BL"   # 포인트 지급 단위가 들어있는 열 (BL)

    text_point_column_letter = "BM"   # 텍스트 포인트 지급 열
    video_point_column_letter = "BN"   # 동영상 포인트 지급 열

    price_column_letter = "F"         # 판매가가 들어있는 열 (F)
    default_point_unit = "원"          # 기본 포인트 단위는 "원"

    month_text_point_column_letter = "BO"   # 한달 텍스트리뷰
    month_video_point_column_letter = "BP"  # 한달 동영상리뷰
    member_point_column_letter = "BQ"       # 알림동의 회원 리뷰

    muiza_column_letter = "BR"         # 무이자할부 열
    freething_column_letter = "BS"     # 사은품 열

    as_templet1_column_letter = "AW"     # A/S 템플릿 열
    as_templet2_column_letter = "AX"     # A/S 템플릿 열
    as_templet3_column_letter = "AY"     # A/S 템플릿 열

    try:
        # ✅ AZ 컬럼 매핑 가져오기
        excel_mapping = get_excel_column_mapping(df)

        # ✅ 열을 실제 컬럼명으로 변환 (BK & BL 열을 실제 컬럼명으로 변경)
        point_value_column = get_column_by_excel_letter(df, point_value_column_letter, excel_mapping)
        point_unit_column = get_column_by_excel_letter(df, point_unit_column_letter, excel_mapping)

        text_point_column = get_column_by_excel_letter(df, text_point_column_letter, excel_mapping)
        video_point_column = get_column_by_excel_letter(df, video_point_column_letter, excel_mapping)
        price_column = get_column_by_excel_letter(df, price_column_letter, excel_mapping)

        month_text_point_column = get_column_by_excel_letter(df, month_text_point_column_letter, excel_mapping)
        month_video_point_column = get_column_by_excel_letter(df, month_video_point_column_letter, excel_mapping)
        member_point_column = get_column_by_excel_letter(df, member_point_column_letter, excel_mapping)

        muiza_column = get_column_by_excel_letter(df, muiza_column_letter, excel_mapping)
        freething_column = get_column_by_excel_letter(df, freething_column_letter, excel_mapping)

        as_templet1_column = get_column_by_excel_letter(df, as_templet1_column_letter, excel_mapping)
        as_templet2_column = get_column_by_excel_letter(df, as_templet2_column_letter, excel_mapping)
        as_templet3_column = get_column_by_excel_letter(df, as_templet3_column_letter, excel_mapping)
        

        # ✅ 구매시 포인트 값 설정
        if point_value_column in df.columns:
            df[point_value_column] = new_point  # 모든 행을 new_point 값으로 변경
            logger.log(f"✅ '{point_value_column}' 컬럼의 모든 값을 '{new_point}'으로 변경 완료.", level="INFO")
        else:
            logger.log(f"⚠️ 포인트 지급 값 컬럼('{point_value_column}')이 데이터프레임에 존재하지 않습니다.", level="WARNING")

        # ✅ 포인트 지급 단위 설정
        if point_unit_column in df.columns:
            df[point_unit_column] = default_point_unit  # 모든 행을 '원'으로 변경
            logger.log(f"✅ '{point_unit_column}' 컬럼의 모든 값을 '{default_point_unit}'로 변경 완료.", level="INFO")
        else:
            logger.log(f"⚠️ 포인트 지급 단위 컬럼('{point_unit_column}')이 데이터프레임에 존재하지 않습니다.", level="WARNING")


        # ✅ 판매가 기준으로 BM & BN 값 설정
        if price_column in df.columns:
            numeric_price = pd.to_numeric(df[price_column], errors='coerce').fillna(0)
            
            # 가격 구간별 로직
            df[text_point_column] = numeric_price.apply(
                lambda x: 50 if x <= 1000 else (100 if x <= 10000 else 150)
            )
            df[video_point_column] = numeric_price.apply(
                lambda x: 100 if x <= 1000 else (200 if x <= 10000 else 300)
            )


        # ✅ BO, BP, BQ 컬럼 각각 10, 20, 50으로 설정
        df[month_text_point_column] = 10
        df[month_video_point_column] = 20
        df[member_point_column] = 50

        logger.log(f"✅ '{month_video_point_column}', '{month_video_point_column}', '{member_point_column}' 컬럼에 각각 10, 20, 50 설정 완료.", level="INFO")

        # ✅ a/s 템플릿번호 셋팅
        df[as_templet1_column] = AS_TEMPLETE_PHONE
        df[as_templet2_column] = AS_TEMPLETE_BASIC
        df[as_templet3_column] = AS_TEMPLETE_ETC

        logger.log(f"✅ a/s 템플릿번호 셋팅 완료", level="INFO")

        # ✅ as 템플릿 설정
        df[muiza_column] = 3
        df[freething_column] = "구매시 포인트 지급"

        # ✅ 결과 로그 출력
        debug_df = pd.DataFrame({
            "판매가": numeric_price.head(),
            f"{text_point_column}": df[text_point_column].head(),
            f"{video_point_column}": df[video_point_column].head(),
            f"{month_text_point_column}": df[month_text_point_column].head(),
            f"{month_video_point_column}": df[month_video_point_column].head(),
            f"{member_point_column}": df[member_point_column].head(),
            f"{muiza_column}": df[muiza_column].head(),
            f"{freething_column}": df[freething_column].head()
        })

        logger.log(f"🔍 판매가 기준 포인트 설정 검증 (최초 5개 샘플):\n{debug_df}", level="DEBUG")
        logger.log(f"✅ 리뷰 포인트, 무이자할부, 사은품, a/s템플릿 셋팅 완료.", level="INFO")





        return df


    except Exception as e:
        logger.log(f"❌ 포인트 지급 값 및 단위 변경 중 오류 발생: {e}", level="ERROR")
        raise

import os
import requests
from urllib.parse import urlparse
from utils.global_logger import logger

import os
import pandas as pd
import requests
from urllib.parse import urlparse
from utils.global_logger import logger

import os
import pandas as pd
import requests
from urllib.parse import urlparse
from utils.global_logger import logger

import os
import pandas as pd
import requests
from urllib.parse import urlparse
from utils.global_logger import logger

def download_images_per_product(df, output_file_path, subfolder_name,
                                 seller_code_column="판매자 상품코드",
                                 thumbnail_column="대표이미지", additional_column="추가이미지"):
    """
    각 상품별 폴더를 생성하고 대표이미지('썸네일') 저장.
    추가이미지는 초기 엑셀에 존재한 것만 추가이미지1~N으로 저장.
    엑셀에는 [추가이미지 + 썸네일] 블록을 반복하여 총 9개로 구성된 추가이미지 URL 문자열을 작성.
    """
    try:
        base_dir = os.path.dirname(output_file_path)
        main_image_dir = os.path.join(base_dir, subfolder_name)
        os.makedirs(main_image_dir, exist_ok=True)
        logger.log(f"📂 이미지 저장 폴더 확인 또는 생성 완료: {main_image_dir}", level="INFO")

        for idx, row in df.iterrows():
            seller_code = str(row.get(seller_code_column, f"no_code_{idx}")).strip()
            if not seller_code:
                continue

            product_dir = os.path.join(main_image_dir, seller_code)
            os.makedirs(product_dir, exist_ok=True)

            # ✅ 대표이미지
            thumb_url = str(row.get(thumbnail_column, "")).strip()
            if not thumb_url or pd.isna(thumb_url) or thumb_url.lower() == "nan":
                logger.log(f"⚠️ '{seller_code}' 대표이미지 없음 → 스킵", level="WARNING")
                continue

            # 썸네일 저장
            thumb_path = download_single_image(thumb_url, product_dir, "썸네일")
            if thumb_path:
                logger.log(f"🖼 '{seller_code}' 썸네일 저장 완료", level="DEBUG")

            # ✅ 추가이미지 원본 URL 필터링
            raw_additional_value = row.get(additional_column, "")
            if pd.isna(raw_additional_value):
                original_add_urls = []
            else:
                original_add_urls = [url.strip() for url in str(raw_additional_value).splitlines()
                                     if isinstance(url, str) and url.strip() and url.strip().lower() != "nan"]

            # ✅ 실제 다운로드는 원래의 추가이미지 URL만
            for i, url in enumerate(original_add_urls):
                saved_path = download_single_image(url, product_dir, f"추가이미지{i+1}")
                if saved_path:
                    logger.log(f"📎 '{seller_code}' 추가이미지{i+1} 저장 완료", level="DEBUG")


            # logger.log(f"저장폴더 : {product_dir} ", level="DEBUG")
    

            # ✅ 숏클립 생성 
            make_shorts(
                image_folder=product_dir,
                output_filename=f"{seller_code}.mp4",
                duration=0.8,
                total_duration=6,
                width=1080,
                height=1920,
                bgm_volume=0.8
            )
            
            

            # ✅ 엑셀용 추가이미지 열 구성: [추가이미지 + 썸네일] 블록 반복 → 9개
            if original_add_urls:
                unit = original_add_urls + [thumb_url]
                repeated_urls = []
                while len(repeated_urls) < 9:
                    repeated_urls.extend(unit)
                full_add_urls = repeated_urls[:9]
            else:
                full_add_urls = [thumb_url] * 9  # 추가이미지 없을 경우 대표이미지 9개

            df.at[idx, additional_column] = '\n'.join(full_add_urls)

        logger.log("✅ 전체 이미지 저장 및 추가이미지 열 업데이트 완료", level="INFO")
        return df

    except Exception as e:
        logger.log(f"❌ 상품 이미지 다운로드 중 오류 발생: {e}", level="ERROR")
        raise



def download_single_image(url, save_dir, base_filename):
    """
    단일 이미지 다운로드 함수 (확장자 포함 저장)

    :param url: 이미지 URL
    :param save_dir: 저장할 디렉토리
    :param base_filename: 저장 파일명 (예: 썸네일)
    :return: 저장된 파일 경로 or None
    """
    try:
        ext = os.path.splitext(urlparse(url).path)[1]
        if ext.lower() not in [".jpg", ".jpeg", ".png", ".gif", ".bmp"]:
            ext = ".jpg"

        save_path = os.path.join(save_dir, base_filename + ext)

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        with open(save_path, "wb") as f:
            f.write(response.content)

        return save_path

    except Exception as e:
        logger.log(f"⚠️ 이미지 다운로드 실패 ({url}): {e}", level="WARNING")
        return None



def update_additional_images_column(df, thumbnail_column="대표이미지", additional_column="추가이미지", max_count=9):
    """
    대표이미지를 마지막에 추가하고, 총 9개의 추가이미지가 되도록 채움.
    
    :param df: 상품 DataFrame
    :param thumbnail_column: 대표이미지 열 이름
    :param additional_column: 추가이미지 열 이름
    :param max_count: 최대 이미지 개수 (기본 9개)
    :return: 수정된 df 반환
    """
    try:
        for idx, row in df.iterrows():
            # 1. 추가이미지 분리
            add_urls = [url.strip() for url in str(row.get(additional_column, "")).splitlines() if url.strip()]
            thumb_url = str(row.get(thumbnail_column, "")).strip()

            # 2. 추가이미지 + 대표이미지(마지막) 조합
            combined_urls = add_urls + ([thumb_url] if thumb_url else [])

            # 3. 반복해서 9개까지 채우기
            if combined_urls:
                repeated_urls = (combined_urls * ((max_count + len(combined_urls) - 1) // len(combined_urls)))[:max_count]
                df.at[idx, additional_column] = '\n'.join(repeated_urls)

        logger.log(f"✅ '추가이미지' 열에 대표이미지 포함하여 9개로 채우기 완료 (대표는 마지막에)", level="INFO")
        return df

    except Exception as e:
        logger.log(f"❌ 추가이미지 채우기 중 오류 발생: {e}", level="ERROR")
        raise



def change_product_excel(first_sheet_data, output_file_path):
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
        # first_sheet_data = apply_discount(first_sheet_data)

        # ✅ 제조일자 변경 
        today_str = datetime.today().strftime("%Y-%m-%d")
        first_sheet_data = update_validity_date(first_sheet_data, '제조일자', today_str)

        # ✅ 유효일자 변경 
        first_sheet_data = update_validity_date(first_sheet_data, "유효일자", "2034-04-01")

        # ✅ 택배사코드 변경
        first_sheet_data = update_delivery_code(first_sheet_data, "택배사코드", "CJGLS")

        # ✅ 리뷰 포인트, 무이자할부, 사은품, a/s템플릿 셋팅 
        first_sheet_data = update_mapping_colums(first_sheet_data)

        # ✅ 구현예정 : 파자마채널 모델템플릿 설정하자 

        # ✅ 대표이미지, 추가이미지 저장
        # subfolder_name="원스톱리빙/젠트" , 오늘담음/파라브러, 파자마채널/기본, 파타르시스/젠트
        download_images_per_product(
            df=first_sheet_data,
            output_file_path=output_file_path,
            subfolder_name="원스톱리빙/더드림"
        )

        

        # ✅ 추가이미지 9개로 추가저장
        first_sheet_data = update_additional_images_column(first_sheet_data, thumbnail_column="대표이미지", additional_column="추가이미지")

        

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
    processed_sheet_data = change_product_excel(first_sheet_data, output_file_path)


    # 📄 **엑셀 파일 저장 (모든 시트 포함)**
    save_excel_modified_naver_xlsx(sheets, output_file_path, first_row_values, processed_sheet_data, first_sheet_name)