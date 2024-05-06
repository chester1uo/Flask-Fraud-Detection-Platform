import datetime
import json
import os
import pickle
from collections import Counter

import numpy as np
import pycountry

from service.database_connect import *


def convert_state_name_to_code(state_name):
    try:
        country = pycountry.countries.get(alpha_2='US')
        states = pycountry.subdivisions.get(country_code=country.alpha_2)
        for state in states:
            if state.name == state_name:
                return state.code[3:]
    except LookupError:
        pass

    return None


def load_config(filename='./data/config.json'):
    """
    Load configuration from a JSON file.

    Args:
    filename (str): The path to the JSON configuration file.

    Returns:
    dict: The configuration dictionary.
    """
    try:
        with open(filename, 'r') as file:
            config = json.load(file)
        return config
    except FileNotFoundError:
        print("Error: The configuration file does not exist.")
        return None
    except json.JSONDecodeError:
        print("Error: The configuration file is not in valid JSON format.")
        return None


config = load_config()

with open(config['model1_path'], 'rb') as f:
    loaded_xgb = pickle.load(f)

with open(config['model2_path'], 'rb') as f:
    loaded_lgbm = pickle.load(f)


def get_predict(record):
    config = load_config()

    threshold_1 = config['modelA_threshold']
    threshold_2 = config['modelB_threshold']

    # Convert the record into the required array format
    record_array = np.array(list(record.values())).reshape(1, -1)
    # print(record_array)

    # Stage 1: LGBM Model Classification
    lgbm_prob = loaded_lgbm.predict_proba(record_array)[0][1]

    # Initialize the final prediction and scores dictionary
    prediction = 0
    xgb_prob = -1

    if lgbm_prob > threshold_1 and lgbm_prob <= threshold_2:  # If the record is 'Suspect'
        # Stage 2: XGBoost Model Classification
        xgb_prob = loaded_xgb.predict_proba(record_array)[0][1]

        # Assigning the final prediction based on the second threshold
        prediction = 1 if xgb_prob > 0.5 else 0
    elif lgbm_prob > threshold_2:  # If the record is 'Fraudulent'
        prediction = 1

    return prediction, lgbm_prob, xgb_prob


# Path to the JSON file
CONFIG_FILE = './data/config.json'


def load_config():
    """Load the configuration from the JSON file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            return json.load(file)
    else:
        return {
            "modelA_threshold": 0.5,
            "modelB_threshold": 0.5,
            "model1_path": "",
            "model2_path": ""
        }


def save_config(config):
    """Save the configuration to the JSON file."""
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent=4)


def get_detail_db_data(page, search_id):
    # Getting the transactions with more attributes and joining with results collection
    transactions_collection = collection

    # Adjust the query to join the two collections based on UUID and get the results
    transactions = list(transactions_collection.aggregate([
        {
            "$lookup": {
                "from": "results",
                "localField": "uuid",
                "foreignField": "uuid",
                "as": "transaction_details"
            }
        },
        {"$unwind": "$transaction_details"},
        {"$sort": {"timestamp": -1}},
        {"$skip": (page - 1) * 15},
        {"$limit": 15},
        {
            "$lookup": {
                "from": "users",
                "localField": "uuid",
                "foreignField": "uuid",
                "as": "user_details"
            }
        }
    ]))

    message = ""
    # Apply search filter if search ID is provided
    if search_id:
        transactions = [transaction for transaction in transactions if transaction['uuid'] == search_id]
        if len(transactions) == 0:  # Not found record
            message = f"No results found for ID: {search_id}"

    # Format the data for display
    for transaction in transactions:
        # print(transaction)
        transaction["formatted_date"] = datetime.datetime.utcfromtimestamp(transaction["timestamp"] / 1000).strftime(
            '%Y-%m-%d %H:%M:%S.%f')[:-3]
        transaction["TransactionAmt"] = round(transaction["TransactionAmt"], 2)
        transaction["card1"] = str(int(transaction["card1"])) + "****"
        transaction["ProductID"] = transaction["user_details"][0]["ProductID"]
        transaction["lgbm_prob"] = round(transaction["transaction_details"]["lgbm_prob"], 3)
        transaction["xgb_prob"] = round(transaction["transaction_details"]["xgb_prob"], 3)
        if "prediction" in transaction["transaction_details"]:
            transaction["prediction"] = transaction["transaction_details"]["prediction"]
        elif "prediction:" in transaction["transaction_details"]:
            transaction["prediction"] = transaction["transaction_details"]["prediction:"]
        else:
            # If neither key is found, handle the situation accordingly
            transaction["prediction"] = -1
        transaction["DeviceSystem"] = transaction["user_details"][0]["OperatingSystem"]
        transaction["Postcode"] = transaction["user_details"][0]["ZIPCode"]
        transaction["Email"] = "***" + transaction["user_details"][0]["UserEmail"][3:]
        # transaction.update(transaction["transaction_details"])

    total_records = transactions_collection.count_documents({})
    return total_records, transactions, message


def get_visualization_data():
    transactions_collection = collection

    # Fetch all transaction amounts for histogram
    transactions = list(transactions_collection.find({}, {"TransactionAmt": 1, "_id": 0}))
    histogram_data = [t['TransactionAmt'] for t in transactions]

    # Fetch day hour values for histogram
    day_hour_transactions = list(transactions_collection.find({}, {"DT_hour": 1, "_id": 0}))
    histogram_day_hour_data = [t['DT_hour'] * 24 for t in day_hour_transactions]

    # Fetch device system values for histogram
    device_system_transactions = list(user_collection.find({}, {"OperatingSystem": 1, "_id": 0}))
    device_system_values = [t['OperatingSystem'] for t in device_system_transactions]
    device_system_frequencies = Counter(device_system_values)

    state_transactions = list(user_collection.find({}, {"State": 1, "_id": 0}))
    state_values = [convert_state_name_to_code(t['State']) for t in state_transactions]
    state_frequencies = Counter(state_values)

    email_transactions = list(user_collection.find({}, {"UserEmail": 1, "_id": 0}))
    email_values = [t['UserEmail'].split("@")[-1] for t in email_transactions]
    email_frequencies = Counter(email_values)
    return histogram_data, histogram_day_hour_data, device_system_frequencies, state_frequencies, email_frequencies


def get_user_info(username):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE user_name = ?', (username,)).fetchone()
    conn.close()
    return user


def train_model():
    return True
