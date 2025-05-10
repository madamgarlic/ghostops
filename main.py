# main.py
import streamlit as st
import tempfile
import os
from garlic_cleaner import clean_excel_file

st.set_page_config(page_title="Garlic Spirit | 정제기", layout="wide")
st.title("🧄 Garlic Spirit | 마늘귀신 정제 시스템")

uploaded_files = st.file_uploader("발주서 업로드 (.xlsx, .xls)", type=["xlsx", "xls"], accept_multiple_files=True)

if uploaded_files:
    st.success(f"{len(uploaded_files)}개 파일 업로드 완료")

    temp_dir = tempfile.mkdtemp()
    for file in uploaded_files:
        input_path = os.path.join(temp_dir, file.name)
        output_path = os.path.join(temp_dir, f"정제_{file.name}")
        
        with open(input_path, "wb") as f:
            f.write(file.getbuffer())

        try:
            clean_excel_file(input_path, output_path)
            with open(output_path, "rb") as f:
                st.download_button(
                    label=f"📥 정제된 파일 다운로드: 정제_{file.name}",
                    data=f,
                    file_name=f"정제_{file.name}",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        except Exception as e:
            st.error(f"{file.name} 처리 중 오류 발생: {str(e)}")
