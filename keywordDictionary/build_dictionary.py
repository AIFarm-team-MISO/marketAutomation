import pandas as pd

def create_initial_dictionary():
    """
    메인 키워드와 보조 키워드(용도, 사양, 스타일)를 포함한 초기 사전을 생성하고
    엑셀 파일로 저장하는 함수입니다.
    """

    # 초기 데이터 설정
    data = {
        "MainKeyword": ["의자", "옷걸이", "선풍기", "텐트"],
        "용도": ["캠핑용", "실내용", "사무용", "아웃도어"],      # 각 메인 키워드의 용도 키워드
        "사양": ["접이식", "경량", "무선", "방수"],              # 각 메인 키워드의 사양 키워드
        "스타일": ["심플", "모던", "미니멀", "빈티지"]            # 각 메인 키워드의 스타일 키워드
    }

    # 데이터프레임 생성
    df = pd.DataFrame(data)

    # 엑셀 파일로 저장
    output_path = "keywordDictionary/dictionary.xlsx"
    df.to_excel(output_path, index=False)
    print(f"사전이 {output_path} 파일로 생성되었습니다.")

# 메인 실행 부분
if __name__ == "__main__":
    create_initial_dictionary()
