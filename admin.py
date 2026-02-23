import streamlit as st
from supabase import create_client, ClientOptions
import logging
import os

# =====================================================
# CONFIGURATION
# =====================================================

st.set_page_config(layout="wide")
st.title("💼 Admin Monthly & Loan Management Panel")

logging.basicConfig(level=logging.INFO)

# =====================================================
# SUPABASE CONNECTION (SECURE)
# =====================================================


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Missing Supabase environment variables.")
    st.stop()


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def fetch_users():
    try:
        response = supabase.table("amount_2026") \
            .select("user_id,name") \
            .execute()

        if response.data is None:
            return []

        return response.data

    except Exception as e:
        logging.error(f"Fetch users error: {e}")
        return []


def fetch_loan(user_id):
    try:
        response = supabase.table("loan_details") \
            .select("*") \
            .eq("user_id", int(user_id)) \
            .execute()

        return response.data if response.data else None

    except Exception as e:
        logging.error(f"Fetch loan error: {e}")
        return None


# =====================================================
# FETCH USERS
# =====================================================

users = fetch_users()

if not users:
    st.error("No users found in amount_2026 table.")
    st.stop()

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

income_months = [
    "jan","feb","mar","apr","may","jun",
    "jul","aug","sep","oct","nov","dec"
]

selected_income_month = st.selectbox("Select Month", income_months)

try:
    month_response = supabase.table("amount_2026") \
        .select(selected_income_month) \
        .eq("user_id", user_id) \
        .execute()

    current_amount = (
        month_response.data[0].get(selected_income_month)
        if month_response.data else 0
    ) or 0

except Exception as e:
    st.error("Error fetching monthly data.")
    st.stop()

st.info(f"Existing Amount for {selected_income_month.upper()}: ₹ {current_amount}")

new_amount = st.number_input(
    "Enter / Update Monthly Amount",
    min_value=0,
    value=int(current_amount)
)

if st.button("Update Monthly Amount"):

    try:
        check = supabase.table("amount_2026") \
            .select("user_id") \
            .eq("user_id", user_id) \
            .execute()

        if check.data:
            supabase.table("amount_2026") \
                .update({selected_income_month: new_amount}) \
                .eq("user_id", user_id) \
                .execute()
        else:
            supabase.table("amount_2026") \
                .insert({
                    "user_id": user_id,
                    selected_income_month: new_amount
                }) \
                .execute()

        st.success("✅ Monthly Amount Saved Successfully!")
        logging.info(f"Monthly updated for user {user_id}")
        st.rerun()

    except Exception as e:
        logging.error(f"Monthly update failed: {e}")
        st.error("❌ Update Failed")


# =====================================================
# 🏦 LOAN SECTION
# =====================================================

st.subheader("🏦 Loan Management")

manage_loan = st.checkbox("Manage Loan")

if manage_loan:

    loan_data = fetch_loan(user_id)
    existing_loan_amount = 0

    if loan_data:
        existing_loan_amount = loan_data[0].get("loan_amount") or 0

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
                loan_payload = {
                    "loan_amount": None,
                    "intrest_amount": None,
                    "status_id": 2
                }
            else:
                loan_payload = {
                    "loan_amount": loan_amount,
                    "intrest_amount": interest_amount,
                    "status_id": 1
                }

            if row_exists:
                supabase.table("loan_details") \
                    .update(loan_payload) \
                    .eq("user_id", user_id) \
                    .execute()
            else:
                loan_payload["user_id"] = user_id
                supabase.table("loan_details") \
                    .insert(loan_payload) \
                    .execute()

            st.success("✅ Loan Saved Successfully!")
            logging.info(f"Loan updated for user {user_id}")
            st.rerun()

        except Exception as e:
            logging.error(f"Loan save error: {e}")
            st.error("❌ Loan Operation Failed")


# =====================================================
# 📊 DISPLAY CURRENT LOAN
# =====================================================

st.subheader("🏦 Admin Loan Monthly & Interest Update")

loan_info = fetch_loan(user_id)

if not loan_info:
    st.warning("No Loan Record Found For This User")
    st.stop()

loan_data = loan_info[0]

loan_amount = loan_data.get("loan_amount") or 0
interest_amount_db = loan_data.get("intrest_amount") or 0

st.write(f"💰 Loan Amount: ₹ {loan_amount}")

interest_amount = st.number_input(
    "Enter / Update Interest Amount",
    min_value=0.0,
    value=float(interest_amount_db)
)

if st.button("Update Interest Amount"):

    try:
        supabase.table("loan_details") \
            .update({"intrest_amount": interest_amount}) \
            .eq("user_id", user_id) \
            .execute()

        st.success("✅ Interest Amount Updated Successfully!")
        st.rerun()

    except Exception as e:
        logging.error(f"Interest update error: {e}")
        st.error("❌ Failed to Update Interest")


st.divider()

# =====================================================
# EMI SECTION
# =====================================================

emi_months = [
    "in_jan","in_feb","in_mar","in_apr","in_may","in_jun",
    "in_jul","in_aug","in_sep","in_oct","in_nov","in_dec"
]

selected_emi_month = st.selectbox("Select Month to Update EMI", emi_months)

current_month_value = loan_data.get(selected_emi_month) or 0

emi_amount = st.number_input(
    f"Enter EMI Amount for {selected_emi_month.upper()}",
    min_value=0,
    value=int(current_month_value)
)

if st.button("Update Monthly EMI"):

    try:
        supabase.table("loan_details") \
            .update({selected_emi_month: emi_amount}) \
            .eq("user_id", user_id) \
            .execute()

        st.success(f"✅ {selected_emi_month.upper()} Updated Successfully!")
        st.rerun()

    except Exception as e:
        logging.error(f"EMI update error: {e}")
        st.error("❌ EMI Update Failed")


# =====================================================
# CURRENT LOAN SUMMARY
# =====================================================

st.subheader("📊 Current Loan Details")

try:
    loan_summary = supabase.table("loan_details") \
        .select("loan_amount,intrest_amount,loan_total,status_id,"
                "in_jan,in_feb,in_mar,in_apr,in_may,in_jun,"
                "in_jul,in_aug,in_sep,in_oct,in_nov,in_dec") \
        .eq("user_id", user_id) \
        .execute()

    if loan_summary.data:

        data = loan_summary.data[0]

        STATUS_MAP = {1: "Ongoing", 2: "Closed"}
        status_text = STATUS_MAP.get(data.get("status_id"), "Unknown")

        paid_months = [
            data.get("in_jan") or 0,
            data.get("in_feb") or 0,
            data.get("in_mar") or 0,
            data.get("in_apr") or 0,
            data.get("in_may") or 0,
            data.get("in_jun") or 0,
            data.get("in_jul") or 0,
            data.get("in_aug") or 0,
            data.get("in_sep") or 0,
            data.get("in_oct") or 0,
            data.get("in_nov") or 0,
            data.get("in_dec") or 0
        ]

        total_paid = sum(paid_months)

        st.write(f"💰 Loan Amount: ₹ {data.get('loan_amount') or 0}")
        st.write(f"📈 Interest Amount: ₹ {data.get('intrest_amount') or 0}")
        st.write(f"🧮 Loan Total: ₹ {data.get('loan_total') or 0}")
        st.write(f"📌 Status: {status_text}")
        st.write(f"✅ Total EMI Paid: ₹ {total_paid}")

    else:
        st.info("No Loan Record Found")

except Exception as e:
    logging.error(f"Loan summary error: {e}")
    st.error("Error fetching loan details.")

