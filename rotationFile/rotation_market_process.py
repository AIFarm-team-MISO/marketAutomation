from utils.global_logger import logger

from rotationFile.rotation_excel_edit_util import clear_column_data, add_prefix_to_column, remove_adult_category_rows, convert_http_to_https, convert_column_str
from rotationFile.rotation_excel_edit_util import update_column_to_9999, adjust_column_by_percentage, swap_image_column, clear_image_columns, replace_base_url

columns_to_update = ["목록 이미지*", "이미지1(대표/기본이미지)*", "이미지2", "이미지3", "이미지4", "이미지5"]

def market_process(first_sheet_data, market_platform, market_name, dome_name):
    logger.log(f"- '{market_platform}, {dome_name}' 초기 셋팅시작 -", level="INFO", also_to_report=True, separator="none")

    if market_platform == "네이버":
        if dome_name == "도매토피아":

            change_url_df, modified_count = replace_base_url(first_sheet_data, columns_to_update, "https://callenge2000.shopon.biz/data/goods_img", "https://dmtusr.vipweb.kr")

            if market_name == "메인":

                modify_sellercode = add_prefix_to_column(change_url_df, "판매자 관리코드", "GT") # 판매자관리코드 접두사만듬
            elif market_name == "파타르시스":
                modify_sellercode = add_prefix_to_column(change_url_df, "판매자 관리코드", "GK") # 판매자관리코드 접두사만듬

            modify_count = update_column_to_9999(modify_sellercode, "수량*")                   # 수량변경
            modify_price = adjust_column_by_percentage(modify_count, "판매가*", 15, "인하")      # 판매가변경
            processed_sheet_data = swap_image_column(modify_price, '목록 이미지*', '이미지2')

        else:

            # 네이버는 json에 네이버용 도매토피아 만들어야됨 아마.. [네이버-GT]등으로
            # processed_sheet_data = add_prefix_to_column(first_sheet_data, "판매자 관리코드", channel_name)
            processed_sheet_data = first_sheet_data  # 원본 데이터 그대로 사용

    elif market_platform == "11번가":

        # 19금 카테고리 제거
        delete_row_df, removed_count  = remove_adult_category_rows(first_sheet_data, "카테고리 번호*")

        if dome_name == "도매토피아":
            
            change_url_df, modified_count = replace_base_url(delete_row_df, columns_to_update, "https://callenge2000.shopon.biz/data/goods_img", "https://dmtusr.vipweb.kr")


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
            updated_df, modified_count = convert_http_to_https(delete_row_df, columns_to_update)
            processed_sheet_data = updated_df

        else:
            processed_sheet_data = delete_row_df

    elif market_platform == "쿠팡":
        # 브랜드명을 모두지움
        processed_sheet_data = clear_column_data(first_sheet_data, "브랜드")

    elif market_platform == "옥지옥션":
        # [옥지옥션-23]_비투비온_GPT_20+20%
        if dome_name == "비투비온":
            columns_to_clear = ["이미지2", "이미지3", "이미지4", "이미지5"]
            processed_sheet_data, modified_count = clear_image_columns(first_sheet_data, columns_to_clear)
    

    elif market_platform == "톡스토어":

        # 원산지 변경 (신우만 국산)
        if dome_name == "신우":
            new_str = "국산"
        else:
            new_str = "기타/중국"

        convert_str_data, modified_rows = convert_column_str(first_sheet_data, "원산지*", new_str)

        processed_sheet_data = convert_str_data 
    
    elif market_platform == "롯데온":
        # 브랜드명을 모두지움
        processed_sheet_data = clear_column_data(first_sheet_data, "브랜드")

     
    elif market_platform == "고도몰": # [고도몰-블루채널]_도매토피아_GT_GPT
        
        if dome_name == "도매토피아":
            
            change_url_df, modified_count = replace_base_url(first_sheet_data, columns_to_update, "https://callenge2000.shopon.biz/data/goods_img", "https://dmtusr.vipweb.kr")
            modify_sellercode = add_prefix_to_column(change_url_df, "판매자 관리코드", "GT") # 판매자관리코드 접두사만듬
            modify_count = update_column_to_9999(modify_sellercode, "수량*")                   # 수량변경
            modify_price = adjust_column_by_percentage(modify_count, "판매가*", 5, "인하")      # 판매가변경
            processed_sheet_data = swap_image_column(modify_price, '목록 이미지*', '이미지2')

        else:
            processed_sheet_data = first_sheet_data  # 원본 데이터 그대로 사용
        

    else:
        processed_sheet_data = first_sheet_data  # 원본 데이터 그대로 사용


   


    return processed_sheet_data