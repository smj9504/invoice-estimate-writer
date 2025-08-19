import pandas as pd
import json
import math
from pathlib import Path

def excel_to_estimate_json(excel_path: str, output_dir: str = None, filename_by_address: bool = True) -> str:
    df_info = pd.read_excel(excel_path, sheet_name="Estimate_Info", engine="openpyxl")
    df_items = pd.read_excel(excel_path, sheet_name="Service_Items", engine="openpyxl")

    info = pd.Series(df_info.Value.values, index=df_info.Field).to_dict()

    company_fields = ["name", "address", "city", "state", "zip", "phone", "email", "logo"]
    client_fields = ["name", "address", "city", "state", "zip", "phone", "email"]

    def safe_string(val):
        """안전한 문자열 변환 함수"""
        if pd.isna(val) or val is None:
            return ""
        return str(val).strip()

    def safe_float(val):
        try:
            if pd.isna(val):
                return 0.0
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    # 회사 정보와 고객 정보에 safe_string 적용
    company = {field: safe_string(info.get(f"company.{field}", "")) for field in company_fields}
    client = {field: safe_string(info.get(f"client.{field}", "")) for field in client_fields}

    estimate_data = {
        "estimate_number": safe_string(info.get("estimate_number", "")),
        "estimate_date": safe_string(info.get("estimate_date", "")),
        "company": company,
        "client": client,
        "top_note": safe_string(info.get("top_note", "")),
        "bottom_note": safe_string(info.get("bottom_note", "")),
        "disclaimer": safe_string(info.get("disclaimer", "")),
        "op_percent": safe_float(info.get("op_percent", 0)),
        "discount": safe_float(info.get("discount", 0))
    }

    tax_rate = safe_float(info.get("tax_rate", 0))

    sections = []
    for section_title in df_items["section_title"].dropna().unique():
        section_df = df_items[df_items["section_title"] == section_title]
        show_subtotal = bool(section_df["show_subtotal"].iloc[0]) if "show_subtotal" in section_df else True

        items = []
        for _, row in section_df.iterrows():
            qty = safe_float(row.get("qty", 0))
            price = safe_float(row.get("price", 0))
            items.append({
                "name": safe_string(row.get("item_name", "")),
                "qty": qty,
                "unit": safe_string(row.get("unit", "")),
                "price": price,
                "dec": safe_string(row.get("description", ""))
            })

        subtotal = round(sum(item["qty"] * item["price"] for item in items), 2)
        sections.append({
            "title": safe_string(section_title),
            "showSubtotal": show_subtotal,
            "items": items,
            "subtotal": subtotal
        })

    estimate_data["serviceSections"] = sections

    valid_subtotals = [s["subtotal"] for s in sections if isinstance(s["subtotal"], (int,
        float)) and not math.isnan(s["subtotal"])]
    subtotal_sum = round(sum(valid_subtotals), 2)
    op_amount = round(subtotal_sum * (estimate_data["op_percent"] / 100), 2)

    taxable_amount = subtotal_sum + op_amount - estimate_data["discount"]
    sales_tax = round(taxable_amount * (tax_rate / 100), 2) if tax_rate > 0 else 0

    total = round(taxable_amount + sales_tax, 2)

    estimate_data["serviceSections"] = sections
    estimate_data["subtotal"] = subtotal_sum
    estimate_data["op_amount"] = op_amount
    estimate_data["sales_tax"] = sales_tax
    estimate_data["tax_rate"] = tax_rate
    estimate_data["total"] = total

    # 주소를 안전하게 처리
    address_value = client.get("address", "estimate")
    if address_value and address_value != "":
        address_part = address_value.replace(" ", "_")
    else:
        address_part = "estimate"

    # JSON 저장 디렉토리 설정
    if output_dir is None:
        # 기본 저장 경로를 data/xlsx_json으로 설정
        project_root = Path(__file__).parent.parent
        output_dir = project_root / "data" / "xlsx_json"
        output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{address_part}.json" if filename_by_address else "estimate.json"
    output_path = Path(output_dir) / filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(estimate_data, f, indent=2, ensure_ascii=False)

    return str(output_path)

# 예시 실행
if __name__ == "__main__":
    excel_file = "estimate_input_template.xlsx"
    output_json = excel_to_estimate_json(excel_file)  # output_dir 인자 제거하여 기본 경로 사용
    print(f"JSON saved to: {output_json}")
