import urllib.parse
from bs4 import BeautifulSoup
import requests

def build_capcenter_url(params: dict) -> str:
    base_url = "https://www.capcenter.com/mortgage-calculator/purchase/conventional"
    
    # Prefix all keys with 'quoteWidget[...]'
    prefixed_params = {
        f"quoteWidget[{key}]": value for key, value in params.items()
    }

    # URL encode the parameters
    query_string = urllib.parse.urlencode(prefixed_params, quote_via=urllib.parse.quote)

    return f"{base_url}?{query_string}"

def extract_monthly_payment_from_html(html):
    """
    Extracts the monthly payment value (e.g., $2,760) from a div with class 'col-4'.
    """
    soup = BeautifulSoup(html, "html.parser")
    col4_divs = soup.find_all("div", class_="col-4")
    for div in col4_divs:
        strong_tags = div.find_all("strong")
        for strong in strong_tags:
            text = strong.get_text(strip=True)
            if text.startswith("$"):
                return text
    return None

mortgage_data = {
    "price": 425000,
    "downDollar": 85000,
    "loanDollar": 340000,
    "FirstTimeHomeBuyer": "true",
    "purchasedWithinLastYear": "false",
    "rate": 0,
    "LoanProgram": "Conventional",
    "LoanPurpose": "Purchase",
    "LoanTerm": "30-Year Term",
    "LoanType": "Fixed",
    "PropertyType": "Single Family Residence",
    "PropertyUse": "Primary Residence",
    "address": "Richmond, VA, USA",
    "PropertyLocation": "Richmond, VA, USA",
    "CountyId": 123,
    "CountyRealty": "Yes",
    "NeedRealtyTeam": "Yes",
    "savings": "Realty",
    "BaseRate": 6.625,
    "Points": 0,
    "ProductCombinationId": 63,
    "StateId": 1,
    "region": "Central Va",
    "LoanAmountType": "Conforming",
    "refiOff": "false",
    "HomeownersInsuranceEscrow": 3000,
    "PropertyTax": 4000,
    "AnnualIncome": 100000,
    "ZipCode": 23249,
    "State": "VA"
}

# Generate and print the full URL
url = build_capcenter_url(mortgage_data)
print(url)
print(extract_monthly_payment_from_html(url))
