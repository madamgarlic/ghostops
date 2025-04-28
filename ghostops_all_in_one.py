# ghostops_all_in_one.py (정제 + 패킹리스트 + 송장리스트 + 오류감지 통합)
import streamlit as st
import pandas as pd
import re
import os
import tempfile
from collections import defaultdict

# ----------------------------- 정제 조건 -----------------------------
MANDATORY_COLUMNS = {
    '11번가': {'수령인': '수취인', '전화번호': '휴대폰번호', '상품명': '정제옵션'},
    '스마트스토어': {'수령인': '수취인명', '전화번호': '수취인연락처1', '상품명': '정제옵션'},
    'ESM': {'수령인': '수취인명', '전화번호': '수령인휴대폰', '상품명': '정제옵션'},
    '카카오': {'수령인': '수취인명', '전화번호': '하이픈포함수령인연락처1', '상품명': '정제옵션'},
}

UNIT_TABLE = {
    '마늘류': 1,
    '마늘쫑': 1,
    '무뼈닭발': 0.2,
    '마늘빠삭이': 10,
    '마늘가루': 0.1,
}

# ----------------------------- 정제 도우미 -----------------------------
def clean_text(text: str) -> str:
    text = re.sub(r'[\[\](){}]', '', text)
    return text.strip()

def extract_weight(text: str) -> float:
    text = text.lower()
    total = 0.0
    matches = re.findall(r'(\d+(\.\d+)?)\s*kg', text)
    for match in matches:
        total += float(match[0])
    return total

def detect_option_column(df) -> str:
    candidates = ["옵션", "옵션정보", "옵션명"]
    for candidate in candidates:
        for col in df.columns:
            if candidate in col:
                return col
    raise ValueError("옵션열을 찾을 수 없습니다. ('옵션', '옵션정보', '옵션명' 중 하나 필요)")

def parse_option(text: str) -> str:
    text = clean_text(text)
    text = text.lower()

    if '마늘빠삭이' in text:
        pcs = re.search(r'(\d+)개입', text)
        return f'마늘빠삭이 {pcs.group(1)}개입' if pcs else '마늘빠삭이'

    if '무뼈닭발' in text:
        packs = re.findall(r'(\d+)\s*팩', text)
        if packs:
            total_packs = sum(map(int, packs))
        else:
            grams = extract_weight(text) * 1000
            total_packs = int(grams // 200)
        return f'무뼈닭발 {total_packs}팩'

    if '마늘쫑' in text:
        parts = ['** 업 소 용 **'] if any(k in text for k in ['대용량', '벌크', '업소용']) else []
        parts.append('마늘쫑')
        parts.append(f'{int(extract_weight(text))}kg')
        return ' '.join(parts)

    if '마늘' in text:
        tags = []
        if any(k in text for k in ['대용량', '벌크', '업소용']) or re.search(r'\b[5-9]\s*kg\b', text):
            tags.append('** 업 소 용 **')
        if '육쪽' in text:
            tags.append('\u2663 육 쪽 \u2663')
        elif '대서' not in text:
            tags.append('대서')
        if '다진마늘' in text:
            tags.append('다진마늘')
        elif '깐마늘' in text:
            tags.append('깐마늘')
        if '특' in text:
            tags.append('특')
        elif '대' in text:
            tags.append('대')
        elif '중' in text:
            tags.append('중')
        elif '소' in text:
            tags.append('소')
        if '꼭지포함' in text:
            tags.append('* 꼭 지 포 함 *')
        elif '꼭지제거' in text:
            tags.append('꼭지제거')
        weight = extract_weight(text)
        if weight:
            tags.append(f'{int(weight)}kg')
        return ' '.join(tags)

    return text

# ----------------------------- Streamlit UI -----------------------------
st.set_page_config(page_title="마늘귀신 ㅣ 올인원 발주 매니저", layout="wide")
st.title("\ud83e\uddc4 마늘귀신 ㅣ 올인원 발주 매니저")

uploaded_files = st.file_uploader("발주서 파일 업로드 (xlsx/xls/csv)", type=["xlsx", "xls", "csv"], accept_multiple_files=True)

if uploaded_files:
    temp_dir = tempfile.mkdtemp()
    cleaned_files = []

    for file in uploaded_files:
        input_path = os.path.join(temp_dir, file.name)
        output_path = os.path.join(temp_dir, f"정제_{file.name}")
        with open(input_path, "wb") as f:
            f.write(file.getbuffer())

        try:
            if file.name.endswith("csv"):
                df = pd.read_csv(input_path)
            else:
                df = pd.read_excel(input_path)

            option_col = detect_option_column(df)

            df[option_col] = df[option_col].fillna("").apply(lambda x: " + ".join(parse_option(s) for s in str(x).split("+") if s))
            df.to_excel(output_path, index=False)
            cleaned_files.append(output_path)
            st.download_button(f"📄 정제된 {file.name}", open(output_path, "rb").read(), file_name=f"정제_{file.name}")
        except Exception as e:
            st.error(f"{file.name} 처리 중 오류 발생: {str(e)}")

    # 패킹리스트
    st.subheader("📦 패킹리스트")
    summary = defaultdict(float)

    for path in cleaned_files:
        df = pd.read_excel(path)
        option_col = detect_option_column(df)
        count_col = next((c for c in df.columns if "수량" in c), None)

        for _, row in df.iterrows():
            options = str(row[option_col]).split(" + ")
            count = row[count_col]
            for opt in options:
                if "마늘가루" in opt:
                    grams = int(re.search(r'(\d+)g', opt).group(1)) if re.search(r'(\d+)g', opt) else 100
                    qty = (grams / 100) * count
                    summary["마늘가루"] += qty
                elif "무뼈닭발" in opt:
                    packs = int(re.search(r'(\d+)팩', opt).group(1)) if re.search(r'(\d+)팩', opt) else 1
                    qty = packs * count
                    summary["무뼈닭발"] += qty
                elif "마늘빠삭이" in opt:
                    pcs = int(re.search(r'(\d+)개입', opt).group(1)) if re.search(r'(\d+)개입', opt) else 10
                    qty = (pcs / 10) * count
                    summary["마늘빠삭이"] += qty
                elif "마늘쫑" in opt:
                    qty = int(re.search(r'(\d+)kg', opt).group(1)) * count if re.search(r'(\d+)kg', opt) else count
                    summary["마늘쫑"] += qty
                else:
                    qty = int(re.search(r'(\d+)kg', opt).group(1)) * count if re.search(r'(\d+)kg', opt) else count
                    summary[opt] += qty

    if summary:
        df_pack = pd.DataFrame([{"상품명": k, "수량": int(v)} for k, v in summary.items()])
        pack_path = os.path.join(temp_dir, "패킹리스트.xlsx")
        df_pack.to_excel(pack_path, index=False)
        st.download_button("📥 패킹리스트 다운로드", open(pack_path, "rb").read(), file_name="패킹리스트.xlsx")
