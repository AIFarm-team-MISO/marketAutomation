import os
import xlrd
import xlwt

def read_excel_file(file_path):
    """
    엑셀 파일을 읽고, xlrd의 Workbook 객체를 반환합니다.

    Parameters:
    - file_path (str): 읽을 엑셀 파일 경로.

    Returns:
    - workbook (xlrd.book.Book): xlrd Workbook 객체.
    """
    try:
        workbook = xlrd.open_workbook(file_path, formatting_info=True)
        return workbook
    except Exception as e:
        print(f"오류 발생 (파일 읽기 실패): {e}")
        return None

def save_excel_file(writable_book, output_file_path):
    """
    엑셀 파일을 저장합니다.

    Parameters:
    - writable_book (xlwt.Workbook): 작성된 xlwt Workbook 객체.
    - output_file_path (str): 저장할 파일 경로.
    """
    try:
        writable_book.save(output_file_path)
        print(f"엑셀 파일 저장 완료: {output_file_path}")
    except Exception as e:
        print(f"오류 발생 (파일 저장 실패): {e}")

def add_prefix_to_column(cell_value, prefix):
    """
    B 열의 값에 접두사를 추가합니다.

    Parameters:
    - cell_value: 현재 셀 값.
    - prefix (str): 추가할 접두사 문자열.

    Returns:
    - cell_value: 수정된 셀 값.
    """
    if isinstance(cell_value, float):  # 소수점 있는 숫자 처리
        cell_value = str(int(cell_value))
    return f"{prefix}{cell_value}" if cell_value else cell_value

def set_column_to_constant(cell_value, constant_value):
    """
    G 열 값을 상수 값으로 설정합니다.

    Parameters:
    - cell_value: 현재 셀 값 (무시됨).
    - constant_value: 설정할 상수 값.

    Returns:
    - constant_value: 수정된 셀 값.
    """
    return constant_value

def adjust_column_value(cell_value, adjustment_percentage, increase=True):
    """
    F 열의 숫자 값을 주어진 비율만큼 조정하고, 소수점을 제거한 뒤 마지막 자릿수를 0으로 만듭니다.

    Parameters:
    - cell_value: 현재 셀 값.
    - adjustment_percentage (float): 조정할 비율.
    - increase (bool): True면 증가, False면 감소.

    Returns:
    - cell_value: 수정된 셀 값.
    """
    if isinstance(cell_value, (int, float)):  # 숫자 값만 처리
        # 1. 비율에 따라 값 조정
        adjustment = cell_value * (adjustment_percentage / 100)
        adjusted_value = cell_value + adjustment if increase else cell_value - adjustment

        # 2. 소수점 제거 (반올림)
        rounded_value = round(adjusted_value)

        # 3. 마지막 자릿수가 0이 아니면 반올림
        last_digit = rounded_value % 10
        if last_digit != 0:
            rounded_value = round(rounded_value / 10) * 10

        return rounded_value

    return cell_value  # 숫자가 아니면 원래 값을 반환

def set_column_to_custom_string(prefix, custom_string):
    """
    C 열의 값을 접두사와 사용자 정의 문자열로 설정합니다.

    Parameters:
    - prefix (str): 접두사 문자열.
    - custom_string (str): 추가할 사용자 정의 문자열.

    Returns:
    - cell_value: 수정된 셀 값.
    """
    return f"{prefix}{custom_string}"

def swap_columns_values(m_value, o_value):
    """
    M 열의 값을 O 열의 값으로 교체합니다. O 열이 비어 있으면 기존 M 값을 유지합니다.

    Parameters:
    - m_value: M 열의 기존 값.
    - o_value: O 열의 값.

    Returns:
    - m_value 또는 o_value: O 열 값이 비어 있으면 기존 M 값을 유지.
    """
    return o_value if o_value else m_value

