import base64
import time
from uuid import uuid4

from flask import Flask, request, jsonify
from flask import render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user
from flask_paginate import Pagination, get_page_parameter

import service.security
from forms import LoginForm
from service.user_authorization import *
from utils import *

VALID_TOKEN = None

# Read the file and load tokens into a list
with open("./data/tokens", 'r') as file:
    VALID_TOKEN = [line.strip() for line in file if line.strip()]

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # The name of the login view function


@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return User(username=user['user_name'], user_id=user['user_id'])
    return None


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = get_user_info(username)

        if user and User.check_password(user['user_password'], password):
            user_obj = User(username=username, user_id=user['user_id'])
            login_user(user_obj)
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid login"
            flash('Invalid username or password')

    return render_template('login.html', form=form, error=error)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))  # Assuming you have a 'login' route defined


@app.route('/change_password', methods=['POST'])
def change_password():
    old_password = request.form['old-password']
    new_password = request.form['new-password']
    confirm_password = request.form['confirm-password']
    #
    # # Validate old password
    # user = load_user(current_user.get_id())
    # if not user or not check_password_hash(user.password, old_password):
    #     flash('Invalid old password.', 'error')
    #     return redirect(url_for('settings'))
    #
    # # Validate new password
    # if new_password != confirm_password:
    #     flash('The new password and confirm password do not match.', 'error')
    #     return redirect(url_for('settings'))
    #
    # # Update password hash and save
    # new_password_hash = generate_password_hash(new_password)
    # user.password = new_password_hash
    # save_user(user)

    flash('Password changed successfully!', 'success')
    return redirect(url_for('settings'))


@app.route('/')
@login_required
def dashboard():
    # Getting the latest 10 transactions sorted by timestamp
    transactions_collection = service.database_connect.collection
    transactions = list(transactions_collection.find({}).sort("timestamp", pymongo.DESCENDING).limit(10))

    # Format the timestamp for each transaction
    for transaction in transactions:
        transaction["formatted_date"] = datetime.datetime.utcfromtimestamp(transaction["timestamp"] / 1000).strftime(
            '%Y-%m-%d %H:%M:%S.%f')[:-3]
        # Rounding the transaction amount
        transaction["TransactionAmt"] = round(transaction["TransactionAmt"], 2)
        # Adjusting the card1 format
        transaction["card1"] = str(int(transaction["card1"])) + "****"

    total_records = transactions_collection.count_documents({})

    # Calculate the total sum of amounts
    total_amount = transactions_collection.aggregate([
        {
            "$group": {
                "_id": None,
                "totalAmount": {"$sum": "$TransactionAmt"}
            }
        }
    ])

    # If there's a result from the aggregation, extract the totalAmount; otherwise, set it to 0
    total_amount = list(total_amount)
    total_amount = round(total_amount[0]["totalAmount"], 2) if total_amount else 0
    fraud_count = user_collection.count_documents({"prediction": 1})

    data = {
        'transactions': transactions,
        'total_number': total_records,
        'fraud': fraud_count,
        'amounts': total_amount
    }

    return render_template('index.html', active_page='dashboard', data=data)


@app.route('/details', methods=['GET'])
@login_required
def details():
    page = request.args.get(get_page_parameter(), type=int, default=1)  # for pagination
    # Get search query parameter if present
    search_id = request.args.get('id')

    total_records, transactions, message = get_detail_db_data(page, search_id)

    pagination = Pagination(page=page, total=total_records, per_page=15, record_name='transactions',
                            css_framework='bootstrap4')

    data = {
        'transactions': transactions,
        'pagination': pagination if not search_id else None
    }

    return render_template('details.html', active_page='details', data=data, message=message)


@app.route('/statistics', methods=['GET'])
@login_required
def statistics():
    histogram_data, histogram_day_hour_data, device_system_frequencies, state_frequencies, email_frequencies = get_visualization_data()
    return render_template('statistics.html', active_page='statistics',
                           histogram_data=histogram_data,
                           histogram_day_hour_data=histogram_day_hour_data,
                           histogram_device_system_data=device_system_frequencies,
                           state_data=state_frequencies,
                           email_data=email_frequencies)


