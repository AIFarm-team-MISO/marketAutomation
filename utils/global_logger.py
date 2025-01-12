from utils.log_utils import Logger

# 전역 Logger 객체
logger = Logger(log_file="logs/debug.log", enable_console=True)



# 싱글톤 패턴으로 Logger 객체를 생성 (프로그램이 크거나 Logger 초기화에 추가 설정이 필요한 경우)
# from utils.log_utils import Logger
# 
# class GlobalLogger:
#     _instance = None

#     @staticmethod
#     def get_logger():
#         if GlobalLogger._instance is None:
#             GlobalLogger._instance = Logger(log_file="logs/debug.log", enable_console=True)
#         return GlobalLogger._instance
