# utils/web_automation/product_status_runner.py

"""
여러 상품코드 상태 확인 실행 모듈

역할:
- 엑셀에서 복사한 여러 줄 상품코드를 입력받는다.
- 상품코드를 한 줄씩 분리한다.
- 각 상품코드를 도매처 사이트에서 검색한다.
- 검색 결과에서 정상 / 품절 / 제품없음 / 확인실패로 분류한다.
- 최종 결과를 그룹별로 출력한다.
"""

import os



from utils.web_automation.wholesale_status_checker.product_searcher import search_product_code
from utils.web_automation.wholesale_status_checker.product_checker import (
    check_3mro_product_status_from_search_result,
)


def parse_product_code_entries(raw_codes):
    """
    입력된 상품코드 목록을 검색용 코드와 출력용 코드로 분리한다.

    입력 가능 예:
    SP-3MR_94
    SP-3MR_96
    3MR_9423
    3MR_9625
    20697

    반환 예:
    [
        {
            "raw_input_code": "SP-3MR_94",
            "search_code": "94",
            "output_code": "SP-3MR_94",
        },
        {
            "raw_input_code": "20697",
            "search_code": "20697",
            "output_code": "20697",
        },
    ]

    원칙:
    - 검색은 search_code로 한다.
    - 결과 출력은 output_code로 한다.
    - 접두사가 있으면 output_code는 원본 그대로 유지한다.
    """

    product_code_entries = []

    for line in str(raw_codes).splitlines():
        raw_input_code = line.strip()

        if not raw_input_code:
            continue

        # 엑셀에서 여러 칸이 같이 복사된 경우 첫 번째 칸만 사용
        if "\t" in raw_input_code:
            raw_input_code = raw_input_code.split("\t")[0].strip()

        # 출력용 코드는 원본 그대로 사용
        output_code = raw_input_code

        # 검색용 코드는 마지막 '_' 뒤의 값을 사용
        # 예:
        # SP-3MR_94 -> 94
        # 3MR_9423 -> 9423
        # 20697 -> 20697
        if "_" in raw_input_code:
            search_code = raw_input_code.rsplit("_", 1)[1].strip()
        else:
            search_code = raw_input_code

        product_code_entries.append({
            "raw_input_code": raw_input_code,
            "search_code": search_code,
            "output_code": output_code,
        })

    return product_code_entries

def check_single_product_code(driver, site_key, product_code):
    """
    상품코드 1개를 검색하고 상태를 판별한다.
    """

    search_product_code(driver, site_key, product_code)

    if site_key == "3mro":
        product_status = check_3mro_product_status_from_search_result(
            driver,
            product_code,
            site_key=site_key,
        )
        return product_status

    raise ValueError(f"아직 지원하지 않는 site_key 입니다: {site_key}")


def check_multiple_product_codes(driver, site_key, raw_codes):
    """
    여러 상품코드를 순서대로 확인하고 결과를 분류한다.

    입력 파일에는 아래처럼 섞어서 넣을 수 있다.

    SP-3MR_94
    SP-3MR_96
    3MR_9423
    3MR_9625
    20697

    검색할 때는 숫자만 사용하고,
    결과 출력에는 입력된 원본 코드를 그대로 사용한다.
    """

    product_code_entries = parse_product_code_entries(raw_codes)

    results = {
        "normal": [],
        "sold_out": [],
        "not_found": [],
        "need_check": [],
        "failed": [],
        "details": [],
    }

    print("=" * 80)
    print(f"상품코드 상태 확인 시작: 총 {len(product_code_entries)}개")
    print("=" * 80)

    for index, entry in enumerate(product_code_entries, start=1):
        search_code = entry["search_code"]
        output_code = entry["output_code"]

        try:
            product_status = check_single_product_code(
                driver,
                site_key,
                search_code,
            )

            status = product_status.get("status")

            if status == "selling":
                results["normal"].append(output_code)
                display_status = "정상"

            elif status == "sold_out":
                results["sold_out"].append(output_code)
                display_status = "품절"

            elif status == "not_found":
                results["not_found"].append(output_code)
                display_status = "제품없음"

            elif status == "need_check":
                results["need_check"].append(output_code)
                display_status = "확인필요"

            else:
                results["failed"].append(output_code)
                display_status = "확인실패"

            # 상세 결과에는 원본/검색용/출력용 코드를 같이 남김
            product_status["raw_input_code"] = entry["raw_input_code"]
            product_status["search_code"] = search_code
            product_status["output_code"] = output_code

            results["details"].append(product_status)

            print(f"[{index}/{len(product_code_entries)}] {output_code} → {display_status}")

        except Exception as e:
            print(f"[{index}/{len(product_code_entries)}] {output_code} → 확인실패 / {e}")

            results["failed"].append(output_code)
            results["details"].append({
                "raw_input_code": entry["raw_input_code"],
                "search_code": search_code,
                "output_code": output_code,
                "found": None,
                "status": "failed",
                "sold_out": None,
                "reason": str(e),
                "current_url": getattr(driver, "current_url", ""),
            })

    return results
def build_grouped_product_status_result_text(results):
    """
    상품코드 상태 확인 결과를 텍스트로 만든다.

    이 함수에서 만든 텍스트를
    1. 콘솔 출력
    2. txt 파일 저장
    양쪽에서 같이 사용한다.
    """

    normal = results.get("normal", [])
    sold_out = results.get("sold_out", [])
    not_found = results.get("not_found", [])
    need_check = results.get("need_check", [])
    failed = results.get("failed", [])

    total_count = (
        len(normal)
        + len(sold_out)
        + len(not_found)
        + len(need_check)
        + len(failed)
    )

    lines = []

    lines.append("=" * 80)
    lines.append("[상품코드 상태 확인 최종 결과]")
    lines.append(f"총 확인: {total_count}개")
    lines.append("=" * 80)

    lines.append("")
    lines.append(f"정상 ({len(normal)}개)")
    lines.append("\n".join(normal) if normal else "없음")

    lines.append("")
    lines.append(f"품절 ({len(sold_out)}개)")
    lines.append("\n".join(sold_out) if sold_out else "없음")

    lines.append("")
    lines.append(f"제품없음 ({len(not_found)}개)")
    lines.append("\n".join(not_found) if not_found else "없음")

    lines.append("")
    lines.append(f"확인필요 ({len(need_check)}개)")
    lines.append("\n".join(need_check) if need_check else "없음")

    lines.append("")
    lines.append(f"확인실패 ({len(failed)}개)")
    lines.append("\n".join(failed) if failed else "없음")

    lines.append("=" * 80)

    return "\n".join(lines)

def print_grouped_product_status_results(results):
    """
    상품코드 상태 확인 결과를 그룹별로 출력한다.
    """

    result_text = build_grouped_product_status_result_text(results)
    print(result_text)

def save_grouped_product_status_results_to_text_file(results):
    """
    상품코드 상태 확인 결과를 web_automation 폴더 아래 txt 파일로 저장한다.

    저장 파일:
    utils/web_automation/product_status_result.txt
    """

    current_dir = os.path.dirname(__file__)

    output_file_path = os.path.join(
        current_dir,
        "product_status_result.txt"
    )

    result_text = build_grouped_product_status_result_text(results)

    with open(output_file_path, "w", encoding="utf-8-sig") as f:
        f.write(result_text)

    print("=" * 80)
    print("상품코드 상태 확인 결과를 txt 파일로 저장했습니다.")
    print(f"저장 경로: {output_file_path}")
    print("=" * 80)

    return output_file_path