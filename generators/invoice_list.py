import pandas as pd
from collections import defaultdict

def generate_invoice_and_summary(input_paths: list, output_invoice_path: str, output_summary_path: str, option_col: str = "정제옵션", count_col: str = "수량") -> None:
    """
    여러 발주서를 통합하여 송장리스트 및 요약 시트를 생성합니다.

    input_paths: 정제된 발주서 파일 목록
    output_invoice_path: 송장리스트 저장 경로
    output_summary_path: 요약 시트 저장 경로
    """
    all_data = []
    summary_count = defaultdict(int)
    unique_recipients = set()
    source_map = {}

    for path in input_paths:
        df = pd.read_excel(path)
        filename = path.split("/")[-1]

        if option_col not in df.columns or count_col not in df.columns:
            raise ValueError(f"{filename} 파일에 필수 열이 없습니다.")

        for _, row in df.iterrows():
            name = str(row.get("수령인", ""))
            phone = str(row.get("전화번호", ""))
            zip_code = str(row.get("우편번호", ""))
            addr1 = str(row.get("주소", ""))
            addr2 = str(row.get("상세주소", "")) if "상세주소" in row else ""
            message = str(row.get("배송메세지", ""))
            options = str(row[option_col]).split(" / ")
            count = row[count_col]

            for opt in options:
                all_data.append({
                    "수령인": name,
                    "전화번호": phone,
                    "우편번호": zip_code,
                    "주소": addr1,
                    "상세주소": addr2,
                    "상품명": opt.strip(),
                    "수량": count,
                    "배송메세지": message,
                    "파일출처": filename
                })
                summary_count[opt.strip()] += 1
                unique_recipients.add((name, phone, addr1))

    # 송장리스트 출력
    invoice_df = pd.DataFrame(all_data)
    invoice_df.sort_values(by="상품명", inplace=True)
    invoice_df.to_excel(output_invoice_path, index=False)

    # 요약 시트 생성
    summary_df = pd.DataFrame([{"상품명": k, "송장 건수": v} for k, v in sorted(summary_count.items())])
    summary_df.loc[len(summary_df.index)] = {"상품명": "[합배송 주문 건수]", "송장 건수": f"{len(all_data) - len(unique_recipients)}건"}
    summary_df.loc[len(summary_df.index)] = {"상품명": "[전체 예상 송장 출력 건수]", "송장 건수": f"{len(unique_recipients)}장"}
    summary_df.to_excel(output_summary_path, index=False)

    print(f"✅ 송장리스트 저장 완료: {output_invoice_path}")
    print(f"✅ 요약시트 저장 완료: {output_summary_path}")