def remove_duplicates_in_column(cell_value):
    """
    AQ 열의 문자열에서 중복된 키워드를 제거합니다.

    Parameters:
    - cell_value: AQ 열의 기존 값 (쉼표로 구분된 문자열).

    Returns:
    - cell_value: 중복 키워드가 제거된 쉼표로 구분된 문자열.
    """
    if isinstance(cell_value, str):
        keywords = cell_value.split(',')
        unique_keywords = list(dict.fromkeys(keywords))  # 중복 제거 및 순서 유지
        return ','.join(unique_keywords)
    return cell_value

def set_column_to_value(cell_value, new_value):
    """
    특정 열의 값을 고정된 값으로 설정합니다.

    Parameters:
    - cell_value: 현재 셀 값 (무시됨).
    - new_value: 설정할 고정된 값.

    Returns:
    - new_value: 고정된 값.
    """
    return new_value

# 열 필터링 함수
def filter_column_values(dataframe, column_name, values_to_remove):
    """
    특정 열에서 지정된 값을 제거하는 함수.

    Args:
        dataframe (pd.DataFrame): 처리할 데이터프레임
        column_name (str): 처리할 열 이름
        values_to_remove (list): 제거할 값 목록

    Returns:
        pd.DataFrame: 값이 제거된 데이터프레임
    """
    if column_name in dataframe.columns:
        return dataframe[~dataframe[column_name].astype(str).isin(values_to_remove)]
    return dataframe



