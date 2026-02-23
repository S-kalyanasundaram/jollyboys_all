import streamlit as st
from supabase import create_client
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# -------------------------
# SUPABASE CONFIG
# -------------------------
SUPABASE_URL = "https://ckbvfhjypiqgeprxqcqv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNrYnZmaGp5cGlxZ2VwcnhxY3F2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk1MDA1NDIsImV4cCI6MjA4NTA3NjU0Mn0.CzzxqtR_XpKjwiT8p1gqAE_Z6RLckwzJZhWwB_bwEgg"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------
# EMAIL CONFIG
# -------------------------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "yourgmail@gmail.com"
SENDER_PASSWORD = "your_app_password"

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title="Jolly Boys Finance",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------
# PROFESSIONAL UI STYLE
# -------------------------
st.markdown("""
<style>
.block-container {
    padding-top: 1rem;
}

.card {
    padding: 20px;
    border-radius: 14px;
    background: white;
    text-align: center;
    box-shadow: 0 3px 10px rgba(0,0,0,0.08);
    margin-bottom: 12px;
    transition: 0.2s;
}
.card:hover {
    transform: translateY(-3px);
}

.green {border-top: 6px solid #2e7d32;}
.blue {border-top: 6px solid #1565c0;}
.orange {border-top: 6px solid #ef6c00;}
.red {border-top: 6px solid #c62828; background:#fff1f1;}

.title {
    font-size: 14px;
    color: #666;
}
.amount {
    font-size: 26px;
    font-weight: 700;
    color: #111;
}

.section-title {
    font-size: 22px;
    font-weight: 600;
    margin-top: 10px;
}

@media (max-width:768px){
    .amount {font-size:20px;}
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# CARD FUNCTION
# -------------------------
def card(title, value, color="green"):
    st.markdown(f"""
    <div class="card {color}">
        <div class="title">{title}</div>
        <div class="amount">₹ {value}</div>
    </div>
    """, unsafe_allow_html=True)

# -------------------------
# EMAIL FUNCTION
# -------------------------
def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()

    except Exception:
        st.warning("Email sending failed")

# -------------------------
# TITLE
# -------------------------
st.title("💳 Jolly Boys Finance Dashboard")

# -------------------------
# LOGIN
# -------------------------
user_id = st.number_input("Enter User ID", step=1)

if st.button("Login"):

    res = supabase.table("amount_2026")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()

    if not res.data:
        st.error("User not found")
        st.stop()

    user = res.data[0]
    st.success(f"Welcome {user.get('name','Member')} 👋")

    # =====================
    # USER DASHBOARD
    # =====================
    st.markdown('<div class="section-title">👤 User Summary</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)

    with c1:
        card("2024 Balance", user.get("balance_2024", 0))
    with c2:
        card("2025 Balance", user.get("balance_2025", 0), "blue")
    with c3:
        card("2026 Balance", user.get("balance_2026", 0), "orange")
    with c4:
        card("Fine Amount", user.get("fine_2026", 0), "blue")

    # Loan pending card
    loan_amt = user.get("loan_amount", 0)
    if loan_amt and loan_amt > 0:
        card("Loan Pending", loan_amt, "red")

    # =====================
    # LOAN DETAILS
    # =====================
    loan_res = supabase.table("loan_details")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()

    if loan_res.data:
        loan = loan_res.data[0]

        total = loan.get("loan_total", 0)
        paid = loan.get("amount_paid", 0)
        remaining = total - paid

        # SAFE STATUS FETCH
        status_id = loan.get("status_id")
        if status_id == 1:
            status = "Ongoing"
        elif status_id == 2:
            status = "Closed"
        else:
            status = "Unknown"

        if status_id:
            status_res = supabase.table("loan_status_master")\
                .select("status_name")\
                .eq("status_id", status_id)\
                .execute()

            if status_res.data:
                status = status_res.data[0]["status_name"]

        st.markdown('<div class="section-title">💰 Loan Details</div>', unsafe_allow_html=True)

        l1, l2 = st.columns(2)
        l3, l4 = st.columns(2)

        with l1:
            card("Loan Total", total, "orange")
        with l2:
            card("Amount Paid", paid)
        with l3:
            card("Remaining Balance", remaining, "red")
        with l4:
            card("Status", status, "blue")

        # EMAIL REMINDER
        if remaining > 0:
            email = user.get("email")
            if email:
                send_email(
                    email,
                    "Loan Payment Reminder",
                    f"""
Hello,

Your loan payment is pending.

Outstanding Amount: ₹{remaining}

Please pay soon.

Thank you,
Jolly Boys Finance
"""
                )

    # =====================
    # GROUP DASHBOARD
    # =====================
    st.divider()
    st.markdown('<div class="section-title">👥 Group Summary</div>', unsafe_allow_html=True)

    group = supabase.table("amount_2026").select("*").execute()
    df = pd.DataFrame(group.data)

    total_2024 = df["balance_2024"].sum()
    total_2025 = df["balance_2025"].sum()
    total_2026 = df["balance_2026"].sum()
    total_fine = df["fine_2026"].fillna(0).sum()
    total_loan = df["loan_amount"].fillna(0).sum()

    total_collected = total_2024 + total_2025 + total_2026 + total_fine
    available = total_collected - total_loan

    g1, g2 = st.columns(2)
    with g1:
        card("Available Fund", available)
    with g2:
        card("Loan Given", total_loan, "red")

    st.markdown("### 📅 Year Totals")

    y1, y2, y3= st.columns(3)
    with y1:
        card("2024 Total", total_2024)
    with y2:
        card("2025 Total", total_2025, "blue")
    with y3:
        card("2026 Total", total_2026, "orange")
