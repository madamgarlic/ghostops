# ghostops_all_in_one.py
import streamlit as st
import pandas as pd
import tempfile
import os
import re
from collections import defaultdict

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

# -- 이하 Streamlit UI 및 처리 로직은 동일 -- (생략하지 않음, 필요 시 다시 포함)
# 기존 ghostops_all_in_one.py 코드의 Streamlit 부분을 여기에 이어붙이면 됩니다.
