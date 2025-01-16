from utils.global_logger import logger

def validate_name_code_list(nameCode_list: list, filterd_list: list) -> None:
    """
    상품명과 판매자관리코드 리스트의 무결성을 확인.

    Args:
        nameCode_list (list): (상품명, 판매자 관리코드) 튜플 리스트.
        filterd_list (list): 필터링된 상품명의 상태 리스트 (튜플 형태: (상태, 상품명)).

    Raises:
        ValueError: 무결성 검사에서 오류가 발견된 경우.
    """
    # 길이 일치 여부 확인
    if len(nameCode_list) != len(filterd_list):
        raise ValueError(
            f"❌ 데이터 불일치: nameCode_list 길이 ({len(nameCode_list)})와 "
            f"filterd_list 길이 ({len(filterd_list)})가 다릅니다."
        )

    # 무결성 검증 결과 저장
    invalid_entries = []

    # 매핑 확인
    for (name, code), (status, filtered_name) in zip(nameCode_list, filterd_list):
        if name != filtered_name:  # 상품명 불일치 확인
            invalid_entries.append((code, name, filtered_name, status))

    # 검증 결과 처리
    if invalid_entries:
        for entry in invalid_entries:
            code, original_name, filtered_name, status = entry
            logger.log(
                f"⚠️ 관리코드 {code}: 상품명 불일치 "
                f"(원본: '{original_name}', 필터링 결과: '{filtered_name}', 상태: {status})",
                level="WARNING"
            )
        raise ValueError(f"❌ 무결성 오류: {len(invalid_entries)}개의 항목이 불일치합니다.")

    logger.log("✅ 무결성 검증 완료: 모든 데이터가 일치합니다.", level="INFO")