def process_add_prefix_to_excel_in_folder_with_sheets(folder_path, column_letter, prefix):
    """
    현재 폴더에 있는 모든 .xls 파일을 대상으로 특정 열의 값에 접두사를 추가하며,
    기존 파일의 모든 탭 이름을 유지. 추가로 비어있는 D 열의 행 삭제 및 G 열 값을 9999로 변경.

    Parameters:
    - folder_path (str): 엑셀 파일들이 위치한 폴더 경로.
    - column_letter (str): 접두사를 추가할 열의 열 문자 (예: 'B').
    - prefix (str): 추가할 접두사 문자열.

    Returns:
    - list: 생성된 결과 파일 경로 목록.
    """
    try:
        # 1. 현재 폴더 내의 모든 .xls 파일 가져오기
        xls_files = [f for f in os.listdir(folder_path) if f.endswith(".xls")]
        if not xls_files:
            raise FileNotFoundError("현재 폴더에 .xls 파일이 존재하지 않습니다.")

        output_files = []

        for file_name in xls_files:
            input_file_path = os.path.join(folder_path, file_name)
            base_name, ext = os.path.splitext(file_name)
            output_file_path = os.path.join(folder_path, f"{base_name}_processed{ext}")

            # 2. 기존 .xls 파일 읽기
            workbook = read_excel_file(input_file_path)
            if not workbook:
                continue

            writable_book = xlwt.Workbook()

            # 3. 각 시트 복사 및 수정
            for sheet_idx in range(workbook.nsheets):
                sheet = workbook.sheet_by_index(sheet_idx)
                writable_sheet = writable_book.add_sheet(sheet.name)

                # 열 문자 → 열 인덱스 변환
                column_indices = {
                    "B": column_letter_to_index(column_letter),
                    "G": column_letter_to_index("G"),
                    "F": column_letter_to_index("F"),
                    "C": column_letter_to_index("C"),
                    "D": column_letter_to_index("D"), 
                    "E": column_letter_to_index("E"),
                    "AQ": column_letter_to_index("AQ"), # 검색어(태그)
                    "AT": column_letter_to_index("AT"), # 요약정보 전항목 상세설명 참조
                    "M": column_letter_to_index("M"),   # 목록이미지
                    "O": column_letter_to_index("O")    # 이미지2
                    
                }

                new_row_idx = 0  # 새로 작성할 행의 인덱스
                seen_e_values = set()  # E 열 값 추적을 위한 집합

                for row_idx in range(sheet.nrows):
                    # D 열 값 체크 및 삭제 조건
                    cell_value_d = sheet.cell_value(row_idx, column_indices["D"])
                    # D 열 값이 없거나 delete_numbers의 숫자와 일치하는 경우 삭제
                    try:
                        cell_value_d_numeric = float(cell_value_d)  # >> D 값을 숫자로 변환
                    except ValueError:
                        cell_value_d_numeric = None  # 변환 실패 시 None 처리

                    if row_idx >= 2 and (cell_value_d_numeric is None or cell_value_d_numeric in delete_numbers):
                        continue  # 행 건너뛰기


                    # E 열 중복 체크 (첫 번째 값은 유지, 이후 값은 삭제)
                    cell_value_e = sheet.cell_value(row_idx, column_indices["E"])
                    if row_idx >= 2 and cell_value_e in seen_e_values:
                        continue  # 중복된 경우 행 건너뛰기
                    seen_e_values.add(cell_value_e)  # 중복되지 않은 경우 추가


                    for col_idx in range(sheet.ncols):
                        cell_value = sheet.cell_value(row_idx, col_idx)

                        # C 열 처리 (접두사와 사용자 정의 문자열 설정)
                        if col_idx == column_indices.get("C") and row_idx >= 2:  # 3번째 행부터 처리
                            cell_value = set_column_to_custom_string(prefix, "도매토피아")

                        # B 열 처리 (접두사 추가)
                        if col_idx == column_indices.get("B") and row_idx >= 2:  # 3번째 행부터 처리
                            cell_value = add_prefix_to_column(cell_value, prefix)

                        # G 열 처리 (상수 값 설정)
                        if col_idx == column_indices.get("G") and row_idx >= 2:  # 3번째 행부터 처리
                            cell_value = set_column_to_constant(cell_value, 9999)

                        # F 열 처리 (가격 조정)
                        if col_idx == column_indices.get("F") and row_idx >= 2:  # 3번째 행부터 처리
                            cell_value = adjust_column_value(cell_value, adjustment_percentage=1, increase=False)

                        # M 열 처리 (O 열 값으로 교체)
                        if col_idx == column_indices.get("M") and row_idx >= 2:  # 3번째 행부터 처리
                            o_value = sheet.cell_value(row_idx, column_indices.get("O"))
                            cell_value = swap_columns_values(cell_value, o_value)

                        # AQ 열 처리 (중복 키워드 제거)
                        if col_idx == column_indices.get("AQ") and row_idx >= 2:  # 3번째 행부터 처리
                            cell_value = remove_duplicates_in_column(cell_value)

                        if col_idx == column_indices.get("AT") and row_idx >= 2:  # 3번째 행부터 처리
                            cell_value = set_column_to_value(cell_value, "Y")
                        

                        writable_sheet.write(new_row_idx, col_idx, cell_value)

                    new_row_idx += 1

                print(f"시트 '{sheet.name}' 처리 완료.")

            # 결과 파일 저장
            save_excel_file(writable_book, output_file_path)
            output_files.append(output_file_path)

        print("모든 파일 처리 완료.")
        return output_files

    except Exception as e:
        print(f"오류 발생: {e}")
        return None

def column_letter_to_index(letter):
    """
    열 문자를 열 인덱스로 변환 (예: 'A' → 0, 'B' → 1, ..., 'AA' → 26, 'AQ' → 42).
    """
    letter = letter.upper()
    index = 0
    for char in letter:
        index = index * 26 + (ord(char) - ord('A') + 1)
    return index - 1  # 인덱스는 0부터 시작

