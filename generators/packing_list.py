import pandas as pd
import re
from collections import defaultdict

PACKING_UNIT = {
    "마늘": 1.0,         # 1kg 기준
    "마늘쫑": 1.0,       # 1kg 기준
    "무뼈닭발": 0.2,     # 1팩 = 200g
    "마늘빠삭이": 10.0   # 1박스 = 10개입
}

POSSIBLE_OPTION_COLS = ["옵션", "옵션명", "옵션정보"]

WEIGHT_REGEX = re.compile(r"(\d+(\.\d+)?)\s*(kg|g|팩|개입)", re.IGNORECASE)


def extract_weight_unit(option: str):
    match = WEIGHT_REGEX.search(option)
    if match:
        value, _, unit = match.groups()
        value = float(value)
        if unit.lower() == "g":
            return value / 1000
        elif unit.lower() == "개입":
            return value / 10
        elif unit.lower() == "팩":
            return value * 0.2
        return value
    return 1.0


def get_base_name(option: str) -> str:
    text = option.replace("** 업 소 용 **", "").replace("♣ 육 쪽 ♣", "").replace("* 꼭 지 포 함 *", "")
    text = text.strip()
    for tag in PACKING_UNIT:
        if tag in text:
            return tag
    return text


def get_unit_label(name: str) -> str:
    if name == "무뼈닭발":
        return "팩"
    elif name == "마늘빠삭이":
        return "박스"
    else:
        return "kg"


def generate_packing_list(input_path: str, output_path: str) -> None:
    df = pd.read_excel(input_path)

    option_col = None
    for col in POSSIBLE_OPTION_COLS:
        if col in df.columns:
            option_col = col
            break
    if not option_col:
        raise ValueError("옵션 관련 열이 없습니다.")

    count_col = "수량"
    if count_col not in df.columns:
        raise ValueError("'수량' 열이 없습니다.")

    summary = defaultdict(float)

    for _, row in df.iterrows():
        options = str(row[option_col]).split(" / ")
        count = row[count_col]

        for opt in options:
            name = get_base_name(opt)
            if not name:
                continue
            weight = extract_weight_unit(opt)
            if name in PACKING_UNIT:
                factor = PACKING_UNIT[name]
                if factor != "원시무게사용":
                    total = (weight * count) / factor
                else:
                    total = weight * count
                summary[name] += total

    result_df = pd.DataFrame([
        {"단위": get_unit_label(name), "상품명": name, "수량": round(qty)}
        for name, qty in summary.items()
    ])

    result_df.sort_values(by="상품명", inplace=True)
    result_df.to_excel(output_path, index=False)
    print(f"✅ 패킹리스트 생성 완료: {output_path}")
