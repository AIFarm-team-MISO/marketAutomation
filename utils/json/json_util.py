from utils.global_logger import logger

import json
import pandas as pd

def load_config(config_file):
    """
    JSON 설정 파일을 로드합니다.
    :param config_file: JSON 파일 경로
    :return: 설정 데이터 딕셔너리
    """
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.log(f"⚠️ 설정 파일 로드 중 에러 발생: {e}", level="ERROR")
        raise





