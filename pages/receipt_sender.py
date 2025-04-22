import streamlit as st
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import os
from dotenv import load_dotenv
from utils.company_service import get_all_companies
from datetime import date

# .env 설정
load_dotenv()
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# 상품 항목 입력용
def item_form(index, item_data):
    with st.container():
        st.markdown(f"### 🛒 상품 {index + 1}")
        item_data["name"] = st.text_input("상품명", value=item_data.get("name", ""), key=f"name_{index}")
        item_data["description"] = st.text_input("설명", value=item_data.get("description", ""), key=f"desc_{index}")
        item_data["reg_price"] = st.number_input("정가", min_value=0.0, step=0.01,
                                                value=item_data.get("reg_price", 0.0), key=f"reg_{index}")
        item_data["final_price"] = st.number_input("최종가", min_value=0.0, step=0.01,
                                                 value=item_data.get("final_price", 0.0), key=f"final_{index}")
        item_data["discount"] = round(item_data["reg_price"] - item_data["final_price"], 2)
    return item_data

# HTML 생성
def generate_html(data, items, company):
    total = sum([item['final_price'] for item in items])
    item_html = ""
    for item in items:
        item_html += f"""
        <tr>
            <td width="55%" style="text-align:left;"><strong>{item['name']}</strong><br>{item['description']}</td>
            <td width="15%" style="text-align:right;">${item['reg_price']:.2f}</td>
            <td width="15%" style="text-align:right;">{"-" if item['discount'] == 0 else f"${item['discount']:.2f}"}</td>
            <td width="15%" style="text-align:right;">${item['final_price']:.2f}</td>
        </tr>
        """
    return f"""
    <html>
    <body style="font-family: Arial;">
        <p><strong>MJ Estimate</strong></p>
        <h2 style="color:#4CAF50;">Your eReceipt</h2>
        <hr>
        <p><strong>Order date:</strong> {data['order_date']}</p>
        <p><strong>Customer:</strong> {data['customer_name']} ({data['email']})</p>
        <table style="width:100%; border-collapse:collapse;" border="1" cellpadding="10">
            <tr style="background-color: #f2f2f2;">
                <th width="50%">Item</th>
                <th width="15%">Reg. Price</th>
                <th width="15%">Discount</th>
                <th width="20%">Final Price</th>
            </tr>
            {item_html}
        </table>
        <p style="text-align:right; font-size:1.2em;"><strong>Total Paid: ${total:.2f}</strong></p>
    </body>
    </html>
    """

# 이메일 발송
def send_html_email(to_email, subject, html_body):
    msg = MIMEMultipart("alternative")
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

# 세션 상태 초기화
if "items" not in st.session_state:
    st.session_state["items"] = [{}]

# Streamlit UI
st.title("📩 eReceipt 생성 및 이메일 발송")

# 상품 추가 버튼 처리 (폼 외부)
if st.button("➕ 상품 추가"):
    st.session_state["items"].append({})
    st.rerun()

# 회사 목록 표시
companies = get_all_companies()
if not companies:
    st.warning("회사 정보를 불러올 수 없습니다.")
    st.stop()

# 회사 선택
company_options = {f"{c['name']} ({c['email']})": c for c in companies}
selected_company_label = st.selectbox("보내는 회사 선택", list(company_options.keys()))
selected_company = company_options[selected_company_label]

# 폼 시작
with st.form("receipt_form"):
    # 선택된 회사 정보로 자동 설정 (수신자로 사용)
    recipient_name = selected_company['name']
    recipient_email = selected_company.get('email', '')
    st.info(f"수신자: {recipient_name} ({recipient_email})")
    
    order_date = st.date_input("주문 날짜", value=date.today())

    # 상품 목록 표시
    updated_items = []
    for idx, item in enumerate(st.session_state["items"]):
        updated = item_form(idx, item)
        updated_items.append(updated)

    # 발송 버튼
    send_button = st.form_submit_button("📨 이메일 발송")

    if send_button:
        if not recipient_email:
            st.error("선택된 회사의 이메일 정보가 없습니다.")
        elif not all([item.get("name") for item in updated_items]):
            st.error("모든 상품에 이름을 입력해주세요.")
        else:
            data = {
                "customer_name": recipient_name,  # 회사 이름을 고객 이름으로 사용
                "email": recipient_email,         # 회사 이메일을, 수신자로 사용
                "order_date": order_date.strftime("%Y-%m-%d")
            }
            html = generate_html(data, updated_items, selected_company)
            try:
                send_html_email(recipient_email, f"[eReceipt] 주문 내역 - {order_date}", html)
                st.success(f"✅ 영수증 이메일이 {recipient_name}({recipient_email})로 발송되었습니다.")
            except Exception as e:
                st.error(f"이메일 발송 중 오류가 발생했습니다: {str(e)}")