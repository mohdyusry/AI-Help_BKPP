
'''import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import os
import django

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Trial.settings')
django.setup()

# Now you can import your models
from app1.models import Ticket


def load_data():
    """
    Load data from the Django model.
    """
    tickets = Ticket.objects.filter(act_stat='S').values('hw_type', 'apps_sw', 'report_type', 'report_desc',
                                                           'act_taken')
    df = pd.DataFrame.from_records(tickets)
    print(df.head())  # Print the first few rows for debugging
    return df


def preprocess_data(df):
    """
    Preprocess the data for model training.
    """
    required_columns = ['hw_type', 'apps_sw', 'report_type', 'report_desc']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing columns: {', '.join(missing_columns)}")

    # Preprocess data
    for col in required_columns:
        df[col] = df[col].str.lower().fillna('')
    df['combined'] = df['hw_type'] + ' ' + df['apps_sw'] + ' ' + df['report_type'] + ' ' + df['report_desc']
    return df


def train_model(df):
    """
    Train a machine learning model using the preprocessed data.
    """
    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(df['combined'], df['act_taken'], test_size=0.2, random_state=42)

    # Create and train a model pipeline
    model = make_pipeline(TfidfVectorizer(), RandomForestClassifier())
    model.fit(X_train, y_train)

    # Evaluate the model
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred))

    return model


def recommend_action(hw_type, apps_sw, report_type, report_desc):
    """
    Recommend an action based on user input.
    """
    # Ensure all fields are strings
    combined_input = f"{str(hw_type)} {str(apps_sw)} {str(report_type)} {str(report_desc)}"

    # Predict the action
    action = model.predict([combined_input])[0]
    return action


def respond(hw_type, apps_sw, report_type, report_desc, chat_history=None):
    """
    Handle user messages and return the response.
    """
    if chat_history is None:
        chat_history = []

    action = recommend_action(hw_type, apps_sw, report_type, report_desc)
    bot_message = f"Recommended Action: {action}"
    chat_history.append((
                        f"Hardware Type: {hw_type}\nSoftware/Application: {apps_sw}\nReport Type: {report_type}\nProblem Description: {report_desc}",
                        bot_message))
    return hw_type, apps_sw, report_desc, chat_history


# Load, preprocess data, and train the model once when the module is loaded
df = preprocess_data(load_data())
model = train_model(df)
'''

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import os
import django

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Trial.settings')
django.setup()

# Import the Ticket model
from app1.models import Ticket

# Global variable to hold the model
model = None


def load_data(hw_type=None, report_type=None):
    """
    Load data from the Django model, optionally filtered by hw_type and report_type.
    """
    filters = {}
    if hw_type:
        filters['hw_type'] = hw_type
    if report_type:
        filters['report_type'] = report_type

    tickets = Ticket.objects.filter(**filters).values('hw_type', 'apps_sw', 'report_type', 'report_desc', 'act_taken')
    df = pd.DataFrame.from_records(tickets)

    # Debugging output
    print("Loaded DataFrame:")
    print(df.head())  # Print the first few rows for debugging
    return df


def preprocess_data(df):
    """
    Preprocess the data for model training.
    """
    required_columns = ['hw_type', 'apps_sw', 'report_type', 'report_desc']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing columns: {', '.join(missing_columns)}")

    # Preprocess data
    for col in required_columns:
        df[col] = df[col].str.lower().fillna('')
    df['combined'] = df['hw_type'] + ' ' + df['apps_sw'] + ' ' + df['report_type'] + ' ' + df['report_desc']
    return df


def train_model(df):
    """
    Train a machine learning model using the preprocessed data.
    """
    # Handle missing values in 'combined' and 'act_taken' columns
    df = df[['combined', 'act_taken']].dropna(subset=['combined', 'act_taken'])

    # Split the data into training and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        df['combined'], df['act_taken'], test_size=0.2, random_state=42
    )

    # Handle any missing or invalid values in y_train (target variable)
    if y_train.isnull().any():
        raise ValueError("Target variable contains null values after splitting.")

    # Ensure that the target variable doesn't have invalid types (like None)
    y_train = y_train.fillna("Unknown")  # Or another sensible default value
    y_test = y_test.fillna("Unknown")

    # Create and train a model pipeline with TF-IDF and RandomForestClassifier
    model = make_pipeline(TfidfVectorizer(), RandomForestClassifier(random_state=42))
    model.fit(X_train, y_train)

    # Make predictions on the test set
    y_pred = model.predict(X_test)

    # Evaluate the model
    print("Model Training Report:")
    print(classification_report(y_test, y_pred))

    return model


def recommend_action(hw_type, apps_sw, report_type, report_desc):
    """
    Recommend an action based on user input.
    """
    combined_input = f"{str(hw_type)} {str(apps_sw)} {str(report_type)} {str(report_desc)}"

    # Predict the action
    if model:
        action = model.predict([combined_input])[0]
        print(f"Recommended Action: {action}")  # Debugging output
        return action
    else:
        raise ValueError("Model has not been trained yet.")


def update_model_with_new_data(hw_type, apps_sw, report_type, report_desc, action):
    """
    Update the model with new data after user input.
    """
    # Load new data with specific filters if needed
    df = load_data(hw_type=hw_type, report_type=report_type)
    df = preprocess_data(df)

    # Include new data into the DataFrame
    new_data = pd.DataFrame({
        'hw_type': [hw_type],
        'apps_sw': [apps_sw],
        'report_type': [report_type],
        'report_desc': [report_desc],
        'combined': [f"{hw_type} {apps_sw} {report_type} {report_desc}"],
        'act_taken': [action]
    })
    df = pd.concat([df, new_data], ignore_index=True)
    df = preprocess_data(df)

    # Train the model with updated data
    global model
    model = train_model(df)


# Load, preprocess data, and train the model once when the module is loaded
df = preprocess_data(load_data())
model = train_model(df)
