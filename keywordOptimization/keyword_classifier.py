def classify_keywords_via_dictionary(main_keyword, other_keywords, dictionary):
    """
    사전 데이터를 사용하여 기타 키워드를 분류하고, 분류되지 않는 키워드는 기타 카테고리에 추가
    
    Parameters:
    - main_keyword (str): 메인 키워드
    - other_keywords (list): 분류할 기타 키워드 목록
    - dictionary (dict): 메인 및 보조 키워드를 포함하는 사전 데이터
    
    Returns:
    - classified_keywords (dict): 분류된 키워드 딕셔너리
    """
    classified_keywords = {'용도': [], '사양': [], '스타일': [], '기타 카테고리': []}
    
    # 메인 키워드에 대한 사전 항목 가져오기
    main_data = dictionary.get(main_keyword, {})
    
    for keyword in other_keywords:
        found = False  # 해당 키워드의 카테고리를 찾았는지 여부
        for category in ['용도', '사양', '스타일']:
            if keyword in main_data.get(category, []):
                classified_keywords[category].append(keyword)
                found = True
                break
        if not found:
            classified_keywords['기타 카테고리'].append(keyword)
    
    # 기타 카테고리에 추가된 키워드를 사전에 업데이트
    if '기타 카테고리' not in main_data:
        main_data['기타 카테고리'] = []
    
    main_data['기타 카테고리'].extend(classified_keywords['기타 카테고리'])
    dictionary[main_keyword] = main_data  # 업데이트된 메인 키워드 정보 반영

    return classified_keywords
