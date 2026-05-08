import os
from io import StringIO

import pandas as pd
import requests
import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

load_dotenv()

SHEET_NAME = os.getenv("SHEET_NAME")
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
WORKSHEET_NAME = "2026"

URL = "https://www.transfermarkt.co.uk/treaty-united/leistungsdaten/verein/88224/reldata/%262025/plus/1"

PLAYER_ID_MAP = {
    "Jack Brady": "brady",
    "Dylan Ashman": "ashman",
    "Kevin Fitzpatrick": "fitzpatrick",
    "Ben Lynch": "blynch",
    "Eric Yoro": "yoro",
    "Richkov Boevi": "boevi",
    "Richard Lapointe": "lapointe",
    "Darren Nwankwo": "nwankwo",
    "Fionn Doherty": "doherty",
    "Mark Walsh": "walsh",
    "Robbie Lynch": "rlynch",
    "Kyle Foley": "foley",
    "Harry Sherlock": "sherlock",
    "Colin Conroy": "conroy",
    "Raphael Ohin": "ohin",
    "Steven Healy": "healy",
    "Benjamin Lee": "lee",
    "Niko Kozlowski": "kozlowski",
    "Matt Jones": "jones",
    "Mark Murphy": "mmurphy",
    "Jevontae Layne": "layne",
    "Mark Byrne": "byrne",
    "Cian Curtis": "curtis",
    "Roy Lawlor": "lawlor",
    "Ben Feeney": "feeney",
    "Jason Oyenuga": "oyenuga",
    "Brian Cunningham": "cunningham",
    "Cillian Mulvihill": "mulvihill",
    "Scott Murphy": "smurphy",
    "Tadhg Mc": "tadhgmc",
}

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-GB,en;q=0.9",
    "Referer": "https://www.transfermarkt.co.uk/",
}

response = requests.get(URL, headers=headers, timeout=20)
response.raise_for_status()

tables = pd.read_html(StringIO(response.text))

df = tables[1]

df = df[df["#"].notna()].copy()

df = df.rename(columns={
    "Player": "Name",
    "Unnamed: 5": "Appearances",
    "Unnamed: 7": "GoalsOrCleanSheets",
    "Unnamed: 8": "Assists",
    "Unnamed: 9": "Yellow",
    "Unnamed: 11": "Red",
})

df["Name"] = (
    df["Name"]
    .astype(str)
    .str.extract(r"([A-Z][a-z]+(?: [A-Z][a-z]+)+)")[0]
)

tm_df = df[
    ["Name", "Appearances", "GoalsOrCleanSheets", "Assists", "Yellow", "Red"]
].copy()

for col in ["Appearances", "GoalsOrCleanSheets", "Assists", "Yellow", "Red"]:
    tm_df[col] = pd.to_numeric(tm_df[col], errors="coerce").fillna(0).astype(int)

tm_df["Player Id"] = tm_df["Name"].map(PLAYER_ID_MAP)

missing_ids = tm_df[tm_df["Player Id"].isna()]
if not missing_ids.empty:
    print("WARNING: These players do not have mapped IDs:")
    print(missing_ids["Name"].tolist())

tm_df = tm_df[tm_df["Player Id"].notna()].copy()

final_df = tm_df[
    [
        "Player Id",
        "Appearances",
        "GoalsOrCleanSheets",
        "Assists",
        "Yellow",
        "Red",
    ]
].copy()

final_df = final_df.rename(columns={
    "GoalsOrCleanSheets": "Goals/Clean Sheets",
    "Yellow": "Yellow Cards",
    "Red": "Red Cards",
})

print(final_df)

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=scopes
)

client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME)
worksheet = sheet.worksheet(WORKSHEET_NAME)

worksheet.clear()

worksheet.update(
    f"A1:F{len(final_df) + 1}",
    [final_df.columns.tolist()] + final_df.fillna("").values.tolist()
)

print("Google Sheet updated successfully.")