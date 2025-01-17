import os
from datetime import datetime

class Logger:
    def __init__(self, log_file="logs_and_report/debug.log", enable_console=True, report_dir="logs_and_report/reports"):
        """
        Logger 클래스 초기화
        :param log_file: 로그 파일 경로
        :param enable_console: 콘솔 출력 활성화 여부
        :param report_dir: 리포트 파일 저장 디렉터리
        """
        self.log_file = log_file
        self.enable_console = enable_console
        self.report_dir = report_dir
        self.report_path = None  # 리포트 파일 경로

        # 이모지 설정
        self.emojis = {
            "기본상품명": "📝",
            "제품군": "🛒",
            "메인키워드": "🔑",
            "고정키워드": "📌",
            "용도": "🛠️",
            "사양": "⚙️",
            "스타일": "🎨",
            "기타 카테고리": "📂",
            "연관검색어": "🔍",
            "브랜드키워드": "🏷️",
            "음식 카테고리 체크": "🍴",
            "이미지 필터링": "🖼️",
            "상품명 가공": "🛒",
            "도매토피아 가공": "🏷️",
            "순환 파일 테스트": "🔄",
            "모든 마켓 폴더 생성": "🔄",
            "스마트스토어": "💚",
            "옥션/지마켓": "💙",
            "11번가": "❤️",
            "고도몰": "⚪",
        }

        # 로그 파일 디렉터리 생성
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 리포트 디렉터리 생성
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)

        # 리포트 파일 초기화
        self._initialize_report()

    def _initialize_report(self):
        """
        리포트 파일을 기본 이름(report.txt)으로 초기화.
        """
        today_date = datetime.now().strftime("%Y-%m-%d")
        date_directory = os.path.join(self.report_dir, today_date)

        if not os.path.exists(date_directory):
            os.makedirs(date_directory)

        self.report_path = os.path.join(date_directory, "✅작업전체-report.txt")
        with open(self.report_path, "w", encoding="utf-8") as report_file:
            report_file.write("=== 기본 작업 리포트 ===\n")
            report_file.write(f"파일 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            report_file.write("=" * 40 + "\n")

    def update_initial_report(self, message, level="INFO"):
        """
        초기화된 리포트 파일에 내용을 추가합니다.
        :param message: 기록할 메시지
        :param level: 로그 레벨 (기본값: INFO)
        """
        if not self.report_path:
            raise RuntimeError("리포트 파일이 초기화되지 않았습니다.")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"[{timestamp}] [{level}] {message}"

        # 초기화된 리포트 파일에 기록
        with open(self.report_path, "a", encoding="utf-8") as report_file:
            report_file.write(full_message + "\n")

    def prepend_report_file_name(self, prefix):
        """
        리포트 파일 이름 앞에 접두사를 추가하여 새 리포트를 생성.
        동일한 이름의 파일이 존재하면 삭제 후 초기화합니다.
        
        :param prefix: 파일 이름에 추가할 접두사
        """
        if not self.report_path:
            raise RuntimeError("리포트 파일이 초기화되지 않았습니다.")

        # 현재 날짜 기준 디렉터리 생성
        today_date = datetime.now().strftime("%Y-%m-%d")
        date_directory = os.path.join(self.report_dir, today_date)
        if not os.path.exists(date_directory):
            os.makedirs(date_directory)

        # 새로운 파일 이름 생성
        base_name = "report.txt"
        new_name = f"{prefix}_{base_name}"
        new_path = os.path.join(date_directory, new_name)

        # 기존 파일이 존재하면 삭제
        if os.path.exists(new_path):
            os.remove(new_path)

        # 새로운 리포트 파일 초기화
        with open(new_path, "w", encoding="utf-8") as report_file:
            report_file.write("=== 파일별 작업 리포트 ===\n")
            report_file.write(f"파일 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            report_file.write(f"처리 대상 파일: {prefix}\n")
            report_file.write("=" * 40 + "\n")

        # 새로 생성된 리포트 경로를 업데이트
        self.report_path = new_path

    def _get_emoji(self, text):
        """
        텍스트에서 이모지를 추출하는 메서드.
        :param text: 이모지를 찾을 텍스트
        :return: 매핑된 이모지 문자열
        """
        return next((emoji for key, emoji in self.emojis.items() if key in text), "")

    def log(self, message, also_to_report=False, data=None, level="INFO", emoji_key=None, include_emoji=True, separator="none"):
        """
        로그와 리포트를 기록.
        :param message: 로그 메시지
        :param also_to_report: 리포트에도 기록할지 여부
        :param data: 추가 데이터
        :param level: 로그 레벨
        :param emoji_key: 이모지 키 (self.emojis에서 가져옴)
        :param include_emoji: 이모지를 포함할지 여부
        :param separator: 구분선 출력 여부 ("none", "1line", "2line", "dash", "dash-1line", "dash-2line")
        """
        if separator == "1line":
            self.log_separator(level=level, also_to_report=also_to_report)
        elif separator == "2line":
            self.log_separator(level=level, also_to_report=also_to_report)
        elif separator == "dash-1line":
            self.log_separator(level=level, also_to_report=also_to_report, char="-")
        elif separator == "dash-2line":
            self.log_separator(level=level, also_to_report=also_to_report, char="-")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        emoji = self.emojis.get(emoji_key, "") if include_emoji else ""

        # 메시지 조합
        full_message = f"[{timestamp}] [{level}] {emoji} {message}"
        if data:
            full_message += f" {data}"

        # 콘솔 출력
        if self.enable_console:
            print(full_message)

        # 로그 파일 기록
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(full_message + "\n")

        # 리포트 파일 기록
        if also_to_report and self.report_path:
            with open(self.report_path, "a", encoding="utf-8") as f:
                f.write(full_message + "\n")

        if separator == "2line":
            self.log_separator(level=level, also_to_report=also_to_report)
        elif separator == "dash-2line":
            self.log_separator(level=level, also_to_report=also_to_report, char="-")

    def log_choices(self, choices, message=None, also_to_report=False, separator="none"):
        """
        선택지를 로그와 리포트에 출력하는 메서드.
        :param choices: 선택지 딕셔너리 (key: 선택 번호, value: 선택 항목)
        :param message: 선택지 메시지
        :param also_to_report: 리포트에도 기록할지 여부
        :param separator: 구분선 출력 여부 ("none", "1line", "2line", "dash", "dash-1line", "dash-2line")
        """
        if separator == "1line":
            self.log_separator(level="INFO", also_to_report=also_to_report)
        elif separator == "2line":
            self.log_separator(level="INFO", also_to_report=also_to_report)
        elif separator == "dash-1line":
            self.log_separator(level="INFO", also_to_report=also_to_report, char="-")
        elif separator == "dash-2line":
            self.log_separator(level="INFO", also_to_report=also_to_report, char="-")

        self.log(f"{message}작업을 선택 해주세요!", level="INFO", also_to_report=also_to_report)
        for key, value in choices.items():
            emoji = self._get_emoji(value)
            self.log(f"{key}. {emoji} {value}", level="INFO", also_to_report=also_to_report)

        if separator == "2line":
            self.log_separator(level="INFO", also_to_report=also_to_report)
        elif separator == "dash-2line":
            self.log_separator(level="INFO", also_to_report=also_to_report, char="-")

    def log_list(self, title, data, level="DEBUG", also_to_report=False, separator="none"):
        """
        리스트 데이터를 로그와 리포트에 출력.
        :param title: 출력 제목
        :param data: 리스트 데이터
        :param level: 로그 레벨
        :param also_to_report: 리포트에도 기록할지 여부
        :param separator: 구분선 출력 여부 ("none", "1line", "2line", "dash", "dash-1line", "dash-2line")
        """
        if separator == "1line":
            self.log_separator(level=level, also_to_report=also_to_report)
        elif separator == "2line":
            self.log_separator(level=level, also_to_report=also_to_report)
        elif separator == "dash-1line":
            self.log_separator(level=level, also_to_report=also_to_report, char="-")
        elif separator == "dash-2line":
            self.log_separator(level=level, also_to_report=also_to_report, char="-")

        emoji = self._get_emoji(title)
        if title.startswith(emoji):
            emoji = ""  # 제목에 이미 이모지가 포함된 경우 빈 문자열로 설정

        if data:
            self.log(f"{emoji} {title}:".strip(), level=level, also_to_report=also_to_report)  # 제목 출력
            for item in data:
                self.log(f"  - {item}", level=level, also_to_report=also_to_report)  # 리스트의 각 항목 출력
        else:
            self.log(f"{emoji} {title}: 없음".strip(), level=level, also_to_report=also_to_report)

        if separator == "2line":
            self.log_separator(level=level, also_to_report=also_to_report)
        elif separator == "dash-2line":
            self.log_separator(level=level, also_to_report=also_to_report, char="-")

    def log_separator(self, char="=", length=100, level="INFO", title=None, also_to_report=False):
        """
        로그와 리포트에 구분선을 추가하는 메서드.
        :param char: 구분선에 사용할 문자 (기본값: '=')
        :param length: 구분선 길이 (기본값: 100)
        :param level: 로그 레벨
        :param title: 구분선 제목 (선택적)
        :param also_to_report: 리포트에도 기록할지 여부
        """
        separator = char * length
        if title:
            emoji = self._get_emoji(title)
            emoji = emoji if not title.startswith(emoji) else ""  # 중복 방지
            self.log(f"{emoji} {title}", level=level, also_to_report=also_to_report)
        self.log(separator, level=level, also_to_report=also_to_report)

    def log_dict(self, title, data, level="DEBUG", also_to_report=False, separator="none"):
        """
        딕셔너리 데이터를 로그와 리포트에 출력.
        :param title: 출력 제목
        :param data: 딕셔너리 데이터
        :param level: 로그 레벨
        :param also_to_report: 리포트에도 기록할지 여부
        :param separator: 구분선 출력 여부 ("none", "1line", "2line", "dash", "dash-1line", "dash-2line")
        """
        if separator == "1line":
            self.log_separator(level=level, also_to_report=also_to_report)
        elif separator == "2line":
            self.log_separator(level=level, also_to_report=also_to_report)
        elif separator == "dash-1line":
            self.log_separator(level=level, also_to_report=also_to_report, char="-")
        elif separator == "dash-2line":
            self.log_separator(level=level, also_to_report=also_to_report, char="-")

        if data is None:
            self.log(f"{title}: 데이터가 None입니다.", level="WARNING", also_to_report=also_to_report)
            return

        emoji = self._get_emoji(title)
        if title.startswith(emoji):
            emoji = ""  # 중복 방지

        self.log(f"{emoji} {title}:", level=level, include_emoji=False, also_to_report=also_to_report)

        for key, value in data.items():
            item_emoji = self.emojis.get(key, "")
            item_emoji = item_emoji if not key.startswith(item_emoji) else ""  # 중복 방지

            if isinstance(value, list):
                formatted_value = ", ".join(value) if value else "없음"
            else:
                formatted_value = value if value else "없음"

            self.log(f"    {item_emoji} {key}: {formatted_value}".strip(), level=level, also_to_report=also_to_report)

        if separator == "2line":
            self.log_separator(level=level, also_to_report=also_to_report)
        elif separator == "dash-2line":
            self.log_separator(level=level, also_to_report=also_to_report, char="-")

    def log_processed_data(self, basic_product_names, make_naver_names, title="최종 상품명가공 리스트", level="INFO", also_to_report=False, separator="none"):
        """
        기본상품명과 가공된 상품명을 로그와 리포트에 출력.
        :param basic_product_names: 기본상품명 리스트
        :param make_naver_names: 최적화된 상품명 리스트
        :param title: 로그 제목
        :param level: 로그 레벨
        :param also_to_report: 리포트에도 기록할지 여부
        :param separator: 구분선 출력 여부 ("none", "1line", "2line", "dash", "dash-1line", "dash-2line")
        """
        if separator == "1line":
            self.log_separator(title=title, char="=", level=level, also_to_report=also_to_report)
        elif separator == "2line":
            self.log_separator(title=title, char="=", level=level, also_to_report=also_to_report)
        elif separator == "dash-1line":
            self.log_separator(title=title, char="-", level=level, also_to_report=also_to_report)
        elif separator == "dash-2line":
            self.log_separator(title=title, char="-", level=level, also_to_report=also_to_report)

        for i, basic_name in enumerate(basic_product_names, start=1):
            # 가공상품명과 기본상품명을 연결
            processed_name = make_naver_names[i - 1] if i - 1 < len(make_naver_names) else "없음"

            # 로그 출력
            self.log(f"🔑 기본상품명{i} → {basic_name}", level=level, also_to_report=also_to_report)
            self.log(f"    - 가공상품명 -> {processed_name}", level=level, also_to_report=also_to_report)

        if separator == "2line":
            self.log_separator(char="=", level=level, also_to_report=also_to_report)
        elif separator == "dash-2line":
            self.log_separator(char="-", level=level, also_to_report=also_to_report)



