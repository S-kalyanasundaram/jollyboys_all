import streamlit as st
from supabase import create_client, ClientOptions

# -------------------------------------------------
# SUPABASE CONNECTION
# -------------------------------------------------
SUPABASE_URL = "https://ckbvfhjypiqgeprxqcqv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNrYnZmaGp5cGlxZ2VwcnhxY3F2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk1MDA1NDIsImV4cCI6MjA4NTA3NjU0Mn0.CzzxqtR_XpKjwiT8p1gqAE_Z6RLckwzJZhWwB_bwEgg"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(layout="wide")
st.title("💼 Admin Monthly & Loan Management Panel")

# =====================================================
# FETCH USERS
# =====================================================
users_response = supabase.table("amount_2026") \
    .select("user_id,name") \
    .execute()

if not users_response.data:
    st.error("No users found in amount_2026 table.")
    st.stop()

users = users_response.data

# Convert user_id to int (VERY IMPORTANT)
user_dict = {
    f"{u['name']} ({u['user_id']})": int(u["user_id"])
    for u in users
}

selected_user = st.selectbox("Select User", list(user_dict.keys()))
user_id = user_dict[selected_user]

# =====================================================
# 📅 MONTHLY SECTION
# =====================================================
st.subheader("📅 Monthly Amount Entry")

months = [
    "jan","feb","mar","apr","may","jun",
    "jul","aug","sep","oct","nov","dec"
]

selected_month = st.selectbox("Select Month", months)

# Fetch current month value
month_response = supabase.table("amount_2026") \
    .select(selected_month) \
    .eq("user_id", user_id) \
    .execute()

if month_response.data:
    current_amount = month_response.data[0].get(selected_month) or 0
else:
    current_amount = 0

st.info(f"Existing Amount for {selected_month.upper()}: ₹ {current_amount}")

new_amount = st.number_input(
    "Enter / Update Monthly Amount",
    min_value=0,
    value=int(current_amount)
)

# ------------------ UPDATE LOGIC ------------------
if st.button("Update Monthly Amount"):

    try:
        # Check row existence
        check = supabase.table("amount_2026") \
            .select("user_id") \
            .eq("user_id", user_id) \
            .execute()

        if check.data:
            # UPDATE
            response = supabase.table("amount_2026") \
                .update({selected_month: new_amount}) \
                .eq("user_id", user_id) \
                .execute()
        else:
            # INSERT
            response = supabase.table("amount_2026") \
                .insert({
                    "user_id": user_id,
                    selected_month: new_amount
                }) \
                .execute()

        st.success("✅ Monthly Amount Saved Successfully!")
        st.rerun()

    except Exception as e:
        st.error(f"❌ Update Failed: {e}")


# =====================================================
# 🏦 LOAN SECTION
# =====================================================
st.subheader("🏦 Loan Management")

manage_loan = st.checkbox("Manage Loan")

if manage_loan:

    loan_response = supabase.table("loan_details") \
        .select("loan_amount,intrest_amount,status_id") \
        .eq("user_id", user_id) \
        .execute()

    existing_loan = loan_response.data
    existing_loan_amount = 0

    if existing_loan:
        existing_loan_amount = existing_loan[0].get("loan_amount") or 0

    loan_amount = st.number_input(
        "Enter Loan Amount",
        min_value=0,
        value=int(existing_loan_amount)
    )

    interest_rate = st.number_input(
        "Interest Percentage (%)",
        min_value=0.0,
        value=1.0
    )

    interest_amount = loan_amount * (interest_rate / 100)

    st.info(f"Calculated Interest Amount: ₹ {interest_amount}")

    status_option = st.selectbox(
        "Loan Status",
        ["Ongoing", "Closed"]
    )

    if st.button("Save Loan"):

        try:
            loan_check = supabase.table("loan_details") \
                .select("user_id") \
                .eq("user_id", user_id) \
                .execute()

            row_exists = True if loan_check.data else False

            if status_option == "Closed":
                loan_data = {
                    "loan_amount": None,
                    "intrest_amount": None,
                    "status_id": 2
                }
            else:
                loan_data = {
                    "loan_amount": loan_amount,
                    "intrest_amount": interest_amount,
                    "status_id": 1
                }

            if row_exists:
                supabase.table("loan_details") \
                    .update(loan_data) \
                    .eq("user_id", user_id) \
                    .execute()
            else:
                loan_data["user_id"] = user_id
                supabase.table("loan_details") \
                    .insert(loan_data) \
                    .execute()

            st.success("✅ Loan Saved Successfully!")
            st.rerun()

        except Exception as e:
            st.error(f"❌ Loan Operation Failed: {e}")


# =====================================================
# 📊 DISPLAY CURRENT LOAN
# =====================================================

st.subheader("🏦 Admin Loan Monthly & Interest Update")

# Fetch existing loan row
loan_info = supabase.table("loan_details") \
    .select("*") \
    .eq("user_id", int(user_id)) \
    .execute()

if not loan_info.data:
    st.warning("No Loan Record Found For This User")
    st.stop()

loan_data = loan_info.data[0]

# -----------------------------
# Default Values From Database
# -----------------------------
loan_amount = loan_data.get("loan_amount") or 0
interest_amount_db = loan_data.get("intrest_amount") or 0

st.write(f"💰 Loan Amount: ₹ {loan_amount}")

# -----------------------------
# Interest Amount Update
# -----------------------------
interest_amount = st.number_input(
    "Enter / Update Interest Amount",
    min_value=0.0,
    value=float(interest_amount_db)
)

if st.button("Update Interest Amount"):

    try:
        supabase.table("loan_details") \
            .update({"intrest_amount": interest_amount}) \
            .eq("user_id", int(user_id)) \
            .execute()

        st.success("✅ Interest Amount Updated Successfully!")
        st.rerun()

    except Exception as e:
        st.error(f"❌ Failed to Update Interest: {e}")


st.divider()

# -----------------------------
# Monthly EMI Entry Section
# -----------------------------

months = [
    "in_jan","in_feb","in_mar","in_apr","in_may","in_jun",
    "in_jul","in_aug","in_sep","in_oct","in_nov","in_dec"
]

selected_month = st.selectbox("Select Month to Update EMI", months)

current_month_value = loan_data.get(selected_month) or 0

emi_amount = st.number_input(
    f"Enter EMI Amount for {selected_month.upper()}",
    min_value=0,
    value=int(current_month_value)
)

if st.button("Update Monthly EMI"):

    try:
        supabase.table("loan_details") \
            .update({selected_month: emi_amount}) \
            .eq("user_id", int(user_id)) \
            .execute()

        st.success(f"✅ {selected_month.upper()} Updated Successfully!")
        st.rerun()

    except Exception as e:
        st.error(f"❌ EMI Update Failed: {e}")


st.subheader("📊 Current Loan Details")

try:
    loan_info = supabase.table("loan_details") \
        .select("loan_amount,intrest_amount,loan_total,status_id") \
        .eq("user_id", int(user_id)) \
        .execute()

    if loan_info.data and len(loan_info.data) > 0:

        loan_data = loan_info.data[0]

        loan_amount = loan_data.get("loan_amount") or 0
        interest_amount = loan_data.get("intrest_amount") or 0
        loan_total = loan_data.get("loan_total") or 0
        status_id = loan_data.get("status_id", 0)

        if status_id == 1:
            status_text = "Ongoing"
        elif status_id == 2:
            status_text = "Closed"
        else:
            status_text = "Unknown"
            
        paid_months = [
            loan_data.get("in_jan") or 0,
            loan_data.get("in_feb") or 0,
            loan_data.get("in_mar") or 0,
            loan_data.get("in_apr") or 0,
            loan_data.get("in_may") or 0,
            loan_data.get("in_jun") or 0,
            loan_data.get("in_jul") or 0,
            loan_data.get("in_aug") or 0,
            loan_data.get("in_sep") or 0,
            loan_data.get("in_oct") or 0,
            loan_data.get("in_nov") or 0,
            loan_data.get("in_dec") or 0
            ]
            
        
    
        total_paid = sum(paid_months)
        
        
        st.write(f"💰 Loan Amount: ₹ {loan_amount}")
        st.write(f"📈 Interest Amount: ₹ {interest_amount}")
        st.write(f"🧮 Loan Total: ₹ {loan_total}")
        st.write(f"📌 Status: {status_text}")

    else:
        st.info("No Loan Record Found")

except Exception as e:
    st.error(f"Error fetching loan details: {e}")



