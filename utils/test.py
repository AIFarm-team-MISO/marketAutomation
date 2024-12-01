import ssl
import requests
from urllib3 import PoolManager
from requests.adapters import HTTPAdapter


class CustomSSLAdapter(HTTPAdapter):
    """Diffie-Hellman 키 문제 우회를 위한 SSL 설정"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        # 보안 수준 완화
        ctx = ssl.create_default_context()
        ctx.check_hostname = False  # 호스트 검증 비활성화
        ctx.verify_mode = ssl.CERT_NONE  # 인증서 검증 비활성화
        ctx.set_ciphers("DEFAULT:@SECLEVEL=1")  # 낮은 보안 수준 허용
        pool_kwargs['ssl_context'] = ctx
        return PoolManager(num_pools=connections, maxsize=maxsize, block=block, **pool_kwargs)



# HTTPS 세션 생성 및 어댑터 설정
session = requests.Session()
session.mount("https://", CustomSSLAdapter())

def download_image(image_url):
    try:
        response = session.get(image_url, timeout=10)
        if response.status_code == 200:
            print("이미지 다운로드 성공!")
            return response.content
        else:
            print(f"Failed to download {image_url}, Status Code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error downloading {image_url}: {e}")
        return None


# 테스트 URL
image_url = "http://callenge2000.shopon.biz/data/goods_img/goods_img/1/2024/11/1374317/1_large.JPG"
image_data = download_image(image_url)

if image_data:
    with open("downloaded_image.jpg", "wb") as f:
        f.write(image_data)
else:
    print("이미지 다운로드 실패!")
