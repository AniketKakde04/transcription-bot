import os
import google.generativeai as genai

# Configure the generative AI model
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

ANALYST_PROMPT = """
You are an expert loan recovery analyst. Your task is to analyze a list of customer data and create a prioritized contact plan for a recovery agent.

Analyze the provided data based on the following criteria to determine priority:
1.  **High Priority:** Customers with a high due amount and a history of late payments.
2.  **Medium Priority:** Customers with a high due amount but a good payment history, or customers with a lower due amount but multiple late payments.
3.  **Low Priority:** Customers with a low due amount and a good payment history.

For each customer in your plan, you must provide a brief, one-sentence justification for why they are at that priority level.

The output should be a clear, formatted list. Here is the customer data:
---
{customer_data}
---
Generate the priority plan now.
"""

def generate_priority_plan(customer_data):
    """
    Uses the Gemini LLM to analyze customer data and generate a priority plan.
    """
    if not customer_data:
        return "You have no customers to analyze."

    # Format the customer data into a readable string for the LLM
    formatted_data = ""
    for customer in customer_data:
        formatted_data += f"Account: {customer['account_number']}, Name: {customer['customer_name']}, Due: {customer['due_amount']}, Record: {customer['payment_record']}\n"

    try:
        # Create the full prompt for the analyst
        full_prompt = ANALYST_PROMPT.format(customer_data=formatted_data)
        
        # Send the prompt to the model
        response = model.generate_content(full_prompt)
        
        return response.text

    except Exception as e:
        print(f"LLM Analyst Error: {e}")
        return "Sorry, I was unable to generate a priority plan at this time."


SUMMARY_PROMPT = """
You are an expert financial analyst providing a briefing for a busy loan recovery supervisor.
Your task is to create a concise, one-paragraph summary of a customer's situation based on the provided data.

The summary must include:
1.  The customer's name and account number.
2.  A brief overview of their financial situation (total loan, due amount).
3.  An analysis of their payment history (e.g., "good record with one recent late payment").
4.  The key reason provided by the recovery agent for the current issue.

Here is the data for the account:
---
{customer_details}
---
Generate the summary now.
"""

def generate_summary_for_supervisor(customer_details):
    """
    Uses the Gemini LLM to generate a concise summary of a customer's case for a supervisor.
    """
    if not customer_details:
        return "No customer details were provided to summarize."

    # Format the customer data into a readable string for the LLM
    formatted_details = (
        f"Account: {customer_details['account_number']}, Name: {customer_details['customer_name']}\n"
        f"Total Loan: {customer_details['total_loan']}, Due Amount: {customer_details['due_amount']}\n"
        f"Payment Record: {customer_details['payment_record']}\n"
        f"Agent's Notes: {customer_details['agent_notes']}"
    )

    try:
        # Create the full prompt for the summarizer
        full_prompt = SUMMARY_PROMPT.format(customer_details=formatted_details)
        
        # Send the prompt to the model
        response = model.generate_content(full_prompt)
        
        return response.text

    except Exception as e:
        print(f"LLM Summarizer Error: {e}")
        return "Sorry, I was unable to generate a summary for this case."