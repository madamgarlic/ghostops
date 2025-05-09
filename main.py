import streamlit as st
import tempfile
import os
from garlic_cleaner import clean_order_file

st.set_page_config(page_title="마늘귀신 | 옵션 정제기", layout="wide")
st.title("🧄 마늘귀신 | 옵션 정제기")

uploaded_files = st.file_uploader("발주서 업로드 (.xlsx, .xls, .csv)", type=["xlsx", "xls", "csv"], accept_multiple_files=True)

if uploaded_files:
    st.success(f"{len(uploaded_files)}개 파일 업로드 완료")

    temp_dir = tempfile.mkdtemp()
    for file in uploaded_files:
        input_path = os.path.join(temp_dir, file.name)
        output_path = os.path.join(temp_dir, f"정제_{file.name}")

        with open(input_path, "wb") as f:
            f.write(file.getbuffer())

        try:
            clean_order_file(input_path, output_path)
            with open(output_path, "rb") as f:
                st.download_button(f"📥 정제된 파일 다운로드: {file.name}", f.read(), file_name=f"정제_{file.name}")
        except Exception as e:
            st.error(f"{file.name} 정제 중 오류 발생: {str(e)}")
