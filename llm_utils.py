import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

ANALYST_PROMPT = """
You are an expert loan recovery analyst. Analyze the provided customer data, including a simple payment record string, to create a prioritized contact plan.
Base priority on high due amounts and the number of 'Late' payments in their record.
For each customer, provide a brief, one-sentence justification.
---
{customer_data}
---
Generate the priority plan now.
"""

def generate_priority_plan(customer_data):
    if not customer_data:
        return "You have no customers to analyze."
    
    formatted_data = ""
    for customer in customer_data:
        formatted_data += f"Account: {customer['account_number']}, Name: {customer['customer_name']}, Due: {customer['due_amount']}, Record: {customer['payment_record']}\n"

    try:
        full_prompt = ANALYST_PROMPT.format(customer_data=formatted_data)
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        print(f"LLM Analyst Error: {e}")
        return "Sorry, I was unable to generate a priority plan at this time."

SUMMARY_PROMPT = """
You are an expert financial analyst. Create a concise, one-paragraph summary of a customer's situation for a busy supervisor.
Include their name, financial situation, an analysis of their payment record string, and any agent notes.
---
{customer_details}
---
Generate the summary now.
"""

def generate_summary_for_supervisor(customer_details):
    if not customer_details:
        return "No customer details were provided to summarize."
    
    formatted_details = (
        f"Account: {customer_details['account_number']}, Name: {customer_details['customer_name']}\n"
        f"Total Loan: {customer_details['total_loan']}, Due Amount: {customer_details['due_amount']}\n"
        f"Agent's Notes: {customer_details.get('agent_notes', 'N/A')}\n"
        f"Payment Record: {customer_details.get('payment_record', 'N/A')}\n"
    )

    try:
        full_prompt = SUMMARY_PROMPT.format(customer_details=formatted_details)
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        print(f"LLM Summarizer Error: {e}")
        return "Sorry, I was unable to generate a summary for this case."