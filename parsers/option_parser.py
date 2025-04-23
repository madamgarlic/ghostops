import re

SIZES = ["소", "중", "대"]
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

    if "업소용" in t or "벌크" in t or "대용량" in t or re.search(r"\b[5-9]\s*kg\b", t):
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

    if "다진마늘" not in t:
        for size in SIZES:
            if size in t:
                tags.append(size)
                break

    if "꼭지포함" in t or "꼭지 포함" in t:
        tags.append("* 꼭 지 포 함 *")

    match = re.search(WEIGHT_PATTERN, t)
    if match:
        tags.append(f"{match.group(1)}{match.group(3)}")

    return " ".join(tags)

def parse_dakbal(text: str) -> str:
    t = text.lower()
    if ":" in t:
        t = t.split(":")[-1].strip()
    if "/" in t:
        t = t.split("/")[0].strip()

    pack_count = sum(map(int, re.findall(r"(\d+)팩", t)))
    grams = sum(map(int, re.findall(r"(\d+)g", t)))
    pack_count += round(grams / 200)
    return f"무뼈닭발 {pack_count}팩"

def parse_special(text: str) -> str:
    t = text.lower()
    if ":" in t:
        t = t.split(":")[-1].strip()
    if "/" in t:
        t = t.split("/")[0].strip()

    if "마늘빠삭이" in t:
        match = re.search(r"(\d+)(개입|개)", t)
        if match:
            return f"마늘빠삭이 {match.group(1)}개입"
    elif "마늘가루" in t:
        match = re.search(WEIGHT_PATTERN, t)
        if match:
            return f"마늘가루 {match.group(1)}{match.group(3)}"
    return t.strip()

def parse_option(text: str) -> list:
    parts = re.split(r"\+|/", text)
    result = []
    for part in parts:
        part = part.strip()
        if "무뼈닭발" in part:
            result.append(parse_dakbal(part))
        elif any(x in part for x in ["깐마늘", "다진마늘", "마늘쫑"]):
            result.append(parse_garlic(part))
        elif "마늘가루" in part or "마늘빠삭이" in part:
            result.append(parse_special(part))
        else:
            result.append(part)
    return result
