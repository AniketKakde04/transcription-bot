import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

def clean_and_prepare_data(df):
    """
    Cleans the dataset by handling missing values and encoding categorical features.
    """
    print("\n--- Starting Data Cleaning and Preparation ---")

    # 1. Handle Missing Values
    for col in df.select_dtypes(include=['float64', 'int64']).columns:
        df[col] = df[col].fillna(df[col].median())
    
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].fillna(df[col].mode()[0])

    print("Missing values handled.")

    # 2. Encode Categorical Variables
    le = LabelEncoder()
    # We will skip encoding the 'ID' column as it's just an identifier
    for col in df.select_dtypes(include=['object']).columns:
        if col != 'ID':
            df[col] = le.fit_transform(df[col])
    
    print("Categorical features encoded.")

    # 3. Split the Data for Training and Testing
    X = df.drop(['Default', 'LoanID'], axis=1) # Drop ID as well, it's not a feature
    y = df['Default']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print(f"\nData split into training and testing sets.")
    
    return X_train, X_test, y_train, y_test

def train_evaluate_and_save_model(X_train, X_test, y_train, y_test):
    """
    Trains an XGBoost model, evaluates its performance, and saves it to a file.
    """
    print("\n--- Starting Model Training ---")

    # 1. Initialize and Train the Model
    # XGBoost is a powerful and popular algorithm for this type of task.
    model = XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)
    model.fit(X_train, y_train)
    
    print("Model training completed.")

    # 2. Make Predictions on the Test Set
    print("\n--- Evaluating Model Performance ---")
    y_pred = model.predict(X_test)

    # 3. Evaluate the Model's Performance
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model Accuracy: {accuracy * 100:.2f}%")

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    # 4. Visualize the Confusion Matrix
    # This shows us how many predictions were correct vs. incorrect.
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Paid', 'Defaulted'], yticklabels=['Paid', 'Defaulted'])
    plt.title('Confusion Matrix')
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.show()

    # 5. Save the Trained Model
    model_filename = 'recovery_model.pkl'
    joblib.dump(model, model_filename)
    print(f"\nModel saved successfully as '{model_filename}'")
    
    return model


if __name__ == "__main__":
    dataset_path = 'loan_default.csv' 
    
    print("Loading the dataset...")
    df = pd.read_csv(dataset_path)
    print("Dataset loaded successfully.")

    # Clean and prepare the data
    X_train, X_test, y_train, y_test = clean_and_prepare_data(df)
    
    # Train, evaluate, and save the model
    trained_model = train_evaluate_and_save_model(X_train, X_test, y_train, y_test)