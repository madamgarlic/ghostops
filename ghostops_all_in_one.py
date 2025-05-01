# ghostops_all_in_one.py
import streamlit as st
import pandas as pd
import re
import tempfile
import os
from collections import defaultdict

st.set_page_config(page_title="Garlic Spirit | 올인원 발주 매니저", layout="wide")
st.title("🧄 Garlic Spirit | 올인원 발주 매니저")

# 공통 정제 도우미
def clean_text(text):
    return re.sub(r"[\[\](){}]", "", str(text)).strip()

def extract_weight_info(text):
    text = text.lower()
    total = 0.0

    # 총 Nkg
    match_total = re.search(r"총\s*(\d+(\.\d+)?)\s*kg", text)
    if match_total:
        return float(match_total.group(1))

    # 1kg + 1kg
    kg_list = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*kg", text)]
    if kg_list:
        return sum(kg_list)

    # 1팩 + 1팩
    pack_count = sum(int(x) for x in re.findall(r"(\d+)\s*팩", text))
    if pack_count:
        return pack_count * 0.2

    # g 단위
    g_match = re.findall(r"(\d+)\s*g", text)
    if g_match:
        return sum([int(x) for x in g_match]) / 1000

    return 1.0  # fallback
def extract_info(text):
    text = clean_text(text)
    text = re.sub(r"[\s]*\/[\s]*", "/", text)
    text = re.sub(r"[\s]*:[\s]*", ":", text)
    text = text.lower()

    # 1) 슬래시 + 콜론 규칙: / 뒤에 : 있으면 가장 마지막 : 뒤를 추출
    if "/" in text:
        parts = text.split("/")
        for part in reversed(parts):
            if ":" in part:
                text = part.split(":")[-1]
                break
        else:
            text = parts[0]
    elif ":" in text:
        text = text.split(":")[-1]

    original_text = text
    tag = []

    # 업소용 판단
    is_bulk = any(k in text for k in ["대용량", "벌크", "업소용"]) or re.search(r"\b[5-9]\s*kg\b", text)
    if is_bulk:
        tag.append("** 업 소 용 **")

    # 마늘류
    if "마늘" in text:
        # 품종
        if "육쪽" in text:
            tag.append("♣ 육 쪽 ♣")
        elif "대서" not in text:
            tag.append("대서")

        # 형태
        if "다진" in text:
            tag.append("다진마늘")
        elif "깐" in text:
            tag.append("깐마늘")
        elif "통" in text:
            tag.append("통마늘")

        # 크기 (다진마늘 제외)
        if "다진" not in text:
            if "특" in text:
                tag.append("특")
            elif "대" in text:
                tag.append("대")
            elif "중" in text:
                tag.append("중")
            elif "소" in text:
                tag.append("소")

        # 꼭지유무
        if "꼭지포함" in text:
            tag.append("* 꼭 지 포 함 *")
        elif "꼭지제거" in text:
            tag.append("꼭지제거")

        # 무게
        tag.append(f"{int(extract_weight_info(original_text))}kg")
        return " ".join(tag)

    # 마늘쫑
    if "마늘쫑" in text:
        if is_bulk:
            tag.append("** 업 소 용 **")
        tag.append("마늘쫑")
        tag.append(f"{int(extract_weight_info(text))}kg")
        return " ".join(tag)

    # 마늘빠삭이
    if "마늘빠삭이" in text:
        pcs = re.search(r"(\d+)\s*개입", text)
        return f"마늘빠삭이 {pcs.group(1)}개입" if pcs else "마늘빠삭이"

    # 무뼈닭발
    if "무뼈닭발" in text:
        packs = re.findall(r"(\d+)\s*팩", text)
        if not packs:
            grams = extract_weight_info(text) * 1000
            packs = int(grams // 200)
        else:
            packs = sum(map(int, packs))
        return f"무뼈닭발 {packs}팩"

    # 마늘가루
    if "마늘가루" in text:
        match = re.search(r"(\d+)[gG]", text)
        return f"마늘가루 {match.group(1)}g" if match else "마늘가루"

    return text
uploaded_files = st.file_uploader(
    "발주서 파일 업로드 (.xlsx, .xls, .csv)", 
    type=["xlsx", "xls", "csv"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"{len(uploaded_files)}개 파일 업로드 완료")
    temp_dir = tempfile.mkdtemp()
    cleaned_files = []

    for file in uploaded_files:
        input_path = os.path.join(temp_dir, file.name)
        output_path = os.path.join(temp_dir, f"정제_{file.name}")
        with open(input_path, "wb") as f:
            f.write(file.getbuffer())

        try:
            df = pd.read_excel(input_path)
        except:
            df = pd.read_csv(input_path, encoding="utf-8")

        option_col = None
        for col in df.columns:
            if any(key in col for key in ["옵션", "옵션정보", "옵션명"]):
                option_col = col
                break

        if option_col is None:
            st.error(f"{file.name} 파일: 옵션열을 찾을 수 없습니다.")
            continue

        df[option_col] = df[option_col].fillna("").apply(
            lambda x: " + ".join(extract_info(p.strip()) for p in str(x).split("+") if p)
        )

        df.to_excel(output_path, index=False)
        cleaned_files.append(output_path)
        st.download_button(
            f"📄 {file.name} 정제 다운로드",
            open(output_path, "rb").read(),
            file_name=f"정제_{file.name}"
        )
    # 📦 패킹리스트 생성
    st.subheader("📦 패킹리스트")
    summary = defaultdict(float)

    for path in cleaned_files:
        df = pd.read_excel(path)
        option_col = next((c for c in df.columns if "옵션" in c), None)
        count_col = next((c for c in df.columns if "수량" in c), None)
        if not option_col or not count_col:
            continue

        for _, row in df.iterrows():
            options = str(row[option_col]).split(" + ")
            count = row[count_col]
            for opt in options:
                key = opt
                # 마늘가루
                if "마늘가루" in opt:
                    match = re.search(r"(\d+)g", opt)
                    grams = int(match.group(1)) if match else 100
                    qty = (grams / 100) * count
                    summary["마늘가루"] += qty
                elif "무뼈닭발" in opt:
                    match = re.search(r"(\d+)팩", opt)
                    qty = int(match.group(1)) * count if match else count
                    summary["무뼈닭발"] += qty
                elif "마늘빠삭이" in opt:
                    match = re.search(r"(\d+)개입", opt)
                    box = int(match.group(1)) // 10 if match else 1
                    qty = count * box
                    summary["마늘빠삭이"] += qty
                elif "마늘쫑" in opt:
                    match = re.search(r"(\d+)kg", opt)
                    qty = int(match.group(1)) * count if match else count
                    summary["마늘쫑"] += qty
                elif "** 업 소 용 **" in opt:
                    qty = count
                    summary[opt] += qty
                else:
                    match = re.search(r"(\d+)kg", opt)
                    kg = int(match.group(1)) if match else 1
                    qty = kg * count
                    summary[re.sub(r"\d+kg", "", opt).strip()] += qty

    if summary:
        df_pack = pd.DataFrame(
            [{"단위": "수량", "상품명": k, "수량": int(v)} for k, v in summary.items()]
        )
        pack_path = os.path.join(temp_dir, "패킹리스트.xlsx")
        df_pack.to_excel(pack_path, index=False)
        st.download_button("📥 패킹리스트 다운로드", open(pack_path, "rb").read(), file_name="패킹리스트.xlsx")

