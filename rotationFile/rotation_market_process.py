from utils.global_logger import logger

from rotationFile.rotation_excel_edit_util import clear_column_data, add_prefix_to_column, remove_adult_category_rows, convert_http_to_https, convert_column_str,filter_product_name, filter_product_code, filter_forbid_product
from rotationFile.rotation_excel_edit_util import update_column_to_9999, adjust_column_by_percentage, swap_image_column, clear_image_columns, replace_base_url, shuffle_keywords_in_column, fill_column_with_value,sort_and_limit_rows_by_column, fill_columns_allwaysonly
from config.settings import FILTER_KEYWORDS, FILTER_UNIT_KEYWORDS, FILTER_PRODUCT_CODE, FILTER_11_KEYWORDS, FILTER_11_PRODUCT_CODE, FILTER_BLAND_KEYWORDS
from rotationFile.rotation_excel_edit_util import remove_empty_rows,remove_food_category_rows, remove_duplicate_rows
from rotationFile.rotation_excel_edit_util import remove_options_rows, clean_search_keywords, update_column_value, update_column_brand

columns_to_update = ["목록 이미지*", "이미지1(대표/기본이미지)*", "이미지2", "이미지3", "이미지4", "이미지5"]

def market_process(first_sheet_data, market_platform, market_name, dome_name):
    logger.log(f"- '{market_platform},  {market_name}, {dome_name}' 초기 셋팅시작 -", level="INFO", also_to_report=True, separator="none")

    # 금지 상품 제거
    forbid_df, keyword_removed_count  = filter_product_name(first_sheet_data, "상품명*", FILTER_KEYWORDS + FILTER_UNIT_KEYWORDS + FILTER_BLAND_KEYWORDS)

    # 금지 상품 코드 제거
    forbid_df_code, product_removed_count = filter_product_code(forbid_df, "판매자 관리코드", FILTER_PRODUCT_CODE)

    # 19금 카테고리 제거
    fitered_df, removed_count  = remove_adult_category_rows(forbid_df_code, "카테고리 번호*")

    if market_platform == "네이버":
        if market_name == "파타르시스" and dome_name == "3MRO":
            # 3엠 우선판매의 경우 인증정보을 모두지움
            forbid_df_code = clear_column_data(fitered_df, "인증정보")


        if dome_name == "도매토피아":

            change_url_df, modified_count = replace_base_url(fitered_df, columns_to_update, "https://callenge2000.shopon.biz/data/goods_img", "https://dmtusr.vipweb.kr")

            
            if market_name == "메인":
                modify_sellercode = add_prefix_to_column(change_url_df, "판매자 관리코드", "GT") # 판매자관리코드 접두사만듬
            elif market_name == "메인XT":
                modify_sellercode = add_prefix_to_column(change_url_df, "판매자 관리코드", "XT") # 판매자관리코드 접두사만듬
            elif market_name == "파타르시스":
                modify_sellercode = add_prefix_to_column(change_url_df, "판매자 관리코드", "GK") # 판매자관리코드 접두사만듬
            elif market_name == "네스쳐GT":
                modify_sellercode = add_prefix_to_column(change_url_df, "판매자 관리코드", "GT") # 판매자관리코드 접두사만듬
            elif market_name == "네스쳐GK":
                modify_sellercode = add_prefix_to_column(change_url_df, "판매자 관리코드", "GK") # 판매자관리코드 접두사만듬

            if market_name == "네스쳐GT" or market_name == "네스쳐GK" :
                modify_count = update_column_to_9999(modify_sellercode, "수량*")                   # 수량변경
                modify_price = adjust_column_by_percentage(modify_count, "판매가*", 5, "인하")      # 판매가변경
                processed_sheet_data = swap_image_column(modify_price, '목록 이미지*', '이미지5')
                processed_sheet_data = shuffle_keywords_in_column(processed_sheet_data, '상품명*')
                processed_sheet_data = update_column_brand(processed_sheet_data, '브랜드', '(주)트리') # 브랜드입력
                
            # else:
            #     modify_count = update_column_to_9999(modify_sellercode, "수량*")                   # 수량변경
            #     modify_price = adjust_column_by_percentage(modify_count, "판매가*", 5, "인하")      # 판매가변경
            #     processed_sheet_data = swap_image_column(modify_price, '목록 이미지*', '이미지2')
            #     processed_sheet_data = shuffle_keywords_in_column(processed_sheet_data, '상품명*')
            #     processed_sheet_data = update_column_brand(processed_sheet_data, '브랜드', '(주)트리')# 브랜드입력




        else:

            # 네이버는 json에 네이버용 도매토피아 만들어야됨 아마.. [네이버-GT]등으로
            # processed_sheet_data = add_prefix_to_column(first_sheet_data, "판매자 관리코드", channel_name)
            processed_sheet_data = fitered_df  # 원본 데이터 그대로 사용

    elif market_platform == "11번가":
        forbid_11_df, removed_counts  = filter_forbid_product(fitered_df, "상품명*", "판매자 관리코드", FILTER_11_KEYWORDS, FILTER_11_PRODUCT_CODE)

        if dome_name == "도매토피아":
            
            change_url_df, modified_count = replace_base_url(forbid_11_df, columns_to_update, "https://callenge2000.shopon.biz/data/goods_img", "https://dmtusr.vipweb.kr")


            if market_name == "2002":
                modify_sellercode = add_prefix_to_column(change_url_df, "판매자 관리코드", "GK")
            elif market_name == "2003":
                modify_sellercode = add_prefix_to_column(change_url_df, "판매자 관리코드", "GT") # 판매자관리코드 접두사만듬
            elif market_name == "2025":
                modify_sellercode = add_prefix_to_column(change_url_df, "판매자 관리코드", "GT") # 판매자관리코드 접두사만듬
            elif market_name == "2026":
                modify_sellercode = add_prefix_to_column(change_url_df, "판매자 관리코드", "GT") # 판매자관리코드 접두사만듬
            else:
                modify_sellercode = change_url_df

            modify_count = update_column_to_9999(modify_sellercode, "수량*") #수량변경
            modify_price = adjust_column_by_percentage(modify_count, "판매가*", 1, "인하") #판매가변경
            processed_sheet_data = swap_image_column(modify_price, '목록 이미지*', '이미지2')

        elif dome_name == "친구도매":

            # http 를 https 로 변경 
            updated_df, modified_count = convert_http_to_https(forbid_11_df, columns_to_update)
            processed_sheet_data = updated_df

        else:
            processed_sheet_data = forbid_11_df

    elif market_platform == "쿠팡":
        # 브랜드명을 모두지움
        processed_sheet_data = clear_column_data(fitered_df, "브랜드")

    elif market_platform == "옥지옥션" or market_platform == "옥지G마켓" :
        # 옥지옥션 : 제품수 1500개로 설정 
        fitered_df = sort_and_limit_rows_by_column(fitered_df)


        # [옥지옥션-23]_비투비온_GPT_20+20%
        if dome_name == "비투비온":
            columns_to_clear = ["이미지2", "이미지3", "이미지4", "이미지5"]
            processed_sheet_data, modified_count = clear_image_columns(fitered_df, columns_to_clear)
        else:
            processed_sheet_data = fitered_df
    

    elif market_platform == "톡스토어":

        # 원산지 변경 (신우만 국산)
        if dome_name == "신우":
            new_str = "국산"
        else:
            new_str = "기타/중국"

        convert_str_data, modified_rows = convert_column_str(fitered_df, "원산지*", new_str)



        if dome_name == "도매토피아":

            change_url_df, modified_count = replace_base_url(convert_str_data, columns_to_update, "https://callenge2000.shopon.biz/data/goods_img", "https://dmtusr.vipweb.kr")

            modify_sellercode = add_prefix_to_column(change_url_df, "판매자 관리코드", "GT") # 판매자관리코드 접두사만듬
            modify_count = update_column_to_9999(modify_sellercode, "수량*")                   # 수량변경
            modify_price = adjust_column_by_percentage(modify_count, "판매가*", 5, "인하")      # 판매가변경
            processed_sheet_data = swap_image_column(modify_price, '목록 이미지*', '이미지2')





        processed_sheet_data = convert_str_data 
    
    elif market_platform == "롯데온":
        # 브랜드명을 모두지움
        processed_sheet_data = clear_column_data(fitered_df, "브랜드")
        # 원산지를 '기타' 로 통일
        processed_sheet_data = fill_column_with_value(processed_sheet_data, "원산지*")

     
    elif market_platform == "고도몰": # [고도몰-블루채널]_도매토피아_GT_GPT
        
        if dome_name == "도매토피아":
            
            change_url_df, modified_count = replace_base_url(fitered_df, columns_to_update, "https://callenge2000.shopon.biz/data/goods_img", "https://dmtusr.vipweb.kr")
            modify_sellercode = add_prefix_to_column(change_url_df, "판매자 관리코드", "GT") # 판매자관리코드 접두사만듬
            modify_count = update_column_to_9999(modify_sellercode, "수량*")                   # 수량변경
            modify_price = adjust_column_by_percentage(modify_count, "판매가*", 5, "인하")      # 판매가변경
            processed_sheet_data = swap_image_column(modify_price, '목록 이미지*', '이미지2')

        else:
            processed_sheet_data = fitered_df  # 원본 데이터 그대로 사용

    
    # 올웨이즈 설정 변경시 
    elif market_platform == "올웨이즈":

        if dome_name == "도매토피아":

            change_url_df, modified_count = replace_base_url(fitered_df, columns_to_update, "https://callenge2000.shopon.biz/data/goods_img", "https://dmtusr.vipweb.kr")

            modify_sellercode = add_prefix_to_column(change_url_df, "판매자 관리코드", "GT") # 판매자관리코드 접두사만듬
            modify_count = update_column_to_9999(modify_sellercode, "수량*")                   # 수량변경
            modify_price = adjust_column_by_percentage(modify_count, "판매가*", 5, "인하")      # 판매가변경
            processed_sheet_data = swap_image_column(modify_price, '목록 이미지*', '이미지2')

        else:
            processed_sheet_data = fitered_df  # 원본 데이터 그대로 사용

    
        # 수량변경
        processed_sheet_data = fill_columns_allwaysonly(fitered_df, "선택사항 타입")     



    else:
        processed_sheet_data = fitered_df  # 원본 데이터 그대로 사용

    return processed_sheet_data


