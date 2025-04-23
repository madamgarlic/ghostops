import pandas as pd
from parsers.option_parser import parse_option

def clean_order_file(input_path: str, output_path: str, option_col_name: str = "옵션") -> None:
    """
    발주서 엑셀 파일을 열어 옵션열을 정제하고 기존 열을 덮어씁니다.
    원본 엑셀 구조는 유지한 채, 옵션열만 정제된 값으로 교체합니다.
    """
    df = pd.read_excel(input_path)

    if option_col_name not in df.columns:
        raise ValueError(f"'{option_col_name}' 열을 찾을 수 없습니다.")

    new_options = []
    for value in df[option_col_name]:
        if pd.isna(value):
            new_options.append("")
        else:
            parsed = parse_option(str(value))
            new_options.append(" / ".join(parsed))

    df[option_col_name] = new_options
    df.to_excel(output_path, index=False)
    print(f"✅ 정제된 옵션으로 덮어쓰기 완료: {output_path}")
