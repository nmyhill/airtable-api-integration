import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
BASE_ID = os.getenv("BASE_ID")
TABLE_NAME = os.getenv("TABLE_NAME")

def fetch_records(max_records=5):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}?maxRecords={max_records}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_TOKEN}"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()