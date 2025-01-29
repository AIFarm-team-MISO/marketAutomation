from utils.global_logger import logger

from rotationFile.rotation_excel_edit_util import clear_column_data, add_prefix_to_column
from rotationFile.rotation_excel_edit_util import update_column_to_9999, adjust_column_by_percentage, swap_image_column

def market_process(first_sheet_data, market_platform, market_name, dome_name):

    if market_platform == "네이버":
        if dome_name == "도매토피아":
            logger.log(f"- '{dome_name}' 초기 셋팅시작 -", level="INFO", also_to_report=True, separator="dash-1line")
 
            modify_sellercode = add_prefix_to_column(first_sheet_data, "판매자 관리코드", "GT") # 판매자관리코드 접두사만듬
            modify_count = update_column_to_9999(modify_sellercode, "수량*")                   # 수량변경
            modify_price = adjust_column_by_percentage(modify_count, "판매가*", 10, "인하")      # 판매가변경
            processed_sheet_data = swap_image_column(modify_price, '목록 이미지*', '이미지3')

        else:

            # 네이버는 json에 네이버용 도매토피아 만들어야됨 아마.. [네이버-GT]등으로
            # processed_sheet_data = add_prefix_to_column(first_sheet_data, "판매자 관리코드", channel_name)
            processed_sheet_data = first_sheet_data  # 원본 데이터 그대로 사용


    elif market_platform == "11번가":
        if dome_name == "도매토피아":
            modify_sellercode = add_prefix_to_column(first_sheet_data, "판매자 관리코드", "GT")
            modify_count = update_column_to_9999(modify_sellercode, "수량*") #수량변경
            modify_price = adjust_column_by_percentage(modify_count, "판매가*", 5, "인하") #판매가변경
            processed_sheet_data = swap_image_column(modify_price, '목록 이미지*', '이미지2')

    elif market_platform == "쿠팡":
        # 브랜드명을 모두지움
        processed_sheet_data = clear_column_data(first_sheet_data, "브랜드")
        
    else:
        processed_sheet_data = first_sheet_data  # 원본 데이터 그대로 사용


    return processed_sheet_data