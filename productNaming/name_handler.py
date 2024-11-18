import os
import pandas as pd
from imageFilter.excel.file_handler import read_excel_file, save_excel_file
from config.settings import FILE_EXTENSION_xls
from imageFilter.excel.excel_utils import apply_filter_and_sort_xls, insert_column_before, column_letter_to_index, apply_row_color_by_condition, update_seller_codes
from imageFilter.excel.url_filter import save_filtered_urls
from keywordOptimization.naver_api import generate_optimized_names
from keywordOptimization.product_info import ProductInfo, ProcessedProductInfo
from keywordOptimization.keyword_filter_never import apply_filters, process_duplicates_with_variation

from keywordDictionary.dictionary_loader import load_dictionary
from keywordDictionary.keyword_extractor import extract_keywords


def process_namingChange_excel_file(file_path, file_name):
    """

    1. 폴더에 있는 기존 파일을 복사해 내용을 수정하여 output 파일(순환파일) 을 생성함
    2. 기존에 이미지필터링을 통과했는지 확인하여 필터링 실행여부를 결정, 필터링 실행후 필터링 모음파일에 저장

    Parameters:
    - file_path (str): 엑셀 파일이 위치한 폴더 경로
    - file_name (str): 엑셀 파일 이름 (확장자 제외)
    - FILE_EXTENSION : 엑셀파일의 확장자 

    - tuple: (엑셀 sheet, 복사된 writable_book, writable_sheet)
      - sheet: 최초 폴더의 있는 엑셀의 첫 번째 시트를 나타내는 객체, 데이터를 읽기 위해 사용
      - writable_book: 기존 엑셀 파일을 복사하여 수정 가능한 형태로 만든 workbook 객체. 
                       데이터를 변경하거나 저장하기 위해 사용
      - writable_sheet: writable_book 내의 첫 번째 시트를 나타내는 객체. 
                        이 시트를 통해 셀 데이터를 수정하거나 추가할 수 있음.

    """ 

    sheet, writable_book, writable_sheet = read_excel_file(file_path, file_name, FILE_EXTENSION_xls)
    if sheet is None:
        return

    name_column_index = 'E'       # '상품명*' 열번호 (썸네일) 이후 이앞열에 열을 추가하므로 결과적으로 이열에 가공내용이 들어감
    number_column_index='B'       # '판매자코드' 열번호 
    name_column_index_int = column_letter_to_index(name_column_index)
    number_column_index_int = column_letter_to_index(number_column_index)

    # '상품명*' 앞에 새로운 열 삽입 (가공상품명의 결과를 추가하기 위해)
    insert_column_before(sheet, writable_sheet, name_column_index, "가공결과")


    # 기본상품명 리스트 생성 (3행부터 시작)
    naming_list = [
        sheet.cell_value(idx, name_column_index_int) 
        for idx in range(2, sheet.nrows)  # 데이터가 3행부터 시작하므로 인덱스를 2부터 시작
        if pd.notna(sheet.cell_value(idx, name_column_index_int))
    ]
    print("\n" + "="*100)
    print(f"[디버그] 기본상품명 행갯수: {sheet.nrows}") 
    #print(f"[디버그] 기본상품명가공 문자열 목록 : {naming_list}")
    print("="*100)

    # 키워드사전 로드
    dictionary = load_dictionary()

    # # 사전 내용을 출력
    print("\n[사전 내용 출력]")
    if not dictionary:
        print("[디버그] 사전에 로드된 데이터가 없습니다.")
    else:
        for main_keyword, keyword_info in dictionary.items():
            print(f"메인 키워드: {main_keyword}")
            print(f"용도: {', '.join(keyword_info.use)}")
            print(f"사양: {', '.join(keyword_info.spec)}")
            print(f"스타일: {', '.join(keyword_info.style)}")
            print(f"기타 카테고리: {', '.join(keyword_info.extra)}\n")

    # 기본상품명 분석, 메인과 보조키워드 추출
    optimized_naming_list = []
    for original_name in naming_list:
        main_keyword, sub_keywords, remaining_words = extract_keywords(original_name, dictionary)

        # 최종 반환된 sub_keywords의 필드들을 올바르게 결합하여 ProductInfo 생성
        product_info = ProductInfo(
            original_name=original_name,
            fixed_keywords=", ".join(remaining_words),  # 고정 키워드도 결합하여 추가
            main_keyword=main_keyword,
            use=", ".join(sub_keywords.use),       # 리스트 그대로 결합
            spec=", ".join(sub_keywords.spec),     # 리스트 그대로 결합
            style=", ".join(sub_keywords.style),   # 리스트 그대로 결합
            extra=", ".join(sub_keywords.extra),   # 리스트 그대로 결합
            
        )
        
        # ProductInfo 객체를 optimized_naming_list에 추가
        optimized_naming_list.append(product_info)

    # 디버그 확인
    print("[디버그] 기본상품명 키워드추출완료")
    print("[디버그] 기본상품명에서 추출된 메인키워드, 고정키워드, 보조키워드:")
    for product in optimized_naming_list:
        print(f"- 원본상품명: '{product.original_name}'")
        print(f"  -- 메인키워드: '{product.main_keyword}'")
        print(f"  -- 고정 키워드: '{product.fixed_keywords}'")
        # print(f"  용도: '{product.use}'")
        # print(f"  사양: '{product.spec}'")
        # print(f"  스타일: '{product.style}'")
        # print(f"  기타: '{product.extra}'")
        print("-" * 50)  # 구분선 추가


    # 각 상품명에 대해 네이버 API 호출하여 최적화된 이름 생성
    final_optimized_names = []  # 최종 결과를 담을 리스트

    print("\n" + "="*50)
    print("[디버그] 메인키워드를 통한 네이버검색 시작")  # 구분선 추가
    print("="*50)
    for item in optimized_naming_list:
        # item: OptimizedName 객체 - original_name, main_keyword, sub_keywords를 가지고 있음


        # >> 상품별로 패턴 생성 또는 API 호출 전 디버깅
        print(f"[디버그] 처리 중인 상품명: {item.original_name}")
        print(f"[디버그] 메인 키워드: {item.main_keyword}")
        print(f"[디버그] 고정 키워드: {item.fixed_keywords}")
        # print(f"[디버그] 보조 키워드: {item.sub_keywords.use}, {item.sub_keywords.spec}, {item.sub_keywords.style}, {item.sub_keywords.extra}")
        

        optimized_name = generate_optimized_names(item)  # API 호출 및 이름 최적화
        final_optimized_names.append(optimized_name)

    # 결과를 확인하거나 이후 단계에서 사용
    print("[디버그] 최종 상품명가공 리스트")
    print("="*50)
    
    for idx, product in enumerate(final_optimized_names, start=1):
        print(f"[디버그] 가공된 상품명 목록 {idx}")
        
        for ptype_idx, (ptype, names) in enumerate(product.processed_names.items(), start=1):
            print(f"    {ptype}: {product.original_name} (기본상품명)")  # 가공 타입 번호 붙이기
            
            for name_idx, name in enumerate(names, start=1):
                print(f"        가공패턴 {name_idx}: {name}")  # 패턴 번호 형식 적용

        print("-" * 50)  # 구분선 추가


    # 네이버 필터링
    filtered_results = apply_filters(
        final_optimized_names,  # 가공된 상품명 리스트
        spam_keywords=["초특가", "1+1", "할인행사", "특가", "빅세일"],  # 스팸 키워드 리스트
        unrelated_keywords=["스타일", "st"],  # 불필요한 키워드 리스트
        max_length=49  # 글자 수 제한
    )

    print("="*50)
    print("[디버그] 필터링 적용 후 상품명 리스트")
    print("="*50)
    for idx, result in enumerate(filtered_results, start=1):
        print(f"{idx}. 기본상품명: {result.original_name}")  # 기본 상품명 출력
        

        print(f"   메인키워드: {result.main_keyword}")  # 가공된 상품명 출력
        print(f"   고정키워드: {result.get_fixed_keywords()}")  # 가공된 상품명 출력

        # 가공타입
        print(f"   가공명타입: {result.get_processing_types()}")  # 가공된 상품명 출력

        # 필터링된 가공 상품명
        processed_names = result.processed_names.get("상위판매자분석", [])
        print(f"   가공상품명: {', '.join(processed_names)}")  # 가공된 상품명 출력

        print("-"*50)

    # 가공타입
    processing_type = list(filtered_results[0].processed_names.keys())[0]
    


    # 상품명 중복체크 
    final_optimized_naming_list= process_duplicates_with_variation(filtered_results)


    # 엑셀에 가공상품명에 가공된 상품명을 입력
    for new_idx, result in enumerate(final_optimized_naming_list):
        # 기본 상품명
        base_name = result.original_name
        
        # 가공된 상품명 (예: '상위판매자분석'의 첫 번째 결과)
        processed_name = ", ".join(result.processed_names.get("상위판매자분석", []))

        # 디버깅 출력
        print(f"[디버그] 엑셀 기록 - 행 {new_idx + 2}")
        print(f"기본상품명: {base_name}")
        print(f"가공상품명: {processed_name}")
        print(f"ptype('{ptype}')의 가공된 상품명: {processed_name}")
        # 각 데이터를 엑셀의 해당 열에 기록
        writable_sheet.write(new_idx + 2, name_column_index_int, processed_name)  # 필터상품명



    # 가공타입을 판매자관리코드에 접두사로 추가 
    update_seller_codes(sheet, writable_sheet, number_column_index_int, processing_type)


    # 가공된 상품명 열을 노란색으로 칠함 
    apply_row_color_by_condition(
        writable_sheet=writable_sheet,
        target_column=name_column_index_int,
        final_optimized_naming_list=final_optimized_naming_list,
        color_name="yellow"
    )


    # 결과 파일 저장 (output 파일(순환파일) 생성)
    output_file_path = os.path.join(file_path, f"{file_name}_output.xls")
    save_excel_file(writable_book, output_file_path)