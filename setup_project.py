import os

folders = [
    "parsers",
    "generators",
    "utils",
    "templates"
]

files = {
    "main.py": "",
    "requirements.txt": "openpyxl\npandas\n",
    "README.md": "# GhostOps\n\n마늘귀신 내부 발주 자동화 시스템 프로젝트.",
    "parsers/option_parser.py": "# 옵션 정제 로직",
    "parsers/order_cleaner.py": "# 발주서 구조 정제 로직",
    "generators/packing_list.py": "# 패킹리스트 생성 로직",
    "generators/invoice_list.py": "# 송장리스트 및 요약시트 생성 로직",
    "utils/excel_io.py": "# 엑셀 입출력 유틸",
    "utils/merge_utils.py": "# 병합 및 그룹화 유틸리티"
}

for folder in folders:
    os.makedirs(folder, exist_ok=True)

for path, content in files.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print("✅ ghostops 프로젝트 초기 구조 생성 완료!")
