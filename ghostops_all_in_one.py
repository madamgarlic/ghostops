# ghostops_all_in_one.py
import streamlit as st
import pandas as pd
import re
import tempfile
import os

# ---------------------- 정제 도우미 ----------------------
def simplify_named_option(text: str) -> str:
    parts = [p.strip() for p in text.split("/") if ":" in p]
    if len(parts) >= 2:
        return parts[-1].split(":")[-1].strip()
    return text

def extract_total_weight(text: str) -> float:
    match = re.search(r"총\s*(\d+(\.\d+)?)\s*kg", text.lower())
    if match:
        return float(match.group(1))
    weights = [float(m.group(1)) for m in re.finditer(r"(\d+(\.\d+)?)\s*kg", text.lower())]
    return sum(weights)

def parse_option(text: str) -> str:
    text = simplify_named_option(text)
    text = re.sub(r"[\[\](){}]", "", text)  # 괄호 제거
    text = text.lower()

    # 업소용
    is_bulk = any(k in text for k in ["대용량", "벌크", "업소용"]) or re.search(r"\b[5-9]\s*kg\b", text)

    # 마늘 여부
    if "마늘" in text:
        tag = []
        if is_bulk:
            tag.append("** 업 소 용 **")

        if "육쪽" in text:
            tag.append("♣ 육 쪽 ♣")
        elif "대서" not in text:
            tag.append("대서")

        if "다진마늘" in text:
            tag.append("다진마늘")
        elif "깐마늘" in text:
            tag.append("깐마늘")

        if "특" in text:
            tag.append("특")
        elif "대" in text:
            tag.append("대")
        elif "중" in text:
            tag.append("중")
        elif "소" in text:
            tag.append("소")

        if "꼭지포함" in text:
            tag.append("* 꼭 지 포 함 *")
        elif "꼭지제거" in text:
            tag.append("꼭지제거")

        tag.append(f"{int(extract_total_weight(text))}kg")
        return " ".join(tag)

    # 마늘쫑
    if "마늘쫑" in text:
        result = []
        if is_bulk:
            result.append("** 업 소 용 **")
        result.append("마늘쫑")
        result.append(f"{int(extract_total_weight(text))}kg")
        return " ".join(result)

    # 무뼈닭발
    if "무뼈닭발" in text:
        packs = re.findall(r"(\d+)\s*팩", text)
        if not packs:
            grams = extract_total_weight(text) * 1000
            packs = int(grams // 200)
        else:
            packs = sum(map(int, packs))
        return f"무뼈닭발 {packs}팩"

    # 마늘빠삭이
    if "마늘빠삭이" in text:
        pcs = re.search(r"(\d+)개입", text)
        return f"마늘빠삭이 {pcs.group(1)}개입" if pcs else "마늘빠삭이"

    # 마늘가루
    if "마늘가루" in text:
        match = re.search(r"(\d+)(g|G)", text)
        return f"마늘가루 {match.group(1)}g" if match else "마늘가루"

    return text

# ---------------------- Streamlit UI ----------------------
st.set_page_config(page_title="ghostops 올인원", layout="wide")
st.title("🧄 ghostops | 올인원 정제 시스템")

uploaded_files = st.file_uploader("발주서 파일 업로드 (.xlsx)", type="xlsx", accept_multiple_files=True)
if uploaded_files:
    st.success(f"{len(uploaded_files)}개 파일 업로드 완료")
    temp_dir = tempfile.mkdtemp()
    for file in uploaded_files:
        input_path = os.path.join(temp_dir, file.name)
        output_path = os.path.join(temp_dir, f"정제_{file.name}")
        with open(input_path, "wb") as f:
            f.write(file.getbuffer())

        df = pd.read_excel(input_path)
        option_col = None
        for col in df.columns:
            if any(key in col for key in ["옵션", "옵션정보", "옵션명"]):
                option_col = col
                break

        if option_col:
            df[option_col] = df[option_col].fillna("").apply(lambda x: " + ".join(parse_option(str(x).strip()) for x in x.split("+") if x))
            df.to_excel(output_path, index=False)
            st.download_button(f"📄 {file.name} 정제 다운로드", open(output_path, "rb").read(), file_name=f"정제_{file.name}")
        else:
            st.error(f"{file.name}: 옵션열을 찾을 수 없습니다.")
