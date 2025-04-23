# ghostops_all_in_one.py
import streamlit as st
import pandas as pd
import tempfile
import os
import re
from collections import defaultdict

# ---------------- 옵션 정제 ----------------
SIZES = ["특", "대", "중", "소"]
WEIGHT_PATTERN = r"(\d+(\.\d+)?)(kg|g|개입|팩)"


def parse_garlic(text: str) -> str:
    tags = []
    t = text.lower()

    if ":" in t:
        t = t.split(":")[-1].strip()
    if "/" in t:
        parts = t.split("/")
        if any(":" in p for p in parts[1:]):
            for p in parts[1:]:
                if ":" in p:
                    t = p.split(":")[-1].strip()
                    break
        else:
            t = parts[0].strip()

    if any(x in t for x in ["업소용", "벌크", "대용량"]) or re.search(r"\b[5-9]\s*kg\b", t):
        tags.append("** 업 소 용 **")

    if "육쪽" in t:
        tags.append("♣ 육 쪽 ♣")
    elif "깐마늘" in t or "다진마늘" in t:
        tags.append("대서")

    if "깐마늘" in t:
        tags.append("깐마늘")
    elif "다진마늘" in t:
        tags.append("다진마늘")
    elif "마늘쫑" in t:
        tags.append("마늘쫑")

    for size in SIZES:
        if size in t:
            tags.append(size)
            break

    if "꼭지포함" in t or "꼭지 포함" in t:
        tags.append("* 꼭 지 포 함 *")
    elif "꼭지제거" in t:
        tags.append("꼭지제거")

    match = re.search(WEIGHT_PATTERN, t)
    if match:
        tags.append(f"{match.group(1)}{match.group(3)}")

    return " ".join(tags)


def parse_option(text: str) -> list:
    parts = re.split(r"\+|/", text)
    result = []
    for part in parts:
        part = part.strip()
        if any(x in part for x in ["깐마늘", "다진마늘", "마늘쫑"]):
            result.append(parse_garlic(part))
        else:
            result.append(part)
    return result

# ---------------- Streamlit ----------------
st.set_page_config(page_title="ghostops ALL", layout="wide")
st.title("🧄 ghostops | 올인원 자동화 시스템")

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

        # 옵션열 탐색
        option_col = next((col for col in ["옵션", "옵션명", "옵션정보"] if col in df.columns), None)
        if not option_col:
            st.error(f"{file.name}: 옵션 관련 열이 없습니다.")
            continue

        # 옵션 정제 수행
        df[option_col] = df[option_col].fillna("").apply(lambda x: " / ".join(parse_option(str(x))))
        df.to_excel(output_path, index=False)
        cleaned_files.append(output_path)

        with open(output_path, "rb") as f:
            st.download_button(
                label=f"📄 정제파일 다운로드 - {file.name}",
                data=f.read(),
                file_name=f"정제_{file.name}"
            )

        # 송장 및 요약 데이터 준비
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
                summary_count[row[option_col]] += row["수량"]

    # 송장리스트 출력
    invoice_df = pd.DataFrame(all_invoice_rows)
    invoice_df["합배송확인"] = invoice_df.groupby(["수령인", "전화번호", "주소"]).cumcount().apply(lambda x: "Y" if x > 0 else "")
    invoice_path = os.path.join(temp_dir, "송장리스트.xlsx")
    invoice_df.to_excel(invoice_path, index=False)

    summary_df = pd.DataFrame([{"상품명": name, "총건수": count} for name, count in summary_count.items()])
    summary_df.sort_values(by="상품명", inplace=True)
    summary_path = os.path.join(temp_dir, "송장요약.xlsx")
    summary_df.to_excel(summary_path, index=False)

    st.header("📤 다운로드")
    st.download_button("🚚 송장리스트 다운로드", open(invoice_path, "rb").read(), file_name="송장리스트.xlsx")
    st.download_button("🧾 요약시트 다운로드", open(summary_path, "rb").read(), file_name="송장요약.xlsx")

    st.info("⚠️ 모든 파일은 서버에 임시 저장되며 앱 종료 시 삭제됩니다.")
