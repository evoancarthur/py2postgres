import os
from fastapi import FastAPI, HTTPException
import psycopg2
import boto3
from botocore.exceptions import BotoCoreError, NoCredentialsError
from datetime import datetime

app = FastAPI()

@app.get("/")
def read_root():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {"message": "it works", "current_time": current_time}

@app.get("/db-connect")
def connect_to_db():
    db_region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "5432")  # Default PostgreSQL port
    db_sslomode = os.getenv("DB_SSL_MODE", "require")  # Default to 'require' if not set
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")

    if not db_host or not db_user or not db_name:
        raise HTTPException(status_code=500, detail="DB_HOST, DB_NAME and DB_USER must be set")

    if not db_pass:
        # Generate IAM Auth Token
        try:
            rds_client = boto3.client("rds", region_name=db_region)
            token = rds_client.generate_db_auth_token(
                DBHostname=db_host,
                Port=db_port,
                DBUsername=db_user
            )
        except (BotoCoreError, NoCredentialsError) as e:
            raise HTTPException(status_code=500, detail=f"Error generating IAM token: {str(e)}")
    else:
        token = db_pass  # Use the token directly if provided
    print (f"token received, now starting to connect to the database")
    # Connect to the database using the token
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=token,
            sslmode=db_sslomode
        )
        cur = conn.cursor()
        cur.execute("select table_name  from information_schema.tables where table_schema = 'public' order by table_name ;")
        tables = cur.fetchall()
        cur.close()
        conn.close()
        return tables
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to DB: {str(e)}")