# 🟢 market_config: 플랫폼, 마켓, 도매사별 설정 매핑

godo_market_config = {
    ("고도몰", "파타르시스", "파라브러"): {
        "option_remove" : True
    },
    ("고도몰", "파타르시스", "필우"): {
        "option_remove" : True
    }
    ,
    ("고도몰", "파타르시스", "셀프"): {
        "option_remove" : True
    }
    ,
    ("고도몰", "파타르시스", "비온"): {
        "option_remove" : True
    }
    ,
    ("고도몰", "파타르시스", "젠트"): {
        "option_remove" : True
    }
    ,
    ("고도몰", "파타르시스", "3MR-생건"): {
        "option_remove" : True
    }
   

    
    ,
    ("고도몰", "블루채널", "파라브러"): {
        "option_remove" : True
    }
    ,
    ("고도몰", "블루채널", "더드림"): {
        "option_remove" : True
    }
    ,
    ("고도몰", "블루채널", "글로벌"): {
        "option_remove" : True
    }
    ,
    ("고도몰", "블루채널", "젠트"): {
        "option_remove" : True
    }
    ,
    ("고도몰", "블루채널", "비온"): {
        "option_remove" : True
    },
    ("고도몰", "블루채널", "친구"): {
        "option_remove" : True
    }
    ,
    ("고도몰", "블루채널", "도매토피아-GT"): {
        "prefix": "GT",
        "quantity": 9999,
        "price_adjust": {"column": "판매가*", "percentage": 15, "mode": "인하"},
        "swap_images": ("목록 이미지*", "이미지2")
    }
}

