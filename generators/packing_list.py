import pandas as pd
import re
from collections import defaultdict

# 단위 기준 정의
PACKING_UNIT = {
    "마늘": 1,           # 1kg
    "마늘쫑": 1,         # 1kg
    "무뼈닭발": 0.2,     # 1팩 = 200g
    "마늘빠삭이": 10,    # 1박스 = 10개입
    "마늘가루": 0.1,     # 100g
    "업소용": "원시무게사용"  # 표기 무게 그대로 사용
}

def extract_weight(text: str) -> float:
    text = text.lower()

    if "kg" in text:
        match = re.search(r"(\d+(\.\d+)?)\s*kg", text)
        if match:
            return float(match.group(1))

    if "g" in text:
        match = re.search(r"(\d+(\.\d+)?)\s*g", text)
        if match:
            return float(match.group(1)) / 1000

    if "개입" in text:
        match = re.search(r"(\d+)개입", text)
        if match:
            return float(match.group(1)) / 10

    if "팩" in text:
        match = re.search(r"(\d+)팩", text)
        if match:
            return float(match.group(1)) * 0.2

    return 1.0

def get_base_product_name(option: str) -> str:
    """
    무게나 수량 제외한 정제 상품명만 반환 (패킹리스트에 표시될 이름)
    """
    return re.sub(r"(\d+(\.\d+)?)(kg|g|개입|팩)", "", option).strip()

def generate_packing_list(input_path: str, output_path: str, option_col: str = "정제옵션", count_col: str = "수량") -> None:
    df = pd.read_excel(input_path)

    if option_col not in df.columns:
        raise ValueError(f"'{option_col}' 열이 없습니다.")
    if count_col not in df.columns:
        raise ValueError(f"'{count_col}' 열이 없습니다.")

    summary = defaultdict(float)

    for i, row in df.iterrows():
        options = str(row[option_col]).split(" / ")
        count = row[count_col]

        for opt in options:
            name = get_base_product_name(opt)
            unit = 1.0

            if "** 업 소 용 **" in opt:
                unit = extract_weight(opt)  # 원시무게 사용
            else:
                for keyword, factor in PACKING_UNIT.items():
                    if keyword in opt and isinstance(factor, (int, float)):
                        unit = extract_weight(opt) / factor
                        break

            summary[name] += count * unit

    out_df = pd.DataFrame([
        {"단위": "EA", "상품명": name, "수량": round(qty)}
        for name, qty in summary.items()
    ])

    out_df.to_excel(output_path, index=False)
    print(f"✅ 패킹리스트 저장 완료: {output_path}")
