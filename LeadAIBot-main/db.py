from sqlalchemy import create_engine, Table, Column, String, MetaData, select
from sqlalchemy.sql import insert
import urllib
from datetime import datetime

#  credentials
server = '192.168.0.30'
database = 'VinayApplicationDB'
username = 'User5'
password = 'CDev005#8'
driver = 'ODBC Driver 17 for SQL Server'

params = urllib.parse.quote_plus(
    f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
)

engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
metadata = MetaData()

leads = Table(
    'leads', metadata,
    Column('job_title', String(100)),
    Column('location', String(100)),
    Column('linkedin_url', String(300)),
    Column('phone_number', String(20), primary_key=True),
    Column('requestSent', String(1))
)

def init_db():
    metadata.create_all(engine)

def save_lead(row):
    with engine.begin() as conn:
        stmt = insert(leads).values(
            job_title=row["job_title"],
            location=row["location"],
            linkedin_url=row["linkedin_url"],
            phone_number=row["phone_number"],
            requestSent="0"
        )
        try:
            conn.execute(stmt)
        except:
            pass

def is_message_sent(phone_number):
    with engine.connect() as conn:
        result = conn.execute(
            select(leads.c.phone_number).where(leads.c.phone_number == phone_number)
        ).fetchone()
      
        return result is not None

messages = Table(
    'messages', metadata,
    Column('id', String(50), primary_key=True),
    Column('phone_number', String(20)),
    Column('message_in', String(1000)),
    Column('message_out', String(1000)),
    Column('timestamp', String(50))
)

def save_message(phone_number, message_in, message_out):
    with engine.begin() as conn:
        stmt = insert(messages).values(
            phone_number=phone_number,
            message_in=message_in,
            message_out=message_out,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        conn.execute(stmt)