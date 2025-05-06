# garlic_cleaner.py
import streamlit as st
import pandas as pd
import os
import re
import tempfile

# 1. 무게 추출 보조 함수
def extract_total_weight(text: str) -> float:
    match = re.search(r"총\s*(\d+(\.\d+)?)\s*kg", text.lower())
    if match:
        return float(match.group(1))
    weights = [float(m.group(1)) for m in re.finditer(r"(\d+(\.\d+)?)\s*kg", text.lower())]
    return sum(weights)

# 2. 정제 핵심 함수
def parse_option(text: str) -> str:
    text = re.sub(r"[\[\](){}]", "", text)
    text = text.lower()

    # 2-1. 마늘류
    if "마늘" in text:
        tags = []
        if any(k in text for k in ["대용량", "업소용", "벌크"]) or re.search(r"\b[5-9]\s*kg\b", text):
            tags.append("** 업 소 용 **")
        if "육쪽" in text:
            tags.append("♣ 육 쪽 ♣")
        elif "대서" not in text:
            tags.append("대서")
        if "다진마늘" in text:
            tags.append("다진마늘")
        elif "깐마늘" in text:
            tags.append("깐마늘")
        elif "통마늘" in text:
            tags.append("통마늘")
        if "특" in text:
            tags.append("특")
        elif "대" in text:
            tags.append("대")
        elif "중" in text:
            tags.append("중")
        elif "소" in text:
            tags.append("소")
        if "꼭지포함" in text:
            tags.append("* 꼭 지 포 함 *")
        elif "꼭지제거" in text:
            tags.append("꼭지제거")
        tags.append(f"{int(extract_total_weight(text))}kg")
        return " ".join(tags)

    # 2-2. 마늘쫑
    if "마늘쫑" in text:
        tags = []
        if any(k in text for k in ["대용량", "업소용", "벌크"]) or re.search(r"\b[5-9]\s*kg\b", text):
            tags.append("** 업 소 용 **")
        tags.append("마늘쫑")
        tags.append(f"{int(extract_total_weight(text))}kg")
        return " ".join(tags)

    # 2-3. 무뼈닭발
    if "무뼈닭발" in text:
        match = re.search(r"(\d+)\s*팩", text)
        count = int(match.group(1)) if match else int(extract_total_weight(text) * 1000 // 200)
        return f"무뼈닭발 {count}팩"

    # 2-4. 마늘빠삭이
    if "마늘빠삭이" in text:
        pcs = re.search(r"(\d+)\s*개입", text)
        return f"마늘빠삭이 {pcs.group(1)}개입" if pcs else "마늘빠삭이"

    # 2-5. 마늘가루
    if "마늘가루" in text:
        match = re.search(r"(\d+)\s*g", text)
        return f"마늘가루 {match.group(1)}g" if match else "마늘가루"

    return text.strip()

# 3. Streamlit 인터페이스
st.set_page_config(page_title="garlic spirit | 정제기", layout="centered")
st.title("🧄 garlic spirit | 정제 전용기")

uploaded_file = st.file_uploader("발주서 파일 업로드 (.xlsx, .xls, .csv)", type=["xlsx", "xls", "csv"])

if uploaded_file:
    st.success("✅ 파일 업로드 완료")
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, uploaded_file.name)

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    try:
        try:
            df = pd.read_excel(file_path)
        except:
            df = pd.read_csv(file_path, encoding='utf-8')

        # 옵션 열 자동 탐색
        option_col = next((c for c in df.columns if any(k in c for k in ["옵션", "옵션정보", "옵션명"])), None)

        if not option_col:
            st.error("❌ 옵션열을 찾을 수 없습니다.")
        else:
            df[option_col] = df[option_col].fillna("").apply(
                lambda x: " + ".join(parse_option(p.strip()) for p in str(x).split("+"))
            )
            output_path = os.path.join(temp_dir, f"정제_{uploaded_file.name}")
            df.to_excel(output_path, index=False)

            st.download_button(
                label="📥 정제된 파일 다운로드",
                data=open(output_path, "rb").read(),
                file_name=f"정제_{uploaded_file.name}",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"❌ 처리 중 오류 발생: {e}")
