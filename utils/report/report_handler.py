import os
from datetime import datetime

def initialize_report_file(base_directory, file_name, extension=".txt"):
    """
    리포트 파일을 초기화합니다. 지정된 기본 경로에 오늘 날짜에 해당하는 폴더를 생성하고,
    그 안에 파일을 생성합니다. 폴더가 이미 존재하면 해당 폴더 안에 파일을 추가로 생성합니다.

    Parameters:
        base_directory (str): 리포트 파일을 저장할 기본 디렉터리 경로.
        file_name (str): 리포트 파일 이름(확장자 제외).
        extension (str): 리포트 파일 확장자 (기본값: ".txt").

    Returns:
        str: 생성된 리포트 파일의 전체 경로.
    """
    try:
        # 오늘 날짜에 해당하는 폴더 이름 생성
        today_date = datetime.now().strftime("%Y-%m-%d")
        date_directory = os.path.join(base_directory, today_date+"_순환파일리포트")

        # 날짜별 디렉터리가 존재하지 않으면 생성
        if not os.path.exists(date_directory):
            os.makedirs(date_directory)

        # 리포트 파일 전체 경로 생성
        report_path = os.path.join(date_directory, f"{file_name}{extension}")

        # 리포트 파일 초기화
        with open(report_path, "w", encoding="utf-8") as report_file:
            report_file.write("=== 작업 리포트 ===\n")
            report_file.write(f"파일 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            report_file.write("=" * 40 + "\n")

        return report_path

    except Exception as e:
        raise RuntimeError(f"리포트 파일 초기화 중 에러 발생: {e}")
    
def update_process_report(report_path, task_type, task_name, initial_count, processed_count, success="성공"):
    """
    리포트 파일에 작업 처리 정보를 기록합니다.

    Parameters:
        report_path (str): 리포트 파일 경로.
        task_type (str): 처리 타입 (예: 필터링, 검증 등).
        task_name (str): 처리 이름.
        initial_count (int): 작업 시작 전 데이터의 총 갯수.
        processed_count (int): 작업 후 처리된 데이터의 갯수.
        success (bool): 작업 성공 여부.

    Returns:
        None
    """
    try:
        with open(report_path, "a", encoding="utf-8") as report_file:
            report_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 작업 : {task_name} 완료 \n")
            report_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 처리 타입: {task_type}\n")
            report_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 최초 데이터 갯수: {initial_count}\n")
            report_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 처리된 데이터 갯수: {processed_count}\n")
            report_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 무결성 여부: {'성공' if success else '실패'}\n")
            report_file.write("-" * 60 + "\n")
    except Exception as e:
        raise RuntimeError(f"리포트 업데이트 중 에러 발생: {e}")
    
def add_separator_line(file_path):
    """
    파일에 구분선("========================================")을 저장합니다.

    Parameters:
        file_path (str): 저장할 파일 경로.

    Returns:
        None
    """
    try:
        with open(file_path, "a", encoding="utf-8") as file:
            file.write("=" * 60 + "\n")
    except Exception as e:
        raise RuntimeError(f"구분선 저장 중 에러 발생: {e}")
    
from datetime import datetime
def add_str_log(report_path, message):
    """
    리포트 파일에 간단한 로그 메시지를 추가합니다.

    Parameters:
        report_path (str): 리포트 파일 경로.
        message (str): 추가할 로그 메시지.

    Returns:
        None
    """
    try:
        with open(report_path, "a", encoding="utf-8") as report_file:
            report_file.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
    except Exception as e:
        raise RuntimeError(f"리포트 파일에 로그 추가 중 에러 발생: {e}")
    

