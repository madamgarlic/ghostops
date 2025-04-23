import pandas as pd
import os
from collections import defaultdict

REQUIRED_COLUMNS = ["수령인", "우편번호", "주소", "상세주소", "전화번호", "옵션", "수량", "배송메세지"]


def generate_invoice_and_summary(input_files: list, invoice_path: str, summary_path: str) -> None:
    all_rows = []
    summary_count = defaultdict(int)
    file_sources = []

    for file in input_files:
        df = pd.read_excel(file)
        filename = os.path.basename(file)

        # 필수 열 확인
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            raise ValueError(f"{filename} 파일에 필수 열이 없습니다: {', '.join(missing_cols)}")

        # 송장 데이터 추출
        for _, row in df.iterrows():
            recipient = row["수령인"]
            zipcode = row["우편번호"]
            addr1 = row["주소"]
            addr2 = row.get("상세주소", "")
            phone = row["전화번호"]
            product = row["옵션"]
            qty = row["수량"]
            msg = row.get("배송메세지", "")

            all_rows.append({
                "수령인": recipient,
                "우편번호": zipcode,
                "주소": addr1,
                "상세주소": addr2,
                "전화번호": phone,
                "상품명": product,
                "수량": qty,
                "배송메세지": msg,
                "파일출처": filename
            })

            summary_count[product] += qty

    # 송장 시트 저장
    invoice_df = pd.DataFrame(all_rows)

    # 합배송 조건부 포맷 컬럼 추가 (동일인/주소일 경우 색상 강조용)
    invoice_df["합배송확인"] = invoice_df.groupby(["수령인", "전화번호", "주소"]).cumcount().apply(lambda x: "Y" if x > 0 else "")

    invoice_df.to_excel(invoice_path, index=False)

    # 요약 시트 저장
    summary_df = pd.DataFrame([{
        "상품명": name,
        "총건수": count
    } for name, count in summary_count.items()])

    summary_df.sort_values(by="상품명", inplace=True)
    summary_df.to_excel(summary_path, index=False)

    print(f"✅ 송장리스트 저장 완료: {invoice_path}")
    print(f"✅ 요약시트 저장 완료: {summary_path}")