def godo_market_process(first_sheet_data, market_platform, market_name, dome_name):
    logger.log(f"- '{market_platform}, {dome_name}' 초기 셋팅 시작 -", level="INFO", also_to_report=True, separator="none")

    # 1️⃣ ** 사전 필터링**

    # 상품명 금지 키워드 필터링
    forbid_df_name, keyword_removed_count = filter_product_name(first_sheet_data, "상품명_기본", FILTER_KEYWORDS + FILTER_UNIT_KEYWORDS)
    # 상품코드 필터링
    forbid_df_code, product_removed_count = filter_product_code(forbid_df_name, "자체상품코드", FILTER_PRODUCT_CODE)
    # 빈 상품명 필터링
    empty_df_code, empty_removed_count = remove_empty_rows(forbid_df_code, "상품명_기본")
    # 중복 상품명 필터링
    duplicate_df_code, duplicate_removed_count = remove_duplicate_rows(empty_df_code, "상품명_기본")



    # 2️⃣ **설정 불러오기**
    config_key = (market_platform, market_name, dome_name)
    config = godo_market_config.get(config_key)

    if not config:
        logger.log(f"⚠️ '{config_key}'에 대한 설정이 없습니다. 기본 데이터 반환.", level="WARNING")
        return duplicate_df_code

    # 3️⃣ **설정에 따른 작업 수행**
    processed_df = duplicate_df_code.copy()

    # 👉 **옵션 사용 여부가 Y인 행 제거**
    if config.get("option_remove", False):
        initial_count = len(processed_df)
        processed_df = processed_df[processed_df["옵션 사용 여부"] != "y"]
        removed_count = initial_count - len(processed_df)
        logger.log(f"🚫 옵션 사용 여부 'Y'인 행 {removed_count}개 제거 완료.", level="INFO", also_to_report=True, separator="none")


    # 🟢 **최종 처리 완료**
    logger.log(f"✅ '{market_platform}-{market_name}-{dome_name}' 설정 적용 완료!", level="SUCCESS", also_to_report=True, separator="none")
    return processed_df
