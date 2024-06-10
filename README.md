# Machine Learning Based Fraud Detection

## Project Structure

```
├── app.py @Flask App
├── data
│   ├── keys
│   │   ├── private_key.pem
│   │   └── public_key.pem
│   ├── tokens
│   └── users.db @SQLite DB
├── forms.py
├── requirements.txt
├── service
│   ├── clean_db.py
│   ├── database_connect.py
│   ├── generate_key.py
│   ├── security.py
│   └── user_authorization.py
├── static @CSS and JS resources
├── templates @HEML Templates
└── utils.py
```

## How to Run the Code

1. **Setting Up the Environment**:
   
    - Ensure you have Python installed on your machine. For MongoDB database, I suggest using MongoDB Atlas.
    
    - Install the required dependencies using:
      
    - Then change database connection information in `service/database_connect.py`
      
      ```
      pip install -r requirements.txt
      ```
    
2. **Running the Main Application**:
   
    - Once the dependencies are installed, you can run the application:
      ```
      flask run
      ```
    
3. **Database and Security**:
   
    - You can generate new security public and private keys, run:
      ```
      python netget/generate_key.py
      ```

The default port is 5000, and default username and password are both `admin`.
