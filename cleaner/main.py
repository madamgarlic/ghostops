from parsers.order_cleaner import clean_order_file
from generators.packing_list import generate_packing_list
from generators.invoice_list import generate_invoice_and_summary

def main():
    # 1. 정제 단계
    print("📥 [1단계] 발주서 정제 시작")
    clean_order_file("원본.xlsx", "정제.xlsx")

    # 2. 패킹리스트 생성
    print("📦 [2단계] 패킹리스트 생성")
    generate_packing_list("정제.xlsx", "패킹리스트.xlsx")

    # 3. 송장리스트 및 요약 생성
    print("🚚 [3단계] 송장리스트 및 요약 생성")
    generate_invoice_and_summary(["정제.xlsx"], "송장리스트.xlsx", "송장_요약.xlsx")

    print("✅ 모든 자동화 프로세스 완료!")

if __name__ == "__main__":
    main()
