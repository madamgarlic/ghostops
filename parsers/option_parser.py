import re

def clean_option_text(option: str) -> str:
    """
    옵션 문자열을 정제하여 핵심 정보만 추출합니다.
    특수 표기, 혼합 상품, 불필요 텍스트 제거 포함
    """
    original = option.strip()
    option = option.lower().strip()

    # 특수표기 (업소용 / 꼭지포함 / 육쪽)
    if "업소용" in option:
        option = "** 업 소 용 ** " + option
    if "꼭지" in option and "포함" in option:
        option = "* 꼭 지 포 함 * " + option
    if "육쪽" in option:
        option = option.replace("육쪽", "♣ 육 쪽 ♣")

    # 불필요 텍스트 제거
    option = re.sub(r"(품종 선택:|크기 선택:)", "", option)
    option = re.sub(r"[()]", "", option)
    option = re.sub(r"예약.*", "", option)
    option = re.sub(r"\s+", " ", option).strip()

    return option

def split_combined_options(option: str) -> list:
    """
    옵션 내 여러 상품이 혼합된 경우 분리
    예: '깐마늘 1KG + 마늘가루 200g' → ['깐마늘 1KG', '마늘가루 200g']
    """
    parts = re.split(r"\s*[+/]\s*", option)
    return [clean_option_text(p) for p in parts if p.strip()]

def parse_option(option: str) -> list:
    """
    최종 옵션 정제 함수
    """
    if "+" in option or "/" in option:
        return split_combined_options(option)
    else:
        return [clean_option_text(option)]
