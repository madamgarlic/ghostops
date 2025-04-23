import pandas as pd
from parsers.option_parser import parse_option

POSSIBLE_OPTION_COLS = ["옵션", "옵션명", "옵션정보"]

def clean_order_file(input_path: str, output_path: str) -> None:
    """
    발주서 엑셀 파일을 열어 옵션 관련 열을 찾아 정제하고 해당 열에 덮어씁니다.
    """
    df = pd.read_excel(input_path)

    # 정제 대상 열 탐색
    option_col_name = None
    for col in POSSIBLE_OPTION_COLS:
        if col in df.columns:
            option_col_name = col
            break

    if not option_col_name:
        raise ValueError("옵션 관련 열을 찾을 수 없습니다. ('옵션', '옵션명', '옵션정보') 중 하나 필요")

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