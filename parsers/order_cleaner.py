import pandas as pd
from parsers.option_parser import parse_option

def clean_order_file(input_path: str, output_path: str, option_col_name: str = "옵션정보") -> None:
    """
    발주서 엑셀 파일을 열어 옵션열을 정제하고 저장합니다.
    
    input_path: 원본 엑셀 경로
    output_path: 정제 후 저장할 엑셀 경로
    option_col_name: 옵션이 들어 있는 열 이름 (기본값: '옵션정보')
    """
    # 엑셀 로드
    df = pd.read_excel(input_path)

    if option_col_name not in df.columns:
        raise ValueError(f"'{option_col_name}' 열을 찾을 수 없습니다.")

    # 정제된 옵션 리스트 생성
    cleaned_options = []
    for value in df[option_col_name]:
        if pd.isna(value):
            cleaned_options.append("")
        else:
            parsed = parse_option(str(value))
            cleaned_options.append(" / ".join(parsed))  # 여러 옵션은 / 로 구분

    # 새로운 열 추가
    df["정제옵션"] = cleaned_options

    # 엑셀로 저장
    df.to_excel(output_path, index=False)
    print(f"✅ 정제된 발주서 저장 완료: {output_path}")
