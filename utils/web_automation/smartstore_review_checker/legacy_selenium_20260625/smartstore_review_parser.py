# utils/web_automation/smartstore_review_checker/smartstore_review_parser.py

import re


def has_no_review_text(page_text):
    """
    페이지 텍스트에서 명확한 리뷰 없음 문구를 확인한다.

    주의:
    - '첫리뷰를 남겨주세요'는 리뷰이벤트 문구로
      리뷰 있는 상품에도 나올 수 있으므로 제외한다.
    """

    if not page_text:
        return False

    no_review_keywords = [
        "아직 작성된 리뷰가 없습니다",
    ]

    return any(keyword in page_text for keyword in no_review_keywords)


def extract_review_count_from_text(page_text):
    """
    페이지 전체 텍스트에서 리뷰 개수를 추정한다.

    우선순위:
    1. 줄 단위 '리뷰 3'
    2. '상세정보리뷰 3Q&A'
    3. '3건 리뷰'
    4. '5.03건 리뷰' 같은 평점 + 리뷰수 결합형
    5. '0.00건 리뷰'는 리뷰 0으로 인정

    주의:
    - 화면에서는 '평점 5.0 + 3건 리뷰'로 보이지만,
      body.text에서는 '5.03건 리뷰'처럼 붙어서 들어올 수 있다.
    """

    if not page_text:
        return None

    # -------------------------------------------------
    # 1. 줄 단위 패턴 우선 확인
    # -------------------------------------------------
    for line in page_text.splitlines():
        clean_line = line.strip()

        # 예: 리뷰 3
        match = re.fullmatch(r"리뷰\s*([0-9,]+)", clean_line)
        if match:
            return int(match.group(1).replace(",", ""))

        # 예: 구매평 3
        match = re.fullmatch(r"구매평\s*([0-9,]+)", clean_line)
        if match:
            return int(match.group(1).replace(",", ""))

        # 예: 구매후기 3
        match = re.fullmatch(r"구매후기\s*([0-9,]+)", clean_line)
        if match:
            return int(match.group(1).replace(",", ""))

    # -------------------------------------------------
    # 2. 탭 문구 패턴 확인
    # -------------------------------------------------
    tab_patterns = [
        r"상세정보리뷰\s*([0-9,]+)\s*Q&A",
        r"상세정보\s*리뷰\s*([0-9,]+)\s*Q&A",
    ]

    for pattern in tab_patterns:
        match = re.search(pattern, page_text)

        if match:
            return int(match.group(1).replace(",", ""))

    # -------------------------------------------------
    # 3. 일반 리뷰 건수 패턴 확인
    # -------------------------------------------------
    general_patterns = [
        r"([0-9,]+)\s*건\s*리뷰",
        r"([0-9,]+)\s*개의\s*리뷰",
        r"리뷰\s*([0-9,]+)",
        r"구매평\s*([0-9,]+)",
        r"구매후기\s*([0-9,]+)",
    ]

    for pattern in general_patterns:
        match = re.search(pattern, page_text)

        if match:
            number_text = match.group(1).replace(",", "")
            return int(number_text)

    # -------------------------------------------------
    # 4. 평점 + 리뷰수 결합형 처리
    # -------------------------------------------------
    # 예:
    # 화면 표시: ★ 5.0 3건 리뷰
    # body.text: 5.03건 리뷰
    #
    # 화면 표시: ★ 4.8 12건 리뷰
    # body.text: 4.812건 리뷰 형태가 될 수 있음
    #
    # 앞의 "5.0", "4.8"은 평점이고,
    # 뒤에 붙은 숫자를 리뷰 수로 본다.
    score_review_match = re.search(
        r"[0-5]\.[0-9]([1-9][0-9,]*)\s*건\s*리뷰",
        page_text,
    )

    if score_review_match:
        return int(score_review_match.group(1).replace(",", ""))

    # -------------------------------------------------
    # 5. 리뷰 없음 보조 패턴
    # -------------------------------------------------
    # 예:
    # 0.00건 리뷰 → 리뷰 0
    #
    # 5.03건 리뷰는 위에서 평점 + 리뷰수 결합형으로 처리한다.
    if "0.00건 리뷰" in page_text:
        return 0

    return None


def find_review_related_lines(page_text, max_lines=40):
    """
    페이지 텍스트 중 리뷰 관련 줄만 추려서 확인용으로 반환한다.
    """

    review_keywords = [
        "리뷰",
        "구매평",
        "구매후기",
        "평점",
        "별점",
        "만족도",
    ]

    related_lines = []

    for line in page_text.splitlines():
        clean_line = line.strip()

        if not clean_line:
            continue

        if any(keyword in clean_line for keyword in review_keywords):
            if clean_line not in related_lines:
                related_lines.append(clean_line)

        if len(related_lines) >= max_lines:
            break

    return related_lines