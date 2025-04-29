# -------------------- 1. 라이브러리 임포트 --------------------
import streamlit as st
import pandas as pd
import os
import re
import tempfile
from collections import defaultdict
from datetime import datetime

# -------------------- 2. Streamlit 기본 설정 --------------------
st.set_page_config(page_title="Garlic Spirit | 올인원 발주 매니저", layout="wide")
st.title("🧄 Garlic Spirit | 올인원 발주 매니저")

# 파일 저장용 임시폴더
TEMP_DIR = tempfile.mkdtemp()
# -------------------- 3. 발주서 옵션 정제 함수 --------------------

def clean_text(text):
    text = str(text)
    text = re.sub(r'[\\[\\](){}]', '', text)
    if '/' in text:
        parts = text.split('/')
        text = parts[-1] if ':' in parts[-1] else parts[0]
    if ':' in text:
        text = text.split(':')[-1]
    return text.strip()

def extract_total_weight(text):
    total = re.search(r'총\\s*(\\d+(\\.\\d+)?)\\s*kg', text.lower())
    if total:
        return float(total.group(1))
    weights = [float(m.group(1)) for m in re.finditer(r'(\\d+(\\.\\d+)?)\\s*kg', text.lower())]
    return sum(weights) if weights else 1.0

def extract_info(text):
    text = clean_text(text)
    lower = text.lower()

    if any(k in lower for k in ['대용량', '벌크', '업소용']) or re.search(r'\\b[5-9]\\s*kg\\b', lower):
        bulk = True
    else:
        bulk = False

    if '마늘' in lower:
        tags = []
        if bulk:
            tags.append('** 업 소 용 **')
        if '육쪽' in lower:
            tags.append('♣ 육 쪽 ♣')
        else:
            tags.append('대서')
        if '다진마늘' in lower:
            tags.append('다진마늘')
        elif '깐마늘' in lower:
            tags.append('깐마늘')
        if '다진마늘' not in lower:
            if '특' in lower:
                tags.append('특')
            elif '대' in lower:
                tags.append('대')
            elif '중' in lower:
                tags.append('중')
            elif '소' in lower:
                tags.append('소')
        if '꼭지포함' in lower:
            tags.append('* 꼭 지 포 함 *')
        elif '꼭지제거' in lower:
            tags.append('꼭지제거')

        total_weight = extract_total_weight(text)
        tags.append(f\"{int(total_weight)}kg\")
        return ' '.join(tags)

    if '마늘쫑' in lower:
        tags = ['** 업 소 용 **'] if bulk else []
        tags.append('마늘쫑')
        total_weight = extract_total_weight(text)
        tags.append(f\"{int(total_weight)}kg\")
        return ' '.join(tags)

    if '무뼈닭발' in lower:
        packs = re.findall(r'(\\d+)\\s*팩', text)
        if not packs:
            grams = extract_total_weight(text) * 1000
            packs = int(grams // 200)
        else:
            packs = sum(map(int, packs))
        return f\"무뼈닭발 {packs}팩\"

    if '마늘빠삭이' in lower:
        pcs = re.search(r'(\\d+)개입', text)
        if pcs:
            return f\"마늘빠삭이 {pcs.group(1)}개입\"
        return '마늘빠삭이'

    if '마늘가루' in lower:
        g = re.search(r'(\\d+)(g|G)', text)
        if g:
            return f\"마늘가루 {g.group(1)}g\"
        return '마늘가루'

    return text
# -------------------- 4. 패킹리스트 생성 함수 --------------------

def generate_packing_list(cleaned_files):
    summary = defaultdict(float)
    unit_table = {
        "마늘가루": 0.1,
        "마늘쫑": 1,
        "무뼈닭발": 0.2,
        "마늘빠삭이": 10,
        "마늘": 1  # 마늘류
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
                if "마늘가루" in opt:
                    match = re.search(r"(\\d+)g", opt)
                    grams = int(match.group(1)) if match else 100
                    qty = (grams / 100) * count
                    summary["마늘가루"] += qty
                elif "무뼈닭발" in opt:
                    match = re.search(r"(\\d+)팩", opt)
                    qty = int(match.group(1)) * count if match else count
                    summary["무뼈닭발"] += qty
                elif "마늘빠삭이" in opt:
                    match = re.search(r"(\\d+)개입", opt)
                    qty = int(match.group(1)) / 10 * count if match else count
                    summary["마늘빠삭이"] += qty
                elif "마늘쫑" in opt:
                    match = re.search(r"(\\d+)kg", opt)
                    qty = int(match.group(1)) * count if match else count
                    summary["마늘쫑"] += qty
                else:
                    match = re.search(r"(\\d+)kg", opt)
                    qty = int(match.group(1)) * count if match else count
                    summary[base] += qty

    df_pack = pd.DataFrame([{"상품명": k, "수량": int(v)} for k, v in summary.items()])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    pack_path = os.path.join(TEMP_DIR, f"패킹리스트_{timestamp}.xlsx")
    df_pack.to_excel(pack_path, index=False)
    return pack_path
# -------------------- 5. 송장리스트 생성 함수 --------------------

def generate_invoice_list(cleaned_files):
    result = []
    for path in cleaned_files:
        df = pd.read_excel(path)
        option_col = next((c for c in df.columns if "옵션" in c), None)
        name_col = next((c for c in df.columns if "수령인" in c or "이름" in c), None)
        zip_col = next((c for c in df.columns if "우편번호" in c), None)
        addr1_col = next((c for c in df.columns if "주소" in c and "상세" not in c), None)
        addr2_col = next((c for c in df.columns if "상세" in c), None)
        phone_col = next((c for c in df.columns if "전화" in c or "휴대폰" in c), None)
        msg_col = next((c for c in df.columns if "배송" in c and "메시지" in c), None)
        count_col = next((c for c in df.columns if "수량" in c), None)

        if not all([option_col, name_col, zip_col, addr1_col, phone_col, count_col]):
            continue

        filename = os.path.basename(path)

        for _, row in df.iterrows():
            result.append({
                "파일출처": filename,
                "수령인": row[name_col],
                "우편번호": row[zip_col],
                "주소": row[addr1_col],
                "상세주소": row[addr2_col] if addr2_col else "",
                "전화번호": row[phone_col],
                "상품명": row[option_col],
                "수량": row[count_col],
                "배송메시지": row[msg_col] if msg_col else ""
            })

    df_invoice = pd.DataFrame(result)
    # 합배송 조건 검사
    duplicates = df_invoice.duplicated(subset=["수령인", "우편번호", "주소", "전화번호"], keep=False)
    df_invoice.loc[duplicates, "수령인"] = "*" + df_invoice.loc[duplicates, "수령인"]

    df_invoice = df_invoice.sort_values(by=["상품명", "수령인"])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    invoice_path = os.path.join(TEMP_DIR, f"송장리스트_{timestamp}.xlsx")
    df_invoice.to_excel(invoice_path, index=False)
    return invoice_path
# -------------------- 6. 메인 실행 흐름 --------------------

uploaded_files = st.file_uploader("발주서 파일 업로드 (.xlsx, .xls, .csv)", type=['xlsx', 'xls', 'csv'], accept_multiple_files=True)

if uploaded_files:
    st.success(f"{len(uploaded_files)}개 파일 업로드 완료!")

    cleaned_paths = []

    for uploaded_file in uploaded_files:
        file_path = os.path.join(TEMP_DIR, uploaded_file.name)
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())

        try:
            df = pd.read_excel(file_path)
        except:
            df = pd.read_csv(file_path, encoding='utf-8')

        option_col = None
        for col in df.columns:
            if any(k in col for k in ['옵션', '옵션명', '옵션정보']):
                option_col = col
                break

        if option_col is None:
            st.error(f"{uploaded_file.name} 파일: 옵션열을 찾을 수 없습니다.")
            continue

        df[option_col] = df[option_col].fillna('').apply(lambda x: ' + '.join(extract_info(opt.strip()) for opt in str(x).split('+') if opt.strip()))
        cleaned_path = os.path.join(TEMP_DIR, f"정제_{uploaded_file.name.split('.')[0]}.xlsx")
        df.to_excel(cleaned_path, index=False)
        cleaned_paths.append(cleaned_path)

        st.download_button(f"📄 정제 파일 다운로드 - {uploaded_file.name}", open(cleaned_path, 'rb').read(), file_name=f"정제_{uploaded_file.name}")

    if cleaned_paths:
        st.subheader("📦 패킹리스트 / 송장리스트 생성")

        pack_path = generate_packing_list(cleaned_paths)
        invoice_path = generate_invoice_list(cleaned_paths)

        st.download_button("📥 패킹리스트 다운로드", open(pack_path, "rb").read(), file_name=os.path.basename(pack_path))
        st.download_button("🚚 송장리스트 다운로드", open(invoice_path, "rb").read(), file_name=os.path.basename(invoice_path))
