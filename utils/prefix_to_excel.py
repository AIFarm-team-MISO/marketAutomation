import os
import xlrd
import xlwt


import os
import xlrd
import xlwt
import datetime
import gc

def remove_rows_with_value_in_column(file_path, file_name, column_name, target_value):
    """
    엑셀 파일에서 특정 열의 값이 target_value인 행을 삭제하고 새로운 파일로 저장합니다.

    이 함수는 다음과 같은 경우에 유용합니다:
    1. 데이터 클린징: 엑셀 파일에서 불필요하거나 조건에 맞지 않는 데이터를 제거.
    2. 대량 데이터 처리: 조건에 따라 행을 제거하여 데이터를 효율적으로 필터링.
    3. 데이터 유효성 확보: 특정 조건을 만족하지 않는 데이터를 배제하여 데이터 품질 향상.

    Parameters:
    - file_path (str): 원본 엑셀 파일이 위치한 디렉토리 경로.
        예: "C:/data"
    - file_name (str): 원본 엑셀 파일의 이름.
        예: "input_file.xls"
    - column_name (str): 값을 검사할 열 이름.
        예: "필터링결과"
    - target_value (str): 삭제 조건이 되는 열 값.
        예: "중복-문자있음"

    Returns:
    - None: 결과는 지정된 경로에 저장되며, 함수는 값을 반환하지 않습니다.
    
    주요 기능:
    - 헤더를 기준으로 특정 열(column_name)을 식별하여 해당 열의 값이 target_value인 모든 행(row)을 제거.
    - 제거된 데이터를 새로운 파일(output_file_path)에 저장.
    - 작업이 완료된 후 리소스(파일 핸들 등)를 해제하여 메모리 누수 방지.
    
    주의:
    - file_path는 반드시 디렉토리여야 하며, file_name에는 파일 이름과 확장자가 포함되어야 합니다.
    - column_name이 엑셀 파일의 헤더에 포함되어 있어야 합니다.
    - xlrd 및 xlwt 라이브러리를 사용하며, .xls 형식의 엑셀 파일만 지원합니다.
    """
    try:
        # 경로 유효성 검사
        if not os.path.isdir(file_path):
            raise ValueError(f"file_path가 디렉토리가 아닙니다: {file_path}")

        # 출력 파일 경로 생성
        output_file_path = os.path.join(file_path, f"{file_name}_output.xls")
        if os.path.isdir(output_file_path):
            output_file_path = os.path.join(output_file_path, "default_output.xls")

        # 기존 파일 읽기
        workbook = xlrd.open_workbook(os.path.join(file_path, file_name), formatting_info=True)
        writable_book = xlwt.Workbook()

        for sheet_idx in range(workbook.nsheets):
            sheet = workbook.sheet_by_index(sheet_idx)
            writable_sheet = writable_book.add_sheet(sheet.name)

            # 헤더에서 열 이름 찾기
            if sheet.nrows == 0:
                raise ValueError("엑셀 파일이 비어 있습니다.")
            header_row = sheet.row_values(0)
            if column_name not in header_row:
                raise ValueError(f"열 '{column_name}'을(를) 찾을 수 없습니다.")

            column_index = header_row.index(column_name)
            new_row_idx = 0

            for row_idx in range(sheet.nrows):
                cell_value = sheet.cell_value(row_idx, column_index)

                # 조건에 따라 행 삭제
                if row_idx > 0 and cell_value == target_value:  # 첫 번째 행(헤더)은 유지
                    continue

                # 해당 행을 새 시트에 복사
                for col_idx in range(sheet.ncols):
                    writable_sheet.write(new_row_idx, col_idx, sheet.cell_value(row_idx, col_idx))

                new_row_idx += 1

            print(f"시트 '{sheet.name}' 처리 완료, 최종 행 수: {new_row_idx}")

        # 결과 파일 저장
        writable_book.save(output_file_path)
        print(f"파일 저장 완료: {output_file_path}")

    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {file_path}")
    except ValueError as ve:
        print(f"유효하지 않은 열 이름: {ve}")
    except Exception as e:
        print(f"예기치 않은 오류 발생: {e}")
    finally:
        # 리소스 해제
        try:
            workbook.release_resources()
            del workbook
        except:
            pass
        del writable_book
        gc.collect()
        print("📁 리소스 해제 완료.")




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

import re
def remove_duplicates_in_column(cell_value):
    """
    AQ 열의 문자열에서 중복된 키워드를 제거하고, 29바이트 내외로 조정하며 숫자 및 특수문자를 필터링합니다.

    Parameters:
    - cell_value: AQ 열의 기존 값 (쉼표로 구분된 문자열).

    Returns:
    - cell_value: 중복 키워드가 제거되고, 숫자 및 특수문자가 제거된 쉼표로 구분된 문자열로 29바이트 내외로 조정된 값.
    """
    if isinstance(cell_value, str):
        # 1. 중복 제거 및 순서 유지
        keywords = cell_value.split(',')
        unique_keywords = list(dict.fromkeys(keywords))
        
        # 2. 숫자 및 특수문자 필터링
        filtered_keywords = [re.sub(r'[^\w가-힣]', '', keyword) for keyword in unique_keywords]
        filtered_keywords = [keyword for keyword in filtered_keywords if not keyword.isdigit()]  # 숫자 제거
        
        # 3. 29바이트 내외로 조정
        result = []
        current_length = 0
        for keyword in filtered_keywords:
            byte_length = len(keyword.encode('utf-8'))  # UTF-8 기준 바이트 계산
            if current_length + byte_length + (1 if result else 0) <= 29:  # 쉼표 추가 고려
                result.append(keyword)
                current_length += byte_length + (1 if result else 0)
            else:
                break
        
        return ','.join(result)
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



def process_add_prefix_to_excel_in_folder_with_sheets(folder_path, file_name, column_letter, prefix):
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

                        # C 열 처리 (접두사와 사용자 정의 문자열 설정)(폴더명 추가)
                        if col_idx == column_indices.get("C") and row_idx >= 2:  # 3번째 행부터 처리
                            cell_value = set_column_to_custom_string(prefix, "도매토피아")

                        # B 열 처리 (접두사 추가)
                        if col_idx == column_indices.get("B") and row_idx >= 2:  # 3번째 행부터 처리
                            cell_value = add_prefix_to_column(cell_value, prefix)

                        # G 열 처리 (상수 값 설정)
                        if col_idx == column_indices.get("G") and row_idx >= 2:  # 3번째 행부터 처리
                            cell_value = set_column_to_constant(cell_value, 9999)

                        # F 열 처리 (가격 조정 : 현재 5프로 다운 )
                        if col_idx == column_indices.get("F") and row_idx >= 2:  # 3번째 행부터 처리
                            cell_value = adjust_column_value(cell_value, adjustment_percentage=30, increase=False)

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

