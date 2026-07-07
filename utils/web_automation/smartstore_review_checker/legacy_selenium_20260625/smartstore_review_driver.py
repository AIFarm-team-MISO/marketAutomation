# utils/web_automation/smartstore_review_checker/smartstore_review_driver.py

import os

from config.web_automation_settings import WEB_AUTOMATION_DIR
from rotationAuto.driver.driver_init import setup_driver


def create_smartstore_review_driver():
    """
    스마트스토어 공개 상품페이지 리뷰 확인 전용 드라이버를 생성한다.
    """

    download_dir = os.path.join(
        WEB_AUTOMATION_DIR,
        "web_automation_data",
        "downloads",
        "smartstore_review",
    )

    driver = setup_driver(
        profile_name="smartstore_review",
        download_dir=download_dir,
    )

    return driver