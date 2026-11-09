import streamlit as st
import mysql.connector
from dotenv import load_dotenv
import os
from google import genai

# Load environment variables
load_dotenv(override=True)

# Gemini client
gemini_key = os.getenv("GEMINI_API_KEY")

if gemini_key:
    client = genai.Client(api_key=gemini_key)
else:
    client = None

# Streamlit page
st.set_page_config(
    page_title="AI Financial Intelligence",
    page_icon="💰",
    layout="centered"
)

st.title("🤖 AI-Powered Financial Intelligence")
st.subheader("Your Personal Financial Data Analyst")

try:
    # Connect to MySQL
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

    cursor = conn.cursor()

    st.success("✅ Connected to Financial Database")

    # Total transactions
    cursor.execute("""
        SELECT COUNT(*)
        FROM Transactions
    """)
    total_transactions = cursor.fetchone()[0]

    st.metric(
        "Total Transactions",
        f"{total_transactions:,}"
    )

    # Question box
    question = st.text_input(
        "Ask your financial question:",
        placeholder="Example: What is the total revenue?"
    )

    if question:

        q = question.lower().strip()

        # ------------------------------------------------
        # TOTAL REVENUE
        # ------------------------------------------------
        if "total revenue" in q or q == "revenue":

            cursor.execute("""
                SELECT SUM(Amount_INR)
                FROM Transactions
                WHERE Transaction_Type = 'Revenue'
            """)

            result = cursor.fetchone()[0]

            st.success(
                f"💰 Total Revenue: ₹{result:,.2f}"
            )

        # ------------------------------------------------
        # TOTAL EXPENSES
        # ------------------------------------------------
        elif (
            "total expense" in q
            or "total expenses" in q
        ):

            cursor.execute("""
                SELECT SUM(Amount_INR)
                FROM Transactions
                WHERE Transaction_Type = 'Expense'
            """)

            result = cursor.fetchone()[0]

            st.success(
                f"💸 Total Expenses: ₹{result:,.2f}"
            )

        # ------------------------------------------------
        # NET PROFIT / LOSS
        # ------------------------------------------------
        elif (
            "net profit" in q
            or "net loss" in q
            or "profit or loss" in q
        ):

            cursor.execute("""
                SELECT
                    SUM(
                        CASE
                            WHEN Transaction_Type = 'Revenue'
                            THEN Amount_INR
                            ELSE 0
                        END
                    )
                    -
                    SUM(
                        CASE
                            WHEN Transaction_Type = 'Expense'
                            THEN Amount_INR
                            ELSE 0
                        END
                    )
                FROM Transactions
            """)

            result = cursor.fetchone()[0]

            if result >= 0:
                st.success(
                    f"📈 Net Profit: ₹{result:,.2f}"
                )
            else:
                st.error(
                    f"📉 Net Loss: ₹{abs(result):,.2f}"
                )

        # ------------------------------------------------
        # HIGHEST EXPENSE DEPARTMENT
        # ------------------------------------------------
        elif (
            "highest expense" in q
            or "highest expenses" in q
            or "most expense" in q
        ):

            cursor.execute("""
                SELECT
                    Department,
                    SUM(Amount_INR) AS Total_Expenses
                FROM Transactions
                WHERE Transaction_Type = 'Expense'
                GROUP BY Department
                ORDER BY Total_Expenses DESC
                LIMIT 1
            """)

            result = cursor.fetchone()

            st.success(
                f"🏢 Highest Expense Department: "
                f"{result[0]} — ₹{result[1]:,.2f}"
            )

        # ------------------------------------------------
        # LOWEST EXPENSE DEPARTMENT
        # ------------------------------------------------
        elif (
            "lowest expense" in q
            or "lowest expenses" in q
            or "least expense" in q
        ):

            cursor.execute("""
                SELECT
                    Department,
                    SUM(Amount_INR) AS Total_Expenses
                FROM Transactions
                WHERE Transaction_Type = 'Expense'
                GROUP BY Department
                ORDER BY Total_Expenses ASC
                LIMIT 1
            """)

            result = cursor.fetchone()

            st.success(
                f"🏢 Lowest Expense Department: "
                f"{result[0]} — ₹{result[1]:,.2f}"
            )

        # ------------------------------------------------
        # EXPENSES BY DEPARTMENT
        # ------------------------------------------------
        elif (
            "expense by department" in q
            or "expenses by department" in q
            or "department expenses" in q
        ):

            cursor.execute("""
                SELECT
                    Department,
                    SUM(Amount_INR) AS Total_Expenses
                FROM Transactions
                WHERE Transaction_Type = 'Expense'
                GROUP BY Department
                ORDER BY Total_Expenses DESC
            """)

            results = cursor.fetchall()

            st.subheader("🏢 Expenses by Department")

            for department, expense in results:

                st.write(
                    f"**{department}** — ₹{expense:,.2f}"
                )

        # ------------------------------------------------
        # FINANCIAL SUMMARY USING GEMINI
        # ------------------------------------------------
        elif (
            "summary" in q
            or "financial overview" in q
            or "financial performance" in q
            or "overall financial" in q
        ):

            # Get real database values

            cursor.execute("""
                SELECT SUM(Amount_INR)
                FROM Transactions
                WHERE Transaction_Type = 'Revenue'
            """)
            revenue = cursor.fetchone()[0]

            cursor.execute("""
                SELECT SUM(Amount_INR)
                FROM Transactions
                WHERE Transaction_Type = 'Expense'
            """)
            expenses = cursor.fetchone()[0]

            net_result = revenue - expenses

            cursor.execute("""
                SELECT
                    Department,
                    SUM(Amount_INR) AS Total_Expenses
                FROM Transactions
                WHERE Transaction_Type = 'Expense'
                GROUP BY Department
                ORDER BY Total_Expenses DESC
                LIMIT 1
            """)
            highest_department = cursor.fetchone()

            # Prepare real data for Gemini

            financial_data = f"""
Financial data from the MySQL database:

Total Transactions: {total_transactions}

Total Revenue: ₹{revenue:,.2f}

Total Expenses: ₹{expenses:,.2f}

Net Profit/Loss: ₹{net_result:,.2f}

Highest Expense Department:
{highest_department[0]} — ₹{highest_department[1]:,.2f}
"""

            if client:

                try:

                    response = client.models.generate_content(
                        model="gemini-3.5-flash-lite",
                        contents=f"""
You are an AI financial data analyst.

Create a short, professional financial summary using ONLY
the database information provided below.

Do not invent numbers.
Do not change the numbers.
Mention whether the company has a profit or loss.
Mention the highest expense department.

{financial_data}
"""
                    )

                    st.info(
                        "🤖 Gemini Financial Summary\n\n"
                        + response.text
                    )

                except Exception as ai_error:

                    st.error(
                        "❌ Gemini error"
                    )

                    st.error(
                        str(ai_error)
                    )

            else:

                st.warning(
                    "Gemini API key was not found."
                )

        # ------------------------------------------------
        # OTHER QUESTIONS → GEMINI
        # ------------------------------------------------
        else:

            if client:

                try:

                    response = client.models.generate_content(
                        model="gemini-3.5-flash-lite",
                        contents=f"""
You are an AI financial data analyst assistant.

The user asked:

{question}

The database contains financial transaction information.

Do not invent exact financial numbers.

For exact financial calculations, the chatbot currently
supports:

- Total revenue
- Total expenses
- Net profit/loss
- Highest expense department
- Lowest expense department
- Expenses by department
- Financial summary

Give a short and professional response.
"""
                    )

                    st.info(
                        "🤖 Gemini: "
                        + response.text
                    )

                except Exception as ai_error:

                    st.warning(
                        "⚠️ Gemini could not answer this question."
                    )

                    st.error(
                        str(ai_error)
                    )

            else:

                st.warning(
                    "I don't understand this question yet."
                )

    cursor.close()
    conn.close()

except Exception as e:

    st.error(
        "❌ Database connection failed"
    )

    st.error(
        str(e)
    )