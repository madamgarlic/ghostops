# ghostops_all_in_one.py
import streamlit as st
import pandas as pd
import re
import tempfile
import os
from collections import defaultdict

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
    text = re.sub(r"[\[\](){}]", "", text)
    text = text.lower()

    # 우선 정제 우선순위 적용
    if "마늘빠삭이" in text:
        pcs = re.search(r"(\d+)개입", text)
        return f"마늘빠삭이 {pcs.group(1)}개입" if pcs else "마늘빠삭이"

    if "무뼈닭발" in text:
        total_pack_match = re.search(r"총\s*(\d+)\s*팩", text)
        if total_pack_match:
            packs = int(total_pack_match.group(1))
        else:
            parts = re.findall(r"(\d+)\s*팩", text)
            if parts:
                packs = sum(map(int, parts))
            else:
                grams = extract_total_weight(text) * 1000
                packs = int(grams // 200)
        return f"무뼈닭발 {packs}팩"

    if "마늘가루" in text:
        match = re.search(r"(\d+)(g|G)", text)
        return f"마늘가루 {match.group(1)}g" if match else "마늘가루"

    if "마늘쫑" in text:
        weight_match = re.search(r"(\d+(\.\d+)?)\s*kg", text)
        weight = weight_match.group(1) if weight_match else ""
        is_bulk = "10kg" in text or "대용량" in text or "벌크" in text or "업소용" in text
        result = []
        if is_bulk:
            result.append("** 업 소 용 **")
        result.append("마늘쫑")
        if weight:
            result.append(f"{weight}kg")
        return " ".join(result)

    # 마늘류 정제
    if "마늘" in text:
        tag = []
        if "10kg" in text or "대용량" in text or "벌크" in text or "업소용" in text:
            tag.append("** 업 소 용 **")
        if "육쪽" in text:
            tag.append("♣ 육 쪽 ♣")
        elif "대서" not in text:
            tag.append("대서")
        if "다진" in text:
            tag.append("다진마늘")
        elif "깐" in text:
            tag.append("깐마늘")
        elif "통" in text:
            tag.append("통마늘")
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
        match = re.search(r"(\d+(\.\d+)?)\s*kg", text)
        if match:
            tag.append(f"{match.group(1)}kg")
        return " ".join(tag)

    return text

# ---------------------- Streamlit UI ----------------------
st.set_page_config(page_title="Garlic Spirit | 올인원 발주 매니저", layout="wide")
st.title("🧄 garlic spirit | 올인원 발주 매니저")

uploaded_files = st.file_uploader("발주서 파일 업로드 (.xlsx, .xls, .csv)", type=["xlsx", "xls", "csv"], accept_multiple_files=True)
if uploaded_files:
    st.success(f"{len(uploaded_files)}개 파일 업로드 완료")
    temp_dir = tempfile.mkdtemp()
    cleaned_files = []

    for uploaded_file in uploaded_files:
        input_path = os.path.join(temp_dir, uploaded_file.name)
        output_path = os.path.join(temp_dir, f"정제_{uploaded_file.name}")
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        df = pd.read_excel(input_path)
        option_col = None
        for col in df.columns:
            if any(key in col for key in ["옵션", "옵션정보", "옵션명"]):
                option_col = col
                break

        if option_col is None:
            st.error(f"{uploaded_file.name} 파일: 옵션열을 찾을 수 없습니다.")
            continue

        df[option_col] = df[option_col].fillna("").apply(lambda x: parse_option(str(x).strip()))
        df.to_excel(output_path, index=False)
        cleaned_files.append(output_path)

        st.download_button(
            label=f"📄 정제된 {uploaded_file.name} 다운로드",
            data=open(output_path, "rb").read(),
            file_name=f"정제_{uploaded_file.name}",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