delete_numbers = [140101000, 140101001, 140101002, 140102000, 140102001, 140102002, 140103000, 140104000, 140105000, 140106000, 140201000, 140202000, 
140203000, 140204000, 140205000, 140206000, 140301000, 140302000, 140303000, 140304000, 140305000, 140401000, 140402000, 140403000, 
140404000, 140405000, 140406000, 140407000, 140508001, 140508002, 140509000, 140510000, 140511001, 140511002, 140511003, 140601000, 
140602000, 140603000, 140604000, 140605000, 140606000, 140607001, 140607002, 140607003, 140608000, 140701000, 140702000, 140703000, 
140704000, 140705000, 140801000, 140802000, 140803000, 140804000, 140901000, 140902000, 140903000, 140904000, 140905000, 140906000, 
141001000, 141002000, 141003000, 141004000, 141005000, 141006000, 141007000, 141008000, 141009000, 141010000, 141011000, 141012000, 
141101000, 141102000, 141201000, 141202000, 141203000, 141204000, 141205000, 141301000, 141302000, 141303000, 141304000, 141401000, 
141402000, 141403000, 141501000, 141502000, 141503000, 141504000, 141601000, 141602000, 141603000, 141604000, 141701000, 141702000, 
400101000, 400102000, 400103000, 400104000, 400105000, 400201000, 400202000, 400203000, 400204000, 400205000, 400206000, 400301000, 
400302000, 400303000, 400304000, 400305000, 400306000, 400307000, 400308000, 400309000, 400401000, 400402000, 400403000, 400404000, 
400405000, 400406000, 400407000, 400408000, 400409000, 400410000, 400411000, 400501000, 400502000, 400503000, 400504000, 400505000, 
400506000, 400507000, 400508000, 400509000, 400601000, 400602000, 400603000, 400604000, 400605000, 400606000, 400701000, 400702000, 
400703000, 400704000, 400705000, 400706000, 400707000, 400708000, 400709000, 400710000, 400711000, 400712000, 400713000, 400714000, 
400715000, 400716000, 400801000, 400802000, 400803000, 400804000, 400805000, 400806000, 400807000, 400808000, 400809000, 400810000, 
400811000, 400812000, 400901000, 400902000, 400903000, 400904000, 400905000, 400906000, 400907000, 400908000, 400909000, 400910000, 
400911000, 400912000, 400913000, 400914000, 400915000, 400916000, 401001000, 401002000, 401003000, 401004000, 401005000, 401006000, 
401007000, 401008000, 401009000, 401010000, 401011000, 401012000, 401013000, 401101000, 401102000, 401103000, 401104000, 401105000, 
401106000, 401107000, 401201000, 401202000, 401203000, 401204000, 401205000, 401206000, 401207000, 401208000, 401209000, 401210000, 
401211000, 401212000, 401213000, 401301000, 401302000, 401303000, 401304000, 401305000, 401306000, 401401000, 401402000, 401403000, 
401404000, 401501000, 401502000, 401503000, 401504000, 401505000, 401506000, 401507000, 401508000, 401509000, 401601000, 401602000, 
401603000, 401604000, 401701000, 401702000, 401703000, 401704000, 401705000, 401706000, 401707000, 401801000, 401802000, 401803000, 
401804000, 401805000, 401901000, 401902000, 401903000, 401904000, 402001000, 402002000, 402003000, 402004000, 402005000, 402006000, 
402007000, 402008000, 402009000, 402010000, 402101000, 402102000, 402103000, 402104000, 402105000, 402106000, 402107000, 402108000, 
402109000, 402110000, 402111000, 402112000, 402113000, 402114000, 402115000, 402201000, 402202000, 402203000, 402204000, 402205000, 
402206000, 402207000, 402208000, 402209000, 402210000, 402211000, 402212000, 402213000, 402214000, 402215000, 402216000, 402217000, 
402301000, 402302000, 402303000, 402304000, 402305000, 402306000, 402307000, 402401000, 402402000, 402403000, 402404000, 402405000, 
402406000, 402501000, 402502000, 402503000, 402504000, 402505000, 402506000, 402507000, 402508000, 402509000, 402601000, 402602000, 
402603000, 402604000, 402605000, 402606000, 402607000, 402608000, 402609000, 402610000, 402611000, 402612000, 402613000, 402614000, 
402615000, 402616000, 402617000, 402618000, 402619000, 402620000, 402621000, 402622000, 402623000, 402624000, 402625000, 402626000, 
402627000, 402628000, 402629000, 402630000, 402631000, 402632000, 402633000, 402634000, 402635000, 402636000, 402637000, 402638000, 
402701000, 402702000, 402703000, 402704000, 402705000, 560101000, 560102000, 560103000, 560104000, 560105000, 560106000, 560107000, 
560108000, 560109000, 560110000, 560111000, 560112000, 560201000, 560202000, 560203000, 560204000, 560205000, 560206000, 560207000, 
560208000, 560209000, 560210000, 560301000, 560302000, 560303000, 560304000, 560305000, 560401000, 560402000, 560403000, 560404000, 
560405000, 560406000, 560407000, 560408000, 560409000, 560410000, 560501000, 560502000, 560503000, 560504000, 560505000, 560506000, 
560601000, 560602000, 560603000, 560604000, 560605000, 560606000, 560607000, 560608000, 560701000, 560702000, 560703000, 560801000, 
560802000, 560803000, 560804000, 560805000, 560806000, 560807000, 560808000, 560809000, 560901000, 560902000, 560903000, 560904000, 
560905000, 560906000, 560907000, 560908000, 560909000, 560910000, 561001000, 561002000, 561003000, 561004000, 561005000, 561006000, 
561007000, 561008000, 561009000, 561010000, 561011000, 561012000, 561013000, 561014000, 561015000, 561101000, 561102000, 561103000, 
561104000, 561201000, 561202000, 561203000, 561204000, 561205000, 561206000, 561207000, 561208000, 561301000, 561302000, 561303000, 
561304000, 561305000, 561306000, 561307000, 561308000, 561309000, 561310000, 561311000, 561401000, 561402000, 561403000, 561404000, 
561405000, 561406000, 561407000, 561501000, 561502000, 561503000, 561504000, 561505000, 561506000, 561601000, 561602000, 561603000, 
561604000, 561605000, 561701000, 561702000, 561703000, 561704000, 561705000, 561706000, 561707000, 561708000, 561709000, 561801000, 
561802000, 561803000, 561804000, 561805000, 561806000, 561807000, 561808000, 561809000, 561901000, 561902000, 561903000, 561904000, 
561905000, 562001000, 562002000, 562003000, 562004000, 562005000, 562006000, 562007000, 562101000, 562102000, 562103000, 562104000, 
562105000, 562106000, 562107000, 562108000, 562109000, 562110000, 562111000, 562112000, 562201000, 562202000, 562203000, 562204000, 
562205000, 610101000, 610102000, 610103000, 610104000, 610105000, 610106000, 610201000, 610202000, 610203000, 610301000, 610302000, 
610303000, 610304000, 610401000, 610402000, 610403000, 610404000, 610405000, 610406000, 610407000, 610408000, 610409000, 610410000, 
610501000, 610502000, 610503000, 610504000, 610505000, 610601000, 610602000, 610603000, 610604000, 610701000, 610702000, 610703000, 
610704000, 610705000, 610706000, 610707000, 610708000, 610709000, 610801000, 610802000, 610803000, 610804000, 610805000, 610806000, 
610807000, 610808000, 610809000, 610810000, 610811000, 610812000, 610813000, 610901000, 610902000, 610903000, 610904000, 610905000, 
610906000, 610907000, 610908000, 610909000, 610910000, 611001000, 611002000, 611003000, 611101000, 611102000, 611103000, 611104000, 
611201000, 611202000, 611203000, 611204000, 611205000, 611206000, 611207000, 611208000, 611301000, 611302000, 611303000, 611304000, 
611305000, 611306000, 611307000]
