# ghostops_all_in_one.py
import streamlit as st
import pandas as pd
import re
import tempfile
import os
from collections import defaultdict

# ---------------------- 정제 도우미 ----------------------
def extract_weight(text: str) -> float:
    text = text.lower()
    match = re.search(r"총\s*(\d+(\.\d+)?)\s*kg", text)
    if match:
        return float(match.group(1))
    parts = re.findall(r"(\d+(\.\d+)?)\s*kg", text)
    return sum(float(p[0]) for p in parts) if parts else 0.0

def parse_option(text: str) -> str:
    text = re.sub(r"[\[\](){}]", "", text)  # 괄호 제거
    text = text.split("/")[0].strip()  # / 뒤 제거
    options = [opt.strip() for opt in text.split("+") if opt.strip()]

    results = []
    for opt in options:
        opt_lower = opt.lower()

        # 무뼈닭발
        if "무뼈" in opt_lower and "닭발" in opt_lower:
            packs = re.findall(r"(\d+)\s*팩", opt_lower)
            if packs:
                count = sum(map(int, packs))
            else:
                weight_match = re.search(r"(총\s*)?(\d+(\.\d+)?)\s*g", opt_lower)
                if weight_match:
                    grams = float(weight_match.group(2))
                    count = round(grams / 200)
                else:
                    count = 1
            results.append(f"무뼈닭발 {count}팩")
            continue

        # 마늘빠삭이
        if "마늘빠삭이" in opt_lower:
            pcs = re.search(r"(\d+)[개입|입]", opt_lower)
            if pcs:
                results.append(f"마늘빠삭이 {pcs.group(1)}개입")
            else:
                results.append("마늘빠삭이")
            continue

        # 마늘가루
        if "마늘가루" in opt_lower:
            match = re.search(r"(\d+)(g|G)", opt)
            if match:
                results.append(f"마늘가루 {match.group(1)}g")
            else:
                results.append("마늘가루")
            continue

        # 마늘쫑
        if "마늘쫑" in opt_lower:
            tag = ["** 업 소 용 **"] if re.search(r"(5|6|7|8|9|10)\s*kg|대용량|벌크|업소용", opt_lower) else []
            weight_match = re.search(r"(총\s*)?(\d+(\.\d+)?)\s*kg", opt_lower)
            weight = weight_match.group(2) if weight_match else "1"
            tag += ["마늘쫑", f"{int(float(weight))}kg"]
            results.append(" ".join(tag))
            continue

        # 마늘류 (다진/깐/통)
        tag = []
        if re.search(r"(5|6|7|8|9|10)\s*kg|대용량|벌크|업소용", opt_lower):
            tag.append("** 업 소 용 **")
        if "육쪽" in opt_lower:
            tag.append("♣ 육 쪽 ♣")
        else:
            tag.append("대서")
        if "다진" in opt_lower:
            tag.append("다진마늘")
        elif "깐" in opt_lower:
            tag.append("깐마늘")
        elif "통" in opt_lower:
            tag.append("통마늘")

        if "다진" not in opt_lower:
            for size in ["특", "대", "중", "소"]:
                if size in opt:
                    tag.append(size)
                    break

        if "꼭지포함" in opt_lower:
            tag.append("* 꼭 지 포 함 *")
        elif "꼭지제거" in opt_lower:
            tag.append("꼭지제거")

        weight_match = re.search(r"(총\s*)?(\d+(\.\d+)?)\s*kg", opt_lower)
        weight = weight_match.group(2) if weight_match else "1"
        tag.append(f"{int(float(weight))}kg")
        results.append(" ".join(tag))

    return " + ".join(results)

# ---------------------- Streamlit 앱 UI ----------------------
st.set_page_config(page_title="Garlic Spirit | 올인원 발주 매니저", layout="wide")
st.title("🧄 Garlic Spirit | 올인원 발주 매니저")

uploaded_files = st.file_uploader("발주서 파일 업로드", type=["xlsx", "xls", "csv"], accept_multiple_files=True)
if uploaded_files:
    st.success(f"{len(uploaded_files)}개 파일 업로드 완료")
    temp_dir = tempfile.mkdtemp()
    cleaned_files = []

    for uploaded_file in uploaded_files:
        input_path = os.path.join(temp_dir, uploaded_file.name)
        output_path = os.path.join(temp_dir, f"정제_{uploaded_file.name}")
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        try:
            df = pd.read_excel(input_path)
        except:
            df = pd.read_csv(input_path, encoding="utf-8")

        option_col = None
        for col in df.columns:
            if any(key in col for key in ["옵션", "옵션명", "옵션정보"]):
                option_col = col
                break

        if option_col is None:
            st.error(f"{uploaded_file.name} 파일: 옵션열을 찾을 수 없습니다.")
            continue

        df[option_col] = df[option_col].fillna("").apply(parse_option)
        df.to_excel(output_path, index=False)
        cleaned_files.append(output_path)
        st.download_button(f"📄 {uploaded_file.name} 정제 다운로드", open(output_path, "rb").read(), file_name=f"정제_{uploaded_file.name}")

    # ---------------------- 📦 패킹리스트 생성 ----------------------
    st.subheader("📦 패킹리스트")
    summary = defaultdict(int)

    for path in cleaned_files:
        df = pd.read_excel(path)
        option_col = next((c for c in df.columns if "옵션" in c), None)
        count_col = next((c for c in df.columns if "수량" in c), None)
        if not option_col or not count_col:
            continue

        for _, row in df.iterrows():
            options = str(row[option_col]).split(" + ")
            count = int(row[count_col])
            for opt in options:
                base = re.sub(r"\s*\d+(kg|g|개입|팩)", "", opt).strip()

                # 업소용은 무게 포함
                if "** 업 소 용 **" in opt:
                    summary[opt] += count
                elif "마늘가루" in opt:
                    grams = int(re.search(r"(\d+)g", opt).group(1))
                    qty = (grams / 100) * count
                    summary[base] += qty
                elif "무뼈닭발" in opt:
                    packs = int(re.search(r"(\d+)팩", opt).group(1)) * count
                    summary[base] += packs
                elif "마늘빠삭이" in opt:
                    pcs = int(re.search(r"(\d+)개입", opt).group(1)) / 10 * count
                    summary[base] += pcs
                elif "마늘쫑" in opt:
                    kg = int(re.search(r"(\d+)kg", opt).group(1)) * count
                    summary[base] += kg
                else:
                    kg = int(re.search(r"(\d+)kg", opt).group(1)) * count
                    summary[base] += kg

    if summary:
        df_pack = pd.DataFrame([{"단위": "개", "상품명": k, "수량": int(v)} for k, v in summary.items()])
        pack_path = os.path.join(temp_dir, "패킹리스트.xlsx")
        df_pack.to_excel(pack_path, index=False)
        st.download_button("📥 패킹리스트 다운로드", open(pack_path, "rb").read(), file_name="패킹리스트.xlsx")
