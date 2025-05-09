import streamlit as st
import tempfile
import os
from garlic_cleaner import clean_order_file

st.set_page_config(page_title="마늘귀신 | 옵션 정제기", layout="wide")
st.title("🧄 마늘귀신 | 옵션 정제기")
st.caption("발주서 업로드 (.xlsx, .xls, .csv)")

uploaded_files = st.file_uploader("Drag and drop files here", type=["xlsx", "xls", "csv"], accept_multiple_files=True)

if uploaded_files:
    st.success(f"{len(uploaded_files)}개 파일 업로드 완료")
    temp_dir = tempfile.mkdtemp()

    for uploaded_file in uploaded_files:
        input_path = os.path.join(temp_dir, uploaded_file.name)
        output_path = os.path.join(temp_dir, f"정제_{uploaded_file.name}")

        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        try:
            clean_order_file(input_path, output_path)
            with open(output_path, "rb") as f:
                st.download_button(
                    label=f"📥 정제된 파일 다운로드: 정제_{uploaded_file.name}",
                    data=f,
                    file_name=f"정제_{uploaded_file.name}",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
        except Exception as e:
            st.error(f"{uploaded_file.name} 정제 중 오류 발생: {e}")
