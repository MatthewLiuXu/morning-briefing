from config import PORTFOLIO_TOKENS

def get_portfolio() -> dict:
    """
    Return portfolio positions.

    Replace this with a Google Sheets pull or database query
    if positions aren't hardcoded.
    """
    return PORTFOLIO_TOKENS


# --- OPTIONAL: Google Sheets version ---
# Uncomment and use this if your portfolio lives in a Google Sheet.
#
# from google.oauth2.service_account import Credentials
# from googleapiclient.discovery import build
#
# SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
# SHEET_ID = os.getenv("GOOGLE_SHEETS_ID")
# RANGE = "Portfolio!A2:D"  # columns: token_id, symbol, quantity, entry_price
#
# def get_portfolio_from_sheets() -> dict:
#     creds = Credentials.from_service_account_file(
#         "credentials.json", scopes=SCOPES
#     )
#     service = build("sheets", "v4", credentials=creds)
#     result = service.spreadsheets().values().get(
#         spreadsheetId=SHEET_ID, range=RANGE
#     ).execute()
#     rows = result.get("values", [])
#
#     portfolio = {}
#     for row in rows:
#         token_id, symbol, qty, entry = row
#         portfolio[token_id] = {
#             "symbol": symbol,
#             "quantity": float(qty),
#             "entry_price": float(entry),
#         }
#     return portfolio
