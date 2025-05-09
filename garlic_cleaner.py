# garlic_cleaner.py (정제기 올인원 버전)
import streamlit as st
import pandas as pd
import re
import tempfile
import os

# -----------------------------
# 📦 공통 세팅
# -----------------------------
st.set_page_config(page_title="마늘귀신 | 정제기", layout="wide")
st.title("🧄 마늘귀신 | 옵션 정제기")

uploaded_files = st.file_uploader("발주서 업로드 (.xlsx, .xls, .csv)", type=["xlsx", "xls", "csv"], accept_multiple_files=True)

# -----------------------------
# 🧠 정제 조건 함수 정의
# -----------------------------
def remove_brackets_keep_content(text):
    return re.sub(r"[\[\](){}]", "", text)

def drop_brackets_weight_only(text):
    return re.sub(r"\(총?\s?\d+(\.\d+)?\s*(kg|g|개|팩)\)", "", text)

def clean_split_text(text):
    if ":" in text and "/" in text:
        text = text.split("/")[-1]
        return text.split(":")[-1].strip()
    elif ":" in text:
        return text.split(":")[-1].strip()
    elif "/" in text:
        return text.split("/")[0].strip()
    return text.strip()

def extract_weight(text):
    matches = re.findall(r"(\d+(\.\d+)?)\s*(kg|g|개|팩)", text.lower())
    total = 0
    for num, _, unit in matches:
        val = float(num)
        if unit == "g":
            val /= 1000
        elif unit == "개":
            val /= 10
        elif unit == "팩":
            val *= 0.2
        total += val
    return total

def extract_packs(text):
    matches = re.findall(r"(\d+)\s*팩", text)
    return sum(map(int, matches)) if matches else int((extract_weight(text) * 1000) // 200)

def extract_pcs(text):
    match = re.search(r"(\d+)개입", text)
    return int(match.group(1)) if match else None
import re

# ---------------- 공통 정제 도우미 ----------------
def clean_text(text: str) -> str:
    text = re.sub(r"[\[\]{}]", "", text)  # 대괄호, 중괄호 제거
    text = re.sub(r"\s+", " ", text)  # 중복 공백 제거
    return text.strip()

def remove_weight_from_text(text: str) -> str:
    return re.sub(r"(\d+(\.\d+)?)(kg|g|개입|팩)", "", text, flags=re.IGNORECASE).strip()

def extract_total_kg(text: str) -> float:
    weights = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*kg", text.lower())]
    return sum(weights)

def extract_total_g(text: str) -> float:
    grams = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*g", text.lower())]
    return sum(grams)

def extract_total_pack(text: str) -> int:
    packs = [int(x) for x in re.findall(r"(\d+)\s*팩", text)]
    return sum(packs)

def extract_total_piece(text: str) -> int:
    pcs = [int(x) for x in re.findall(r"(\d+)\s*개입", text)]
    return sum(pcs)

def has_bulk_tag(text: str) -> bool:
    # 10kg 이상 또는 키워드
    if re.search(r"\b(10|1[1-9]|\d{3,})\s*kg\b", text.lower()):
        return True
    return False

def clean_brackets(text: str) -> str:
    # 괄호 안에 무게 정보가 있을 경우 제거, 아닐 경우 괄호 제거
    new_text = re.sub(r"\(([^)]*?(?:\d+(?:\.\d+)?\s*(kg|g|개입|팩|박스)))\)", "", text, flags=re.IGNORECASE)
    new_text = re.sub(r"[()]", "", new_text)
    return new_text
# ---------------- 카테고리별 정제 로직 ----------------
def parse_manutype(text: str) -> str:
    tag = []

    # 업소용 여부
    if has_bulk_tag(text):
        tag.append("** 업 소 용 **")

    # 품종
    if "육쪽" in text:
        tag.append("♣ 육 쪽 ♣")
    elif "대서" in text or "대서마늘" in text:
        tag.append("대서")
    else:
        tag.append("대서")  # 디폴트 품종

    # 형태
    if "다진" in text or "다진마늘" in text:
        tag.append("다진마늘")
    elif "통" in text:
        tag.append("통마늘")
    elif "깐" in text:
        tag.append("깐마늘")
    else:
        tag.append("깐마늘")

    # 크기
    if "특" in text:
        tag.append("특")
    elif "대" in text:
        tag.append("대")
    elif "중" in text:
        tag.append("중")
    elif "소" in text:
        tag.append("소")

    # 꼭지 여부
    if "꼭지포함" in text:
        tag.append("* 꼭 지 포 함 *")
    elif "꼭지제거" in text:
        tag.append("꼭지제거")

    # 무게
    kg = extract_total_kg(text)
    tag.append(f"{int(kg)}kg" if kg else "1kg")

    return " ".join(tag)

def parse_chong(text: str) -> str:
    tag = []
    if has_bulk_tag(text):
        tag.append("** 업 소 용 **")
    tag.append("마늘쫑")
    kg = extract_total_kg(text)
    tag.append(f"{int(kg)}kg" if kg else "1kg")
    return " ".join(tag)

def parse_dakbal(text: str) -> str:
    pack = extract_total_pack(text)
    if not pack:
        grams = extract_total_g(text)
        pack = int(round(grams / 200)) if grams else 1
    return f"무뼈닭발 {pack}팩"

def parse_ppasak(text: str) -> str:
    pcs = extract_total_piece(text)
    box = int(pcs / 10) if pcs else 1
    return f"마늘빠삭이 {box}박스"

def parse_garu(text: str) -> str:
    gram = extract_total_g(text)
    unit = int(round(gram / 100)) if gram else 1
    return f"마늘가루 {unit}개"

# ---------------- 최종 카테고리 분류 적용 함수 ----------------
def parse_by_category(text: str) -> str:
    t = text.lower()
    if "빠삭" in t:
        return parse_ppasak(text)
    elif "닭발" in t:
        return parse_dakbal(text)
    elif "가루" in t:
        return parse_garu(text)
    elif "쫑" in t:
        return parse_chong(text)
    elif "마늘" in t:
        return parse_manutype(text)
    else:
        return text.strip()

# ---------------- 옵션 셀 정제 함수 ----------------
def clean_option_cell(option: str) -> str:
    if not isinstance(option, str) or option.strip() == "":
        return ""
    
    cleaned = []
    segments = re.split(r"\s*\+\s*", option)

    for seg in segments:
        text = remove_brackets(seg)
        text = extract_colon_slash(text)
        cleaned.append(parse_by_category(text))

    return " + ".join(cleaned)