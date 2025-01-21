from utils.global_logger import logger

from keywordDictionary.keyword_extractor import extract_keywords

def process_naming_list_with_gpt(dictionary, naming_list, missing_threshold=1):
    """
    naming_list를 처리하여 GPT 데이터를 생성하고 무결성을 검증하는 함수.
    
    Args:
        dictionary (dict): JSON 데이터로 로드된 딕셔너리.
        naming_list (list): 기본상품명 리스트.
        missing_threshold (int): 기록되지 않은 상품명의 임계치.

    Returns:
        list: 처리된 GPT 데이터 리스트.

    Raises:
        ValueError: 데이터 불일치 또는 임계치 초과 시 예외 발생.
    """
    try:
        # 1. 초기 상태 설정
        initial_dictionary_snapshot = {
            key: set(data.get("기본상품명", []))
            for key, data in dictionary.items()
        }

        # 추적 변수 초기화
        extract_namingData_list = []
        missing_after_processing = []
        initial_existing_count = 0
        added_to_dictionary_count = 0

        total_items = len(naming_list)
        logger.log(f"📌 총 {total_items}개의 기본상품명 처리 시작", level="INFO", also_to_report=True, separator="none")
        
        # 2. naming_list 처리 루프
        for index, original_name in enumerate(naming_list, start=1):
            logger.log(f"🟡 [{index}/{total_items}] '{original_name}' 처리 시작", level="INFO", also_to_report=True, separator="none")
            
            # 2.1 GPT 데이터를 생성 또는 가져오기
            gptData = extract_keywords(original_name, dictionary)
            if not gptData:
                logger.log(f"⚠️ {original_name}에 대한 GPT 데이터가 없습니다.", level="WARNING")
                continue
            
            extract_namingData_list.append(gptData)
            
            # 2.2 기존 데이터와 비교
            is_existing = check_if_existing(original_name, initial_dictionary_snapshot)
            if is_existing:
                initial_existing_count += 1
                continue

            # 2.3 새로운 데이터 추가 여부 확인
            is_added = check_if_added(original_name, dictionary)
            if is_added:
                added_to_dictionary_count += 1
            else:
                missing_after_processing.append(original_name)
                if len(missing_after_processing) >= missing_threshold:
                    raise_threshold_exceeded(missing_threshold, missing_after_processing)

        # 3. 데이터 무결성 확인
        validate_list_lengths(naming_list, extract_namingData_list)

        # 4. 처리 완료 로그 출력
        logger.log(f"📌 사전조회 및 GPT호출 데이터 처리결과.", level="INFO", also_to_report=True, separator="dash-1line")
        logger.log(f"💬 총 {total_items}개의 데이터 처리 완료.", level="INFO", also_to_report=True, separator="none")
        logger.log(f"💬 사전에 이미 존재했던 기본상품명 수: {initial_existing_count}", level="INFO", also_to_report=True, separator="none")
        logger.log(f"💬 새로 추가된 기본상품명 수: {added_to_dictionary_count}", level="INFO", also_to_report=True, separator="none")
        
        return total_items, initial_existing_count, added_to_dictionary_count, extract_namingData_list

    except ValueError as e:
        logger.log(f"❌ 처리 중 오류 발생: {e}", level="ERROR")
        raise


def check_if_existing(original_name, snapshot):
    """
    사전에 이미 등록된 기본상품명인지 확인.

    Args:
        original_name (str): 확인할 상품명.
        snapshot (dict): 초기 사전 스냅샷.

    Returns:
        bool: 존재 여부.
    """
    return any(original_name in names for names in snapshot.values())

def check_if_added(original_name, dictionary):
    """
    GPT 데이터 처리 후, 기본상품명이 사전에 새로 추가되었는지 확인.

    Args:
        original_name (str): 확인할 상품명.
        dictionary (dict): 현재 사전 데이터.

    Returns:
        bool: 추가 여부.
    """
    return any(
        original_name in set(data.get("기본상품명", []))
        for data in dictionary.values()
    )


def raise_threshold_exceeded(threshold, missing_list):
    """
    기록되지 않은 상품명이 임계치를 초과했을 때 예외를 발생.

    Args:
        threshold (int): 임계치.
        missing_list (list): 기록되지 않은 상품명 리스트.

    Raises:
        ValueError: 임계치 초과 예외.
    """
    error_message = (
        f"❌ 임계치 초과: 기록되지 않은 상품명 수가 {threshold}개를 초과했습니다."
        f"\n기록되지 않은 상품명: {missing_list}"
    )
    logger.log(error_message, level="CRITICAL")
    raise ValueError(error_message)

def validate_list_lengths(input_list, output_list):
    """
    입력 리스트와 출력 리스트의 길이를 비교하여 무결성을 검증.

    Args:
        input_list (list): 입력 데이터 리스트.
        output_list (list): 출력 데이터 리스트.

    Raises:
        ValueError: 길이가 일치하지 않을 경우 예외 발생.
    """
    if len(input_list) != len(output_list):
        error_message = (
            f"❌ 데이터 불일치: 입력 리스트({len(input_list)})와 출력 리스트({len(output_list)})의 길이가 다릅니다."
        )
        logger.log(error_message, level="ERROR")
        raise ValueError(error_message)



