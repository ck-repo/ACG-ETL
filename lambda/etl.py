import pandas as pd
import boto3
import os
from sqlalchemy import create_engine
import pymysql
import json

def extract_csv1(event, context):
# Extract 1st CSV

  cols = ["Date","Country/Region", "Recovered"]

  url1 = "https://raw.githubusercontent.com/datasets/covid-19/master/data/time-series-19-covid-combined.csv"

  rec = pd.read_csv(url1, usecols=cols)

  return rec

def extract_csv2(event):
# Extract 2nd CSV

  url2 = "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us.csv"

  data = pd.read_csv(url2)

  return data

def transform_csv(data, rec):
# Transform CSVs

  data = pd.DataFrame(data)   

  data = data.drop([0])

  data.rename(columns={'date': 'Date', 'cases': 'Cases', 'deaths': 'Deaths'}, inplace=True) 

  usrec = rec[rec["Country/Region"] == "US"]  

  usrec = usrec.drop(columns=['Country/Region'])

  data = data.merge(usrec, on='Date')

  return data

# Call Extract and Transform Functions

rec = extract_csv1({
  "key1": "value1"},1)

data = extract_csv2({
  "key1": "value1"})

data = transform_csv(data, rec)

def load_to_db(data):
# Retrieve AWS Secret

  secret_name = os.environ['SECRET_NAME']
  region_name = "eu-west-2"
  session = boto3.session.Session()
  client = session.client(
    service_name='secretsmanager',
    region_name=region_name)

  secret_value = client.get_secret_value(
    SecretId=secret_name)

  dbpass = secret_value['SecretString']
  j = json.loads(dbpass)
  dbpass = j['password']

# Load data to RDS

  rds_instance = os.environ['RDS_INSTANCE']
  
  db_con = 'mysql+pymysql://admin:%s@%s/covid' % (dbpass, rds_instance)

  sqlEngine = create_engine(db_con, pool_recycle=3600)

  dbConnection = sqlEngine.connect()

  tableName = 'coviddata'

  data.to_sql(tableName, dbConnection, if_exists='replace')
  
  return

data = load_to_db(data)