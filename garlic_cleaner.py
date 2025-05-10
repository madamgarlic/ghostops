import re

# 공통 정제 규칙
def clean_text(text: str) -> str:
    # 괄호 제거 (내용은 유지)
    text = re.sub(r"[()]", "", text)
    # 특수문자 정리
    return text.strip()

# 괄호 내 무게정보 삭제 (총400g 등)
def remove_weight_in_parentheses(text: str) -> str:
    return re.sub(r"\(총\s*\d+(\.\d+)?\s*(kg|g|개|팩)\)", "", text)

# + 단위 합산 (1kg + 1kg → 2kg 등)
def extract_total_unit(text: str, unit: str, weight_per_unit: float = 1.0) -> float:
    values = [float(x) for x in re.findall(rf"(\d+(?:\.\d+)?)\s*{unit}", text.lower())]
    return round(sum(values) * weight_per_unit, 2) if values else 0

# 예외상품 처리: 제품+제품 혼합
def is_mixed_product(text: str) -> bool:
    plus_parts = text.split("+")
    product_count = sum(1 for part in plus_parts if any(k in part for k in ["마늘", "닭발", "가루", "쫑", "빠삭이"]))
    return product_count > 1

# ---------------- 정제 로직 함수 정의 ----------------
def clean_option_cell(text: str) -> str:
    text = str(text)

    # 괄호 제거 (단, 무게 단위 포함된 괄호는 무시)
    text = re.sub(r"\((?:(?!\d+(?:\.\d+)?\s*(?:kg|g|팩|개입)).)*?\)", "", text)

    # / 콜론 정제 우선
    if "/" in text:
        parts = text.split("/")
        parts = [p.strip() for p in parts if p.strip()]
        # 슬래시 뒤에 콜론이 있다면 가장 마지막 콜론 뒤 값만 추출
        if ":" in parts[-1]:
            text = parts[-1].split(":")[-1].strip()
        else:
            text = parts[0]

    # 콜론만 있는 경우
    if ":" in text:
        text = text.split(":")[-1].strip()

    text = text.replace("+", " + ")  # 구분자 명확화
    chunks = [chunk.strip() for chunk in text.split("+")]

    result = []
    for chunk in chunks:
        lower = chunk.lower()

        # 마늘빠삭이
        if "빠삭" in lower:
            match = re.search(r"(\d+)\s*개입", lower)
            val = f"마늘빠삭이 {match.group(1)}개입" if match else "마늘빠삭이"
            result.append(val)
            continue

        # 무뼈닭발
        if "닭발" in lower:
            packs = re.findall(r"(\d+)\s*팩", lower)
            if not packs:
                grams = sum(map(float, re.findall(r"(\d+(?:\.\d+)?)\s*g", lower)))
                pack_count = int(grams // 200)
            else:
                pack_count = sum(map(int, packs))
            result.append(f"무뼈닭발 {pack_count}팩")
            continue

        # 마늘가루
        if "가루" in lower:
            gram = re.search(r"(\d+)\s*g", lower)
            val = f"마늘가루 {gram.group(1)}g" if gram else "마늘가루"
            result.append(val)
            continue

        # 마늘쫑
        if "쫑" in lower:
            kg = re.findall(r"(\d+(?:\.\d+)?)\s*kg", lower)
            total = sum(map(float, kg)) if kg else 1
            prefix = "** 업 소 용 ** " if total >= 10 else ""
            result.append(f"{prefix}마늘쫑 {int(total)}kg")
            continue

        # 마늘류
        if "마늘" in lower:
            parts = []

            # 업소용
            kg_values = re.findall(r"(\d+(?:\.\d+)?)\s*kg", lower)
            total_kg = sum(map(float, kg_values)) if kg_values else 0
            if total_kg >= 10:
                parts.append("** 업 소 용 **")

            # 품종
            if "육쪽" in lower:
                parts.append("♣ 육 쪽 ♣")
            elif "대서" in lower or "대서" in chunk:
                parts.append("대서")
            else:
                parts.append("대서")  # 기본 품종

            # 형태
            if "다진" in lower:
                parts.append("다진마늘")
            elif "깐" in lower:
                parts.append("깐마늘")
            elif "통" in lower:
                parts.append("통마늘")

            # 크기
            if "특" in lower:
                parts.append("특")
            elif "대" in lower:
                parts.append("대")
            elif "중" in lower:
                parts.append("중")
            elif "소" in lower:
                if "다진" not in lower:
                    parts.append("소")

            # 꼭지
            if "꼭지포함" in lower:
                parts.append("* 꼭 지 포 함 *")
            elif "꼭지제거" in lower:
                parts.append("꼭지제거")

            parts.append(f"{int(total_kg)}kg" if total_kg else "1kg")
            result.append(" ".join(parts))
            continue

        # 기본
        result.append(chunk)

    return " + ".join(result)

# ---------------- 정제 로직 구현 ----------------
def clean_option_cell(cell: str) -> str:
    original = cell
    cell = re.sub(r"[\[\]{}]", "", cell)  # 괄호 제거
    cell = re.sub(r"\([^)]*총\s*\d+(\.\d+)?\s*(kg|g|개|팩)\)", "", cell, flags=re.IGNORECASE)  # (총xx단위) 제거
    cell = re.sub(r"\([^)]*\)", "", cell)  # 나머지 괄호 제거

    parts = re.split(r"\s*/\s*", cell)
    simplified = []
    for part in parts:
        if ":" in part:
            part = part.split(":")[-1]
        simplified.append(part.strip())
    cell = " ".join(simplified)

    # 제품 + 제품 예외처리
    if "+" in cell and not re.search(r"\d+\s*(kg|g|개|팩)", cell):
        return cell.strip()

    # 마늘빠삭이
    if "빠삭" in cell:
        pcs = sum(map(int, re.findall(r"(\d+)\s*개", cell)))
        return f"마늘빠삭이 {pcs}개입" if pcs else "마늘빠삭이"

    # 무뼈닭발
    if "닭발" in cell:
        packs = sum(map(int, re.findall(r"(\d+)\s*팩", cell)))
        if not packs:
            g = sum(map(float, re.findall(r"(\d+\.?\d*)\s*g", cell)))
            packs = int(g // 200)
        return f"무뼈닭발 {packs}팩"

    # 마늘가루
    if "가루" in cell:
        grams = sum(map(int, re.findall(r"(\d+)\s*g", cell)))
        return f"마늘가루 {grams}g" if grams else "마늘가루"

    # 마늘쫑
    if "마늘쫑" in cell:
        kg = sum(map(int, re.findall(r"(\d+)\s*kg", cell.lower())))
        return f"** 업 소 용 ** 마늘쫑 {kg}kg" if kg >= 10 else f"마늘쫑 {kg}kg"

    # 마늘류
    tag = []
    bulk = bool(re.search(r"\b10\s*kg\b", cell.lower()))
    if bulk:
        tag.append("** 업 소 용 **")

    if "육쪽" in cell:
        tag.append("♣ 육 쪽 ♣")
    elif "대서" in cell:
        tag.append("대서")
    else:
        tag.append("대서")

    if "다진" in cell:
        tag.append("다진마늘")
    elif "깐" in cell:
        tag.append("깐마늘")
    elif "통" in cell:
        tag.append("통마늘")

    if not "다진" in cell:
        if "특" in cell:
            tag.append("특")
        elif "대" in cell:
            tag.append("대")
        elif "중" in cell:
            tag.append("중")
        elif "소" in cell:
            tag.append("소")

    if "꼭지포함" in cell:
        tag.append("* 꼭 지 포 함 *")
    elif "꼭지제거" in cell:
        tag.append("꼭지제거")

    kg = sum(map(int, re.findall(r"(\d+)\s*kg", cell.lower())))
    tag.append(f"{kg}kg" if kg else "0kg")
    return " ".join(tag)

# ---------------- 엑셀 파일 정제 함수 ----------------
import pandas as pd

def clean_excel_file(input_path: str, output_path: str) -> None:
    df = pd.read_excel(input_path)
    option_col = None

    for col in df.columns:
        if any(key in col for key in ["옵션", "옵션명", "옵션정보"]):
            option_col = col
            break

    if not option_col:
        raise ValueError("정제 가능한 옵션 열이 존재하지 않습니다.")

    df[option_col] = df[option_col].astype(str).apply(clean_option_cell)
    df.to_excel(output_path, index=False)

