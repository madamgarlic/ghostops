import streamlit as st
import pandas as pd
import tempfile
import os
from parsers.order_cleaner import clean_order_file
from generators.packing_list import generate_packing_list
from generators.invoice_list import generate_invoice_and_summary

# 옵션 열 자동 탐지 함수
def detect_option_column(df, possible_names=["옵션", "옵션정보", "상세정보", "옵션명"]) -> str:
    for name in possible_names:
        if name in df.columns:
            return name
    raise ValueError("옵션 열을 찾을 수 없습니다. ('옵션정보', '옵션', '옵션명', '상세정보' 중 하나 필요)")

# 페이지 설정
st.set_page_config(page_title="ghostops 자동화", layout="wide")
st.title("🧄 ghostops | 마늘귀신 발주 자동화 시스템")

# 파일 업로드
uploaded_files = st.file_uploader("발주서 파일 업로드 (.xlsx)", type="xlsx", accept_multiple_files=True)

if uploaded_files:
    st.success(f"{len(uploaded_files)}개 파일 업로드됨!")

    temp_dir = tempfile.mkdtemp()
    cleaned_files = []

    for file in uploaded_files:
        input_path = os.path.join(temp_dir, file.name)
        output_path = os.path.join(temp_dir, f"정제_{file.name}")
        with open(input_path, "wb") as f:
            f.write(file.getbuffer())

        # 옵션 열 자동 감지 및 정제 처리
        df_temp = pd.read_excel(input_path)
        option_col_name = detect_option_column(df_temp)
        clean_order_file(input_path, output_path, option_col_name)
        cleaned_files.append(output_path)

        # 💾 정제된 개별 파일 다운로드 버튼 표시
        with open(output_path, "rb") as f:
            st.download_button(
                label=f"📄 정제파일 다운로드 - {file.name}",
                data=f.read(),
                file_name=f"정제_{file.name}",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # 패킹리스트 생성
    packing_path = os.path.join(temp_dir, "패킹리스트.xlsx")
    generate_packing_list(cleaned_files[0], packing_path)

    # 송장리스트 및 요약 생성
    invoice_path = os.path.join(temp_dir, "송장리스트.xlsx")
    summary_path = os.path.join(temp_dir, "송장요약.xlsx")
    generate_invoice_and_summary(cleaned_files, invoice_path, summary_path)

    # 결과 다운로드
    st.header("📤 결과 다운로드")
    st.download_button("📦 패킹리스트 다운로드", open(packing_path, "rb").read(), file_name="패킹리스트.xlsx")
    st.download_button("🚚 송장리스트 다운로드", open(invoice_path, "rb").read(), file_name="송장리스트.xlsx")
    st.download_button("🧾 요약시트 다운로드", open(summary_path, "rb").read(), file_name="송장요약.xlsx")

    st.info("모든 파일은 서버에 임시 저장되며 앱 종료 시 자동 삭제됩니다.")
