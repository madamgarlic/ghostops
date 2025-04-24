# ghostops_all_in_one.py
import streamlit as st
import pandas as pd
import tempfile
import os
import re
from collections import defaultdict

st.set_page_config(page_title="ghostops ALL", layout="wide")
st.title("🧄 ghostops | 올인원 자동화 시스템")
st.info("📥 발주서 파일을 업로드하면 자동 정제가 시작됩니다.")

SIZES = ["특", "대", "중", "소"]
WEIGHT_PATTERN = r"(\d+(\.\d+)?)(kg|g|개입|팩|그램)"

def extract_last(text):
    if ":" in text:
        text = text.split(":")[-1].strip()
    if "/" in text:
        parts = text.split("/")
        if any(":" in p for p in parts[1:]):
            for p in parts[1:]:
                if ":" in p:
                    return p.split(":")[-1].strip()
        else:
            return parts[0].strip()
    return text.strip()

def parse_garlic(text: str) -> str:
    tags = []
    t = extract_last(text.lower())
    if any(x in t for x in ["업소용", "벌크", "대용량"]) or re.search(r"\b[5-9]\s*kg\b", t):
        tags.append("** 업 소 용 **")
    if "육쪽" in t:
        tags.append("♣ 육 쪽 ♣")
    else:
        tags.append("대서")
    if "깐마늘" in t:
        tags.append("깐마늘")
    elif "다진마늘" in t:
        tags.append("다진마늘")
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
        tags.append(f"{match.group(1).lower()}{match.group(3).lower()}")
    return " ".join(tags)

def parse_dakbal(text: str) -> str:
    t = extract_last(text.lower())
    pack_count = sum(map(int, re.findall(r"(\d+)팩", t)))
    grams = sum(map(int, re.findall(r"(\d+)g", t))) + sum(map(int, re.findall(r"(\d+)그램", t)))
    pack_count += round(grams / 200)
    return f"무뼈닭발 {pack_count}팩"

def parse_pasak(text: str) -> str:
    t = extract_last(text.lower())
    match = re.search(r"(\d+)(개입|개)", t)
    if match:
        return f"마늘빠삭이 {match.group(1)}개입"
    return "마늘빠삭이"

def parse_maneuljjong(text: str) -> str:
    t = extract_last(text.lower())
    result = []
    if any(x in t for x in ["업소용", "벌크", "대용량"]) or re.search(r"\b[5-9]\s*kg\b", t):
        result.append("** 업 소 용 **")
    match = re.search(WEIGHT_PATTERN, t)
    if match:
        result.append(f"마늘쫑 {match.group(1).lower()}{match.group(3).lower()}")
    return " ".join(result)

def parse_powder(text: str) -> str:
    t = extract_last(text.lower())
    match = re.search(WEIGHT_PATTERN, t)
    if match:
        return f"마늘가루 {match.group(1).lower()}{match.group(3).lower()}"
    return "마늘가루"

def parse_option(text: str) -> list:
    parts = re.split(r"\+|/", text)
    result = []
    for part in parts:
        part = part.strip()
        if "무뼈닭발" in part:
            result.append(parse_dakbal(part))
        elif "마늘빠삭이" in part:
            result.append(parse_pasak(part))
        elif "마늘쫑" in part:
            result.append(parse_maneuljjong(part))
        elif "마늘가루" in part:
            result.append(parse_powder(part))
        elif any(x in part for x in ["깐마늘", "다진마늘"]):
            result.append(parse_garlic(part))
        else:
            result.append(part)
    return result

uploaded_files = st.file_uploader("발주서 파일 업로드 (.xlsx)", type="xlsx", accept_multiple_files=True)

if uploaded_files:
    st.success(f"{len(uploaded_files)}개 파일 업로드됨!")
    temp_dir = tempfile.mkdtemp()

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

        with open(output_path, "rb") as f:
            st.download_button(
                label=f"📄 정제파일 다운로드 - {file.name}",
                data=f.read(),
                file_name=f"정제_{file.name}"
            )
