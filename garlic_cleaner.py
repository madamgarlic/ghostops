# ghostops_all_in_one.py
import streamlit as st
import pandas as pd
import re
import tempfile
import os
from collections import defaultdict

st.set_page_config(page_title="Garlic Spirit | 올인원 발주 매니저", layout="wide")
st.title("🧄 Garlic Spirit | 올인원 발주 매니저")

# ---------- 정제 로직 ----------
def extract_kg(text):
    weights = re.findall(r"(\d+(?:\.\d+)?)\s*kg", text.lower())
    return sum(map(float, weights)) if weights else 0

def extract_pack(text):
    packs = re.findall(r"(\d+)\s*팩", text)
    return sum(map(int, packs)) if packs else 0

def extract_piece(text):
    pcs = re.findall(r"(\d+)\s*개입", text)
    return sum(map(int, pcs)) if pcs else 0

def clean_text(text):
    text = re.sub(r"[\[\](){}]", "", text)  # 괄호 제거
    if ":" in text:
        segments = text.split("/")
        for seg in reversed(segments):
            if ":" in seg:
                text = seg.split(":")[-1].strip()
                break
        else:
            text = segments[0].strip()
    elif "/" in text:
        text = text.split("/")[0].strip()
    return text

def parse_option(raw):
    raw = clean_text(raw)
    raw = raw.replace(" ", "")

    # 마늘빠삭이
    if "마늘빠삭이" in raw:
        pcs = extract_piece(raw)
        pcs = pcs if pcs else 10
        return f"마늘빠삭이 {pcs}개입"

    # 무뼈닭발
    if "무뼈닭발" in raw:
        packs = extract_pack(raw)
        if not packs:
            kg = extract_kg(raw)
            packs = int((kg * 1000) // 200)
        return f"무뼈닭발 {packs}팩"

    # 마늘가루
    if "마늘가루" in raw:
        g = re.search(r"(\d+)[gG]", raw)
        amount = g.group(1) if g else "100"
        return f"마늘가루 {amount}g"

    # 마늘쫑
    if "마늘쫑" in raw:
        kg = extract_kg(raw)
        label = "** 업 소 용 ** " if kg >= 10 else ""
        return f"{label}마늘쫑 {int(kg)}kg"

    # 마늘류
    tag = []
    kg = extract_kg(raw)
    if kg >= 10:
        tag.append("** 업 소 용 **")

    if "육쪽" in raw:
        tag.append("♣ 육 쪽 ♣")
    else:
        tag.append("대서")

    if "다진" in raw:
        tag.append("다진마늘")
    elif "깐" in raw:
        tag.append("깐마늘")
    elif "통" in raw:
        tag.append("통마늘")

    if "다진" not in raw:
        for size in ["특", "대", "중", "소"]:
            if size in raw:
                tag.append(size)
                break

    if "꼭지포함" in raw:
        tag.append("* 꼭 지 포 함 *")
    elif "꼭지제거" in raw:
        tag.append("꼭지제거")

    tag.append(f"{int(kg)}kg")
    return " ".join(tag)

# ---------- 앱 실행 ----------
uploaded_files = st.file_uploader("발주서 업로드", type=["xlsx", "xls", "csv"], accept_multiple_files=True)
if uploaded_files:
    st.success(f"{len(uploaded_files)}개 파일 업로드됨!")
    temp_dir = tempfile.mkdtemp()

    for uploaded_file in uploaded_files:
        input_path = os.path.join(temp_dir, uploaded_file.name)
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        df = pd.read_excel(input_path)
        option_col = next((col for col in df.columns if any(key in col for key in ["옵션", "옵션명", "옵션정보"])), None)

        if option_col is None:
            st.error(f"{uploaded_file.name} 파일: 옵션열을 찾을 수 없습니다.")
            continue

        def parse_combined_options(cell):
            return " + ".join(parse_option(part.strip()) for part in str(cell).split("+") if part.strip())

        df[option_col] = df[option_col].apply(parse_combined_options)
        output_path = os.path.join(temp_dir, f"정제_{uploaded_file.name}")
        df.to_excel(output_path, index=False)
        st.download_button(f"📄 정제 완료: {uploaded_file.name}", open(output_path, "rb").read(), file_name=f"정제_{uploaded_file.name}")