# 식품관련 이셀러스 카테고리 
delete_numbers =[401303000, 400907000, 610811000, 140402000, 400802000, 401508000, 141504000, 560703000, 401211000, 140105000, 560109000, 140401000, 610907000, 560406000, 322801000, 561506000, 400708000, 140905000, 402613000, 561403000, 401003000, 141012000, 561604000, 610407000, 201004000, 402616000, 401301000, 402305000, 561005000, 610805000, 610501000, 610403000, 320103000, 141007000, 402102000, 200806000, 320206000, 141010000, 610807000, 200805000, 401206000, 401002000, 141102000, 402633000, 560110000, 610812000, 560606000, 561305000, 141303000, 401202000, 402208000, 562004000, 560203000, 141503000, 201402000, 560401000, 610503000, 401802000, 402629000, 560407000, 611302000, 140601000, 400504000, 561804000, 560607000, 560402000, 400811000, 141002000, 402503000, 201002000, 321804000, 611103000, 402623000, 610904000, 402106000, 140102000, 560206000, 560506000, 560408000, 402009000, 561306000, 611305000, 400903000, 401503000, 140205000, 402506000, 201001000, 401006000, 402007000, 402113000, 401013000, 402215000, 560403000, 401212000, 402210000, 402112000, 402217000, 401009000, 561805000, 240209000, 562001000, 401207000, 561201000, 321202000, 610708000, 140403000, 400804000, 240104000, 140604000, 141403000, 402301000, 402004000, 611101000, 141304000, 400102000, 402213000, 560304000, 562204000, 200803000, 141001000, 402406000, 402501000, 402303000, 610402000, 400404000, 140511003, 141603000, 200905000, 201401000, 400707000, 560102000, 401902000, 402115000, 
402508000, 140607002, 560604000, 140406000, 400509000, 560210000, 561202000, 611306000, 200901000, 610601000, 400709000, 561401000, 321306000, 400204000, 402114000, 561801000, 401904000, 400713000, 140304000, 402703000, 560404000, 140906000, 140404000, 401903000, 140202000, 610704000, 400409000, 140803000, 402606000, 141702000, 402005000, 141011000, 402635000, 240103000, 401505000, 561207000, 401805000, 610203000, 400306000, 140607003, 141601000, 400410000, 611003000, 402110000, 401603000, 560505000, 561505000, 561706000, 402003000, 401203000, 400901000, 201003000, 560303000, 560803000, 201503000, 402204000, 560103000, 141003000, 400910000, 401504000, 140608000, 400505000, 401509000, 401601000, 560702000, 401004000, 562102000, 560907000, 562111000, 400914000, 140102002, 402601000, 400908000, 561208000, 321303000, 402701000, 560804000, 400911000, 561501000, 561103000, 610504000, 610809000, 401402000, 320102000, 402609000, 400401000, 561302000, 610604000, 140702000, 402603000, 402634000, 400602000, 561013000, 140508002, 401008000, 400202000, 402621000, 402201000, 140206000, 141204000, 400205000, 402107000, 561004000, 561309000, 560302000, 401507000, 561407000, 562112000, 140101002, 402212000, 611201000, 321205000, 611203000, 610302000, 201102000, 401804000, 561011000, 401005000, 401012000, 140902000, 400103000, 401704000, 561402000, 560501000, 322806000, 610701000, 400307000, 401803000, 400201000, 401213000, 402209000, 400806000, 140201000, 
140606000, 561602000, 201504000, 140705000, 610906000, 401305000, 401404000, 402307000, 401209000, 610903000, 402306000, 402002000, 402105000, 401007000, 560208000, 400805000, 401501000, 561707000, 402622000, 201403000, 561205000, 402604000, 570101000, 560104000, 400812000, 400606000, 402203000, 402638000, 560107000, 560504000, 610201000, 141502000, 401705000, 560410000, 560205000, 560405000, 201101000, 562110000, 400308000, 561705000, 561709000, 611301000, 402614000, 402702000, 141101000, 402507000, 610409000, 321203000, 402010000, 402602000, 562104000, 610804000, 400407000, 560701000, 562103000, 400507000, 240212000, 561203000, 610408000, 561007000, 402505000, 320104000, 141302000, 402607000, 561901000, 400904000, 402103000, 562201000, 141701000, 562101000, 610101000, 240105000, 141006000, 560802000, 561904000, 141604000, 140101000, 560201000, 141203000, 402610000, 561905000, 401104000, 401010000, 560909000, 562203000, 401102000, 561605000, 400808000, 402620000, 562005000, 401302000, 611307000, 560908000, 562108000, 611207000, 320202000, 560805000, 321801000, 402214000, 401105000, 320204000, 610901000, 560503000, 140903000, 322804000, 561015000, 400801000, 401101000, 320207000, 610801000, 201103000, 140801000, 610702000, 610707000, 141501000, 562109000, 560901000, 240208000, 401801000, 562106000, 140904000, 240101000, 140511001, 201202000, 240107001, 560111000, 562002000, 201404000, 321301000, 402104000, 400301000, 560601000, 560605000, 
561002000, 201501000, 140510000, 400406000, 402509000, 201201000, 320101000, 140605000, 401306000, 400712000, 401701000, 610102000, 402704000, 610404000, 402625000, 201304000, 561504000, 561503000, 610703000, 611303000, 560301000, 561003000, 610502000, 560204000, 560602000, 200902000, 321204000, 402006000, 140511002, 402402000, 610910000, 561204000, 561405000, 240107002, 400905000, 400601000, 200804000, 140203000, 141602000, 400508000, 402302000, 140602000, 610705000, 321302000, 402502000, 401001000, 610401000, 140701000, 140204000, 140104000, 402101000, 561101000, 560809000, 561001000, 401502000, 611205000, 562202000, 562003000, 561703000, 322803000, 320201000, 400403000, 561304000, 400203000, 400603000, 140407000, 561406000, 321803000, 401602000, 561012000, 561903000, 321305000, 561601000, 400411000, 402637000, 611104000, 402618000, 400807000, 562006000, 141004000, 560105000, 140802000, 402626000, 400304000, 320205000, 561809000, 402605000, 561303000, 561802000, 401210000, 610202000, 400502000, 201301000, 610405000, 400701000, 610104000, 321201000, 402109000, 400809000, 560207000, 141202000, 402612000, 401403000, 610806000, 400503000, 402630000, 561702000, 200906000, 402608000, 611208000, 610905000, 560409000, 561701000, 400710000, 140101001, 240210002, 140703000, 320105000, 560904000, 562107000, 610802000, 140508001, 560101000, 561010000, 400716000, 611102000, 562205000, 400105000, 400302000, 402619000, 401205000, 402636000, 561807000, 
560112000, 140301000, 610810000, 400402000, 240211000, 402627000, 140103000, 141301000, 402108000, 400912000, 610105000, 561803000, 321802000, 560806000, 560902000, 610303000, 561404000, 610709000, 240210001, 402504000, 402211000, 400206000, 400305000, 610304000, 400902000, 201302000, 322805000, 561808000, 401304000, 402617000, 400506000, 561301000, 570102000, 322901000, 400405000, 561902000, 400715000, 400916000, 610301000, 201502000, 560603000, 561014000, 400706000, 611001000, 200801000, 400501000, 401201000, 400909000, 560106000, 561307000, 402207000, 402624000, 562105000, 610505000, 562007000, 611002000, 400714000, 400408000, 400309000, 400915000, 320203000, 402628000, 402205000, 610106000, 140305000, 402403000, 561704000, 610602000, 140405000, 560903000, 610908000, 402401000, 240102000, 400104000, 611206000, 141401000, 561008000, 140102001, 401208000, 141205000, 140704000, 401506000, 610603000, 401107000, 610902000, 402216000, 401011000, 200802000, 400101000, 560209000, 610410000, 400705000, 201303000, 561206000, 560906000, 140804000, 561502000, 402202000, 400711000, 201405000, 610803000, 400303000, 320208000, 560502000, 401901000, 402008000, 402111000, 610813000, 321307000, 402206000, 560305000, 611304000, 402304000, 611202000, 200903000, 402404000, 321805000, 323102000, 561603000, 141005000, 561006000, 561311000, 610103000, 141402000, 610406000, 402631000, 140303000, 140603000, 560608000, 322802000, 401204000, 402405000, 401707000, 
140607001, 401604000, 401401000, 400913000, 400810000, 610808000, 401703000, 140302000, 400605000, 560808000, 201005000, 561708000, 610706000, 610909000, 323001000, 400906000, 321304000, 400703000, 401106000, 400702000, 402611000, 561104000, 141009000, 402632000, 560108000, 561009000, 401706000, 140106000, 400704000, 561102000, 401702000, 611204000, 561806000, 200904000, 140509000, 560910000, 401103000, 402001000, 402615000, 400604000, 141201000, 561308000, 560807000, 140901000, 560202000, 400803000, 560905000, 141008000, 561310000, 402705000, 240106000, 560801000]



