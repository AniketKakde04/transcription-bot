import joblib
import pandas as pd
from sklearn.preprocessing import LabelEncoder

# Load the trained model when the application starts
try:
    model = joblib.load('recovery_model.pkl')
    print("Predictive model loaded successfully.")
except FileNotFoundError:
    print("Warning: recovery_model.pkl not found. Predictive features will be disabled.")
    model = None

def make_prediction(customer_data):
    """
    Uses the loaded model to predict the likelihood of loan recovery.
    """
    if not model:
        return "Predictive model is not available."

    try:
        # 1. Define the exact column order the model expects
        expected_columns = [
            'Age', 'Income', 'LoanAmount', 'CreditScore', 'MonthsEmployed', 
            'NumCreditLines', 'InterestRate', 'LoanTerm', 'DTIRatio', 'Education', 
            'EmploymentType', 'MaritalStatus', 'HasMortgage', 'HasDependents', 
            'LoanPurpose', 'HasCoSigner'
        ]
        
        # 2. Convert the single customer's data into a DataFrame with the correct column order
        df = pd.DataFrame([customer_data], columns=expected_columns)

        # 3. Preprocess the data in the exact same way as in training
        # Note: In a production system, you would save and load the trained LabelEncoders
        # to ensure consistent mapping between text and numbers.
        for col in df.select_dtypes(include=['object']).columns:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col])
        
        # 4. Make the prediction
        prediction = model.predict(df)
        probability = model.predict_proba(df)

        # 5. Format the output
        if prediction[0] == 0:
            return f"Prediction: High chance of recovery (Probability: {probability[0][0]*100:.2f}%)."
        else:
            return f"Prediction: High risk of default (Probability: {probability[0][1]*100:.2f}%)."

    except Exception as e:
        print(f"Prediction Error: {e}")
        return "Could not generate a prediction for this customer."

def generate_model_based_plan(all_customer_data):
    """
    Uses the loaded model to predict default risk for a list of customers and
    sorts them to create a priority plan.
    """
    if not model:
        return "Predictive model is not available."
    if not all_customer_data:
        return "You have no customers to create a plan for."

    try:
        expected_columns = [
            'Age', 'Income', 'LoanAmount', 'CreditScore', 'MonthsEmployed', 
            'NumCreditLines', 'InterestRate', 'LoanTerm', 'DTIRatio', 'Education', 
            'EmploymentType', 'MaritalStatus', 'HasMortgage', 'HasDependents', 
            'LoanPurpose', 'HasCoSigner'
        ]
        
        df = pd.DataFrame(all_customer_data)
        df_processed = df.copy()
        for col in df_processed.select_dtypes(include=['object']).columns:
            le = LabelEncoder()
            df_processed[col] = le.fit_transform(df_processed[col])
        
        df_processed = df_processed[expected_columns]
        probabilities = model.predict_proba(df_processed)[:, 1]
        df['risk_score'] = probabilities
        df_sorted = df.sort_values(by='risk_score', ascending=False)

        # --- THIS IS THE KEY FIX ---
        # We now create a much simpler and more actionable reply.
        reply_msg = "🤖 Here is your AI-generated priority plan:\n"
        for index, row in df_sorted.iterrows():
            # Assign a clear priority level based on the risk score
            if row['risk_score'] > 0.5:
                priority = "High Priority"
            elif row['risk_score'] > 0.2:
                priority = "Medium Priority"
            else:
                priority = "Low Priority"
            
            reply_msg += f"\n--------------------\n"
            reply_msg += f"👤 *{row['customer_name']} ({row['account_number']})*\n"
            reply_msg += f"   - *Priority:* {priority}"
        
        return reply_msg

    except Exception as e:
        print(f"Priority Plan Error: {e}")
        return "Could not generate a priority plan for your customers."