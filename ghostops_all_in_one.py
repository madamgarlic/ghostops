# ghostops_all_in_one.py
import streamlit as st
import pandas as pd
import tempfile
import os
import re
from collections import defaultdict

SIZES = ["특", "대", "중", "소"]
WEIGHT_PATTERN = r"(\d+(\.\d+)?)(kg|g|개입|팩|그램)"

# --- 옵션 정제 함수 (생략부 동일) ---
# ... [parse 함수들 그대로 유지] ...

# --- Streamlit 앱 시작 ---
st.set_page_config(page_title="ghostops ALL", layout="wide")
st.title("🧄 ghostops | 올인원 자동화 시스템")

# ✅ 초기 실행 상태 안내 메시지
st.info("📥 발주서 파일을 업로드하면 자동 정제가 시작됩니다.")

uploaded_files = st.file_uploader("발주서 파일 업로드 (.xlsx)", type="xlsx", accept_multiple_files=True)

if uploaded_files:
    st.success(f"{len(uploaded_files)}개 파일 업로드됨!")
    temp_dir = tempfile.mkdtemp()
    cleaned_files = []
    summary_count = defaultdict(int)
    all_invoice_rows = []

    for file in uploaded_files:
        input_path = os.path.join(temp_dir, file.name)
        output_path = os.path.join(temp_dir, f"정제_{file.name}")
        df = pd.read_excel(file)

        option_col = next((col for col in ["옵션", "옵션명", "옵션정보"] if col in df.columns), None)
        if not option_col:
            st.error(f"{file.name}: 옵션 관련 열이 없습니다.")
            continue

        df[option_col] = df[option_col].fillna("").apply(lambda x: " + ".join(parse_option(str(x))))
        df.to_excel(output_path, index=False)
        cleaned_files.append(output_path)

        with open(output_path, "rb") as f:
            st.download_button(
                label=f"📄 정제파일 다운로드 - {file.name}",
                data=f.read(),
                file_name=f"정제_{file.name}"
            )

        for _, row in df.iterrows():
            if all(k in df.columns for k in ["수령인", "우편번호", "주소", "상세주소", "전화번호", "수량", "배송메세지"]):
                all_invoice_rows.append({
                    "수령인": row["수령인"],
                    "우편번호": row["우편번호"],
                    "주소": row["주소"],
                    "상세주소": row.get("상세주소", ""),
                    "전화번호": row["전화번호"],
                    "상품명": row[option_col],
                    "수량": row["수량"],
                    "배송메세지": row.get("배송메세지", ""),
                    "파일출처": file.name
                })