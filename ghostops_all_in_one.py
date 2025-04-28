# ghostops_all_in_one.py
import streamlit as st
import pandas as pd
import re
import tempfile
import os
from collections import defaultdict

# ---------------------- 정제 도우미 ----------------------
def read_file(input_path):
    ext = os.path.splitext(input_path)[-1].lower()
    if ext == ".csv":
        return pd.read_csv(input_path)
    elif ext in [".xls", ".xlsx"]:
        return pd.read_excel(input_path, engine="openpyxl")
    else:
        raise ValueError("지원하지 않는 파일 형식입니다.")

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

    is_bulk = any(k in text for k in ["대용량", "벌크", "업소용"]) or re.search(r"\b[5-9]\s*kg\b", text)

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

    if "마늘쫑" in text:
        result = []
        if is_bulk:
            result.append("** 업 소 용 **")
        result.append("마늘쫑")
        result.append(f"{int(extract_total_weight(text))}kg")
        return " ".join(result)

    if "무뼈닭발" in text:
        packs = re.findall(r"(\d+)\s*팩", text)
        if not packs:
            grams = extract_total_weight(text) * 1000
            packs = int(grams // 200)
        else:
            packs = sum(map(int, packs))
        return f"무뼈닭발 {packs}팩"

    if "마늘빠삭이" in text:
        pcs = re.search(r"(\d+)개입", text)
        return f"마늘빠삭이 {pcs.group(1)}개입" if pcs else "마늘빠삭이"

    if "마늘가루" in text:
        match = re.search(r"(\d+)(g|G)", text)
        return f"마늘가루 {match.group(1)}g" if match else "마늘가루"

    return text

# ---------------------- Streamlit UI ----------------------
st.set_page_config(page_title="garlic spirit | All-in-One Order Manager", layout="wide")
st.title("garlic spirit | All-in-One Order Manager")

uploaded_files = st.file_uploader("발주서 파일 업로드 (.xlsx, .xls, .csv)", type=["xlsx", "xls", "csv"], accept_multiple_files=True)
if uploaded_files:
    st.success(f"{len(uploaded_files)}개 파일 업로드 완료")
    temp_dir = tempfile.mkdtemp()
    cleaned_files = []

    for file in uploaded_files:
        input_path = os.path.join(temp_dir, file.name)
        output_path = os.path.join(temp_dir, f"정제_{file.name}")
        with open(input_path, "wb") as f:
            f.write(file.getbuffer())

        df = read_file(input_path)
        option_col = None
        for col in df.columns:
            if any(key in col.strip() for key in ["옵션", "옵션정보", "옵션명"]):
                option_col = col
                break

        if option_col:
            df[option_col] = df[option_col].fillna("").apply(lambda x: " + ".join(parse_option(str(x).strip()) for x in x.split("+") if x))
            df.to_excel(output_path, index=False)
            cleaned_files.append(output_path)
            st.download_button(f"📄 {file.name} 정제 다운로드", open(output_path, "rb").read(), file_name=f"정제_{file.name}")
        else:
            st.error(f"{file.name}: 옵션열(옵션/옵션정보/옵션명)을 찾을 수 없습니다.")

    # ---------------------- 패킹리스트 생성 ----------------------
    st.subheader("📦 패킹리스트")
    summary = defaultdict(int)
    unit_table = {
        "마늘가루": 0.1,
        "마늘쫑": 1,
        "무뼈닭발": 0.2,
        "마늘빠삭이": 10,
        "마늘": 1
    }

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
                base = opt
                if any(k in opt for k in ["마늘가루"]):
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
                    qty = (int(match.group(1)) / 10) * count if match else count
                    summary["마늘빠삭이"] += qty
                elif "마늘쫑" in opt:
                    match = re.search(r"(\d+)kg", opt)
                    qty = int(match.group(1)) * count if match else count
                    summary["마늘쫑"] += qty
                else:
                    match = re.search(r"(\d+)kg", opt)
                    qty = int(match.group(1)) * count if match else count
                    summary[base] += qty

    if summary:
        df_pack = pd.DataFrame([{"상품명": k, "수량": int(v)} for k, v in summary.items()])
        pack_path = os.path.join(temp_dir, "패킹리스트.xlsx")
        df_pack.to_excel(pack_path, index=False)
        st.download_button("📥 패킹리스트 다운로드", open(pack_path, "rb").read(), file_name="패킹리스트.xlsx")