@app.route('/api/detect', methods=['POST'])
def detect():
    token = request.args.get('tokenid')
    data = request.args.get('data')
    otp = request.args.get('otp')

    if not token or token not in VALID_TOKEN:
        return jsonify({"error": "Invalid or missing token"}), 401

    try:
        # Convert the string data to JSON format
        decrypted_aes_key = service.security.decrypt_key_with_rsa("data/keys/private_key.pem",
                                                                  base64.b64decode(otp))
        # print("Receive key:\n",decrypted_aes_key)
        # print("Receive data:\n", data)
        decrypted_data = service.security.decrypt_with_aes(decrypted_aes_key, data)
        data_json = json.loads(decrypted_data)
    except:
        return jsonify({"error": "Invalid input data"}), 400
    # Predict

    trans_data = data_json['Transaction']
    user_data = data_json['User']

    label, lgbm_prob, xgb_prob = get_predict(trans_data)

    # Process the data and generate a response
    # For this example, we'll just return the data as is
    # res = ml_models.predict.get_predict(data_json)
    # Add uuid and timestamp fields
    trans_data["uuid"] = str(uuid4())
    trans_data["timestamp"] = int(time.time() * 1000)  # Current time in milliseconds

    score_dict = {"uuid": trans_data["uuid"],
                  "lgbm_prob": float(round(lgbm_prob, 5)),
                  "xgb_prob": float(round(xgb_prob, 5)),
                  "prediction": label}

    user_data["uuid"] = trans_data["uuid"]

    # Insert into MongoDB
    score_return = score_dict.copy()
    service.database_connect.result_collection.insert_one(score_dict)
    service.database_connect.collection.insert_one(trans_data)
    service.database_connect.user_collection.insert_one(user_data)

    return jsonify(score_return)


@app.route('/process', methods=['GET'])
@login_required
def process():
    transactions = get_suspect_data()
    data = {'transactions': transactions}
    return render_template('process.html', active_page='process', data=data)


@app.route('/get_transaction_details', methods=['GET'])
@login_required
def get_transaction_details():
    uuid = request.args.get('uuid')
    transaction = get_transaction_by_uuid(uuid)
    if not transaction:
        return "Transaction not found", 404
    details_html = render_template('transaction_details.html', transaction=transaction)
    return details_html


def get_transaction_by_uuid(uuid):
    transactions_collection = collection
    transaction = transactions_collection.aggregate([
        {"$match": {"uuid": uuid}},
        {
            "$lookup": {
                "from": "results",
                "localField": "uuid",
                "foreignField": "uuid",
                "as": "transaction_details"
            }
        },
        {"$unwind": "$transaction_details"},
        {
            "$lookup": {
                "from": "users",
                "localField": "uuid",
                "foreignField": "uuid",
                "as": "user_details"
            }
        }
    ])
    transaction = next(transaction, None)
    if transaction:
        transaction["formatted_date"] = datetime.datetime.utcfromtimestamp(transaction["timestamp"] / 1000).strftime(
            '%Y-%m-%d %H:%M:%S.%f')[:-3]
        transaction["TransactionAmt"] = round(transaction["TransactionAmt"], 2)
        transaction["card1"] = str(int(transaction["card1"])) + "****"
        transaction["ProductID"] = transaction["user_details"][0]["ProductID"]
        transaction["lgbm_prob"] = round(transaction["transaction_details"]["lgbm_prob"], 3)
        transaction["xgb_prob"] = round(transaction["transaction_details"]["xgb_prob"], 3)
        transaction["prediction"] = transaction["transaction_details"].get("prediction", -1)
        transaction["DeviceSystem"] = transaction["user_details"][0]["OperatingSystem"]
        transaction["Postcode"] = transaction["user_details"][0]["ZIPCode"]
        transaction["Email"] = "***" + transaction["user_details"][0]["UserEmail"][3:]
    return transaction


@app.route('/update_transaction_label', methods=['POST'])
@login_required
def update_transaction_label():
    uuid = request.form.get('uuid')
    label = int(request.form.get('label'))
    update_label_in_db(uuid, label)
    return "Label updated", 200


def update_label_in_db(uuid, label):
    print(f"Update prediction {uuid} to {label}")
    result_collection.update_one({'uuid': uuid}, {'$set': {'prediction': label}})


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        if request.form.get('action') == 'train_model':
            # Get timestamp and call the function
            ret = train_model()
            if ret:
                flash('Model training initiated successfully!', 'success')
            else:
                flash('Model training failed.', 'error')
            return redirect(url_for('settings'))
        else:
            # Retrieve values from form
            modelA_threshold = request.form.get('modelA-threshold', type=float)
            modelB_threshold = request.form.get('modelB-threshold', type=float)
            model1_path = request.form['model1-path']
            model2_path = request.form['model2-path']

            # Update config and save
            config = {
                "modelA_threshold": modelA_threshold,
                "modelB_threshold": modelB_threshold,
                "model1_path": model1_path,
                "model2_path": model2_path
            }
            save_config(config)
            return redirect(url_for('settings'))
    else:
        # Load existing config to prefill the form
        config = load_config()
        return render_template('settings.html', config=config, active_page='settings')


if __name__ == '__main__':
    app.run()
