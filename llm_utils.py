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



AI_DECISION_PROMPT = """
You are a junior loan recovery officer. Your task is to analyze a customer's case and recommend a standard, pre-approved action.
The case data includes the customer's profile, their payment history, and the recovery agent's recent notes.

Analyze the data and choose ONE of the following standard actions:
1.  "Offer a 7-day payment extension."
2.  "Schedule a follow-up call in 3 days."
3.  "Verify customer contact details."

Provide only the chosen action as your response, with no additional explanation.
---
{case_data}
---
Recommend the standard action now.
"""

def generate_ai_decision(case_data):
    """
    Uses the Gemini LLM to make a standard decision for a low-risk case.
    """
    if not case_data:
        return "Insufficient data to make a decision."

    # Format the data for the prompt
    formatted_data = (
        f"Customer: {case_data['customer_name']} ({case_data['account_number']})\n"
        f"Type: {case_data['customer_type']}, Due Amount: {case_data['due_amount']}\n"
        f"Payment Record: {case_data['payment_record']}\n"
        f"Agent's Notes: {case_data['agent_notes']}"
    )

    try:
        full_prompt = AI_DECISION_PROMPT.format(case_data=formatted_data)
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        print(f"LLM Decision Error: {e}")
        return "Could not determine an AI decision."