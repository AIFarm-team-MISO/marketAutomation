from utils.global_logger import logger

import sys
import time
import keyboard  # noqa: F401

# 색상 코드
RESET = "\033[0m"  # 색상 초기화
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
BOLD = "\033[1m"
# 바의 문자표 ( █, ▒, ■, # )

"""
프로그램 설명:
    이 모듈은 진행률 바를 사용하여 작업 상태를 시각적으로 표시하고,
    작업 처리 중 발생하는 로그를 출력하며, 작업 완료 후 요약 정보를 제공합니다.

주요 함수 설명:
1. initialize_summary():
    - 작업 요약 정보를 초기화합니다.
    - 반환값: {"processed": 0, "errors": 0} 형태의 딕셔너리.

2. log_for_process_bar(idx, image_url, summary):
    - 개별 작업을 처리하고, 작업 진행 상황(처리된 항목, 오류)을 업데이트합니다.
    - 매개변수:
        - idx: 현재 작업 인덱스.
        - image_url: 처리할 이미지 URL.
        - summary: 작업 요약 정보를 저장하는 딕셔너리.

3. finish_progressbar_summary(summary, total_items, bar_length=50, color=CYAN):
    - 작업 완료 후 진행률 바를 100%로 갱신하고, 요약 정보를 출력합니다.
    - 매개변수:
        - summary: 작업 요약 정보.
        - total_items: 총 작업 개수.
        - bar_length: 진행률 바 길이 (기본값: 50).
        - color: 진행률 바 색상.

4. log_message(message, level="INFO"):
    - 진행률 바 아래에 로그 메시지를 출력하거나, 주요 이벤트만 실시간으로 표시합니다.
    - 매개변수:
        - message: 출력할 메시지.
        - level: 로그 수준 ("INFO", "ERROR", "WARNING" 등).

5. finalize_progress_bar():
    - 진행률 바 작업을 종료하고, 커서 위치를 정리합니다.
    - 진행률 바 출력 후 줄바꿈을 추가합니다.

6. print_progress_bar(current, total, bar_length=50, color=CYAN):
    - 고정된 위치에 진행률 바를 출력하고 업데이트합니다.
    - 매개변수:
        - current: 현재 진행 상태 (0부터 시작).
        - total: 총 작업 개수.
        - bar_length: 진행 바 길이 (기본값: 50).
        - color: 진행 바 색상.

사용 흐름:
    1. initialize_summary()로 요약 정보를 초기화합니다.
    2. for 루프에서 각 작업마다:
        - print_progress_bar로 진행률 바를 갱신합니다.
        - log_for_process_bar로 개별 작업을 처리하고 요약 정보를 업데이트합니다.
    3. 작업 완료 후:
        - finish_progressbar_summary로 진행률 바를 100%로 갱신하고, 요약 정보를 출력합니다.
        
"""


def initialize_summary():
    """
    작업 요약 정보를 초기화하는 함수.
    
    Returns:
        dict: 초기화된 요약 정보.
    """
    return {"processed": 0, "errors": 0}

def log_for_process_bar(idx, image_url, summary):
    """
    개별 작업을 처리하고 요약 정보를 업데이트하는 함수.

    Parameters:
        image_url (str): 처리할 이미지 URL.
        summary (dict): 요약 정보 딕셔너리.

    Returns:
        None
    """
    try:
        # 실제 처리 로직 (필터링 등)
        log_message(f"Processing {idx}번째 {image_url}", level="DEBUG")
        # 예외적으로 발생할 수 있는 조건 시뮬레이션
        if "error" in image_url:
            raise ValueError("Simulated error")
        summary["processed"] += 1
    except Exception as e:
        log_message(f"Error processing {image_url}: {str(e)}", level="ERROR")
        summary["errors"] += 1

def finish_progressbar_summary(summary, total_items, bar_length=50, color=CYAN):
    """
    작업 완료 후 진행률 바를 100%로 표시하고 요약 정보를 출력.

    Parameters:
        summary (dict): 요약 정보 딕셔너리.
        total_items (int): 총 작업 개수.
        bar_length (int): 진행 바 길이 (기본값: 50).
        color (str): 진행 바 색상.
    """

    finalize_progress_bar()

    # 진행률 바를 100%로 갱신
    print_progress_bar(total_items, total_items, bar_length, color)

    # 요약 정보 출력
    logger.log_separator()
    logger.log("📌 작업 완료 요약 정보", level="INFO")
    logger.log(f"총 작업 대상 갯수: {total_items}", level="INFO")
    logger.log(f"처리된 항목: {summary['processed']}", level="INFO")
    logger.log(f"오류 발생 항목: {summary['errors']}", level="INFO")
    logger.log_separator()


    

    
def log_message(message, level="INFO"):
    """
    진행률 바 아래에 요약 로그를 출력하거나, 주요 이벤트만 출력하는 함수.

    Parameters:
    - message (str): 출력할 메시지.
    - level (str): 로그 수준 (기본값: "INFO").
    """
    if level in ["ERROR", "WARNING"]:  # 주요 로그만 실시간 출력
        sys.stdout.write("\033[s")  # 현재 커서 위치 저장
        sys.stdout.write("\033[H\033[1B")  # 진행률 바 아래로 이동
        sys.stdout.write("\033[K")  # 현재 줄 내용 지우기
        logger.log(message, level=level)  # 로그 출력
        sys.stdout.flush()
    else:
        # 비중요 로그는 파일에 기록
        logger.log(message, level=level)

def finalize_progress_bar():
    """
    진행률 바 작업 완료 후 줄바꿈을 추가하여 출력 상태를 정리하는 함수.
    """
    sys.stdout.write("\n")
    sys.stdout.flush()


def print_progress_bar(current, total, bar_length=50, color=CYAN):
    """
    고정된 위치에 진행률 바를 출력하고 로그 구분선을 포함하는 함수.

    Parameters:
    - current (int): 현재 진행 상태.
    - total (int): 총 작업 개수.
    - logger: 로그 출력용 logger 객체.
    - bar_length (int): 진행 바 길이 (기본값: 50).
    """
    progress = current / total
    filled_length = int(bar_length * progress)
    bar = "█" * filled_length + "-" * (bar_length - filled_length)
    percentage = progress * 100

    # ANSI escape 코드로 화면 상단에 고정
    sys.stdout.write("\033[H")  # 화면 맨 위로 이동
    sys.stdout.write("\033[2K")  # 현재 줄 초기화
    sys.stdout.write(f"{color}Progress: |{bar}| {percentage:.2f}%{RESET}\n")
    sys.stdout.flush()


    

    # # 진행률 바를 한 줄에 고정 출력
    # sys.stdout.write(f"\r{color}Progress: |{bar}| {percentage:.2f}%{RESET}")
    # sys.stdout.flush()  # 즉시 출력
    # # 진행이 완료되면 새 줄 추가
    # if current == total:
    #     sys.stdout.write("\n")  # 완료 후 새 줄 추가
    #     sys.stdout.flush()

    # # 커서를 이동하여 진행 바를 고정된 위치에 출력
    # sys.stdout.write("\033[F\033[K" * 2)  # 커서를 두 줄 위로 이동하고 해당 줄을 지움
    # print("\n")  # 빈 줄 추가
    
    # # 진행률 바 출력
    # sys.stdout.write(f"\r{color}Progress: |{bar}| {percentage:.2f}%{RESET}\n")
    # sys.stdout.flush()  # 즉시 출력


    # # 진행률 바 출력 (색상 적용) : 각각의 개체의 색상을 적용할때
    # sys.stdout.write(f"\rProgress: |"  # 진행 바 시작
    #                  f"\033[32m{bar}\033[0m"  # 초록색 바 (ANSI 색상 코드 적용 후 리셋)
    #                  f"| {percentage:.2f}%\n")
    # sys.stdout.flush()  # 즉시 출력

    # 로그 구분선 출력
    # logger.log_separator()

# def print_progress_bar(iteration, total, bar_length=50, color=CYAN):
#     """
#     진행률 바를 출력하는 함수.

#     Parameters:
#     - iteration (int): 현재 반복 횟수
#     - total (int): 전체 반복 횟수
#     - bar_length (int): 진행 바의 길이 (디폴트 50)
#     - color (str): 색상 코드
#     """
#     percent = (iteration / total) * 100
#     filled_length = int(bar_length * iteration // total)
#     # 바의 문자표 ( █, ▒, ■, # )
#     bar = "█" * filled_length + "-" * (bar_length - filled_length)
    
    
#     sys.stdout.write(f"\r{color}Progress: |{bar}| {percent:.2f}%{RESET}")
#     sys.stdout.flush()


def calculate_estimates(item_list, process_type):

    """
    task_type == 이미지필터링
        item_list 의 status 가 "새로운이미지" 인지 아닌지를 판별해
        예상 구글ocr 호출 비용과 시간을 계산 

    task_type == 상품명가공
        기본상품명 리스트를 사전에서 조회하여 존재 여부를 확인하고
        예상 GPT 호출 비용과 시간을 계산. 

    """
    filtered_count = 0  # 사전에 이미 있는 기본상품명 개수
    unfiltered_count = 0  # 사전에 없는 기본상품명 개수
    exchange_rate = 1450  # 환율 (1 USD = 1450 KRW)

    logger.log(f'{process_type} 프로세스 계산 시작!')
    # logger.log(f' {item_list} ')

    if process_type == "상품명가공":
        # 작업 유형에 따른 기본 설정
        actual_cost_per_call = 2.14 / 919  # 실 사용량 기준으로 계산
        estimated_cost_per_1000_calls = actual_cost_per_call * 1000  # 1000건당 비용        
        estimated_time_per_call = 2  # GPT 호출당 소요 시간 (초)

        # 상품명 가공 작업
        assert isinstance(item_list, list), "item_list must be a list for 이미지필터링"
        for status, image_url in item_list:
            if status == "새로운문자열":
                unfiltered_count += 1
            else:
                filtered_count += 1

        logger.log(f"이미 처리된 기존 상품명 갯수: {filtered_count}")

    elif process_type == "이미지필터링":
        # 작업 유형에 따른 기본 설정
        estimated_cost_per_1000_calls = 1.50  # 1000건당 이미지 필터링 비용 (달러)
        estimated_time_per_call = 0.5  # 이미지 필터링당 소요 시간 (초)

        # 이미지 필터링 작업
        assert isinstance(item_list, list), "item_list must be a list for 이미지필터링"
        for status, image_url in item_list:
            if status == "새로운이미지":
                unfiltered_count += 1
            else:
                filtered_count += 1
            # logger.log(f"Status: {status}, URL: {image_url}")

    else:
        raise ValueError(f"Invalid task_type: {process_type}. Use '상품명가공' or '이미지필터링'.")


    # 예상 비용과 시간 계산
    estimated_cost_usd = (unfiltered_count / 1000) * estimated_cost_per_1000_calls
    estimated_cost_krw = estimated_cost_usd * exchange_rate
    estimated_time_sec = unfiltered_count * estimated_time_per_call
    estimated_time_min = estimated_time_sec // 60
    remaining_seconds = estimated_time_sec % 60

    return filtered_count, unfiltered_count, estimated_cost_usd, estimated_cost_krw, estimated_time_min, remaining_seconds


def run_filtering_item_process(filtered_item_list, process_type, task_type="single"):
    """
        작업 유형에 따라 시간과 비용 계산.

        Parameters:
            filtered_result (list): 필터링된 결과 (상태, URL).
            process_type (str): 작업 유형 ("이미지필터링" or "상품명가공")

        Returns:
            None
    """
    logger.log_separator()
    logger.log(f"=== {process_type} 시간 및 비용 계산 ===", level="INFO")

    total_items = len(filtered_item_list)

    # logger.log(f"=== filtered_item_list : {filtered_item_list}  ===", level="INFO")


    # 사전 조회 및 비용/시간 산출
    filtered_count, unfiltered_count, estimated_cost_usd, estimated_cost_krw, estimated_time_min, remaining_seconds = calculate_estimates(filtered_item_list, process_type)

    # 결과 출력
    logger.log_separator()
    logger.log(f"=== {process_type} 프로세스 예비 분석 ===")
    logger.log(f"총 작업 대상 갯수: {total_items}개")
    logger.log(f"사전에 이미 처리된 작업대상 갯수: {filtered_count}개")
    logger.log(f"API 호출 작업대상 갯수 : {unfiltered_count}개")
    logger.log(f"예상 비용: ${estimated_cost_usd:.2f} (USD) / {int(estimated_cost_krw):,} 원 (KRW)")
    logger.log(f"예상 소요 시간: {int(estimated_time_min)}분 {int(remaining_seconds)}초")
    logger.log_separator()


    if task_type == "auto":
        logger.log(f"▶️ 자동 실행 모드 활성화 {task_type} 작업).", level="INFO")
        return True  # 바로 진행
    
    else:
        logger.log("\n▶️ Enter 키를 누르면 계속 진행합니다. ESC 키를 누르면 프로그램을 종료합니다.")

        while True:
            if keyboard.is_pressed("enter"):  # 스페이스 키 감지
                print("✅ 스페이스 키 입력 감지. 계속 진행합니다...")
                return True  # 프로세스 진행
            elif keyboard.is_pressed("esc"):  # ESC 키 감지
                print("❌ ESC 키 입력 감지. 프로그램을 종료합니다.")
                raise SystemExit("프로그램이 종료되었습니다.")
