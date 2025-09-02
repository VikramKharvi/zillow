import pandas as pd
import time
import urllib.parse
import re
import json
from bs4 import BeautifulSoup
import requests

def build_zillow_rental_url(address):
    """
    Build the Zillow rental price estimator URL for a given address.
    """
    encoded_address = urllib.parse.quote(address)
    return f"https://www.zillow.com/rental-manager/price-my-rental/results/{encoded_address}/"

def extract_json_object(js_text, var_name="window.__INITIAL_STATE__"):
    start = js_text.find(var_name)
    if start == -1:
        return None
    start = js_text.find("{", start)
    if start == -1:
        return None
    brace_count = 0
    for i in range(start, len(js_text)):
        if js_text[i] == "{":
            brace_count += 1
        elif js_text[i] == "}":
            brace_count -= 1
            if brace_count == 0:
                json_str = js_text[start:i+1]
                # Clean up: replace 'undefined' with null
                json_str = json_str.replace(":undefined", ":null")
                return json_str
    return None

def extract_rent_json(html):
    soup = BeautifulSoup(html, "html.parser")
    script_tags = soup.find_all("script", type="text/javascript")
    for script in script_tags:
        if script.string and "window.__INITIAL_STATE__" in script.string:
            json_str = extract_json_object(script.string)
            if json_str:
                try:
                    data = json.loads(json_str)
                    return data
                except Exception as e:
                    print(f"Error parsing JSON: {e}")
    return None

def get_rent_estimates(address, beds, baths):
    url = build_zillow_rental_url(address)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection": "keep-alive",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Failed to fetch Zillow rental estimate for {address}: {response.status_code}")
            return None
        data = extract_rent_json(response.text)
        rentZestimate = rentZestimateRangeHigh = rentZestimateRangeLow = marketMedianRent = None
        if data and 'address' in data:
            rentZestimate = data['address'].get('rentZestimate')
            rentZestimateRangeHigh = data['address'].get('rentZestimateRangeHigh')
            rentZestimateRangeLow = data['address'].get('rentZestimateRangeLow')
            marketSummary = data['address'].get('marketSummary', {})
            summary = marketSummary.get('summary', {})
            marketMedianRent = summary.get('medianRent')
        return {
            'address': address,
            'beds': beds,
            'baths': baths,
            'rentZestimate': rentZestimate,
            'rentZestimateRangeHigh': rentZestimateRangeHigh,
            'rentZestimateRangeLow': rentZestimateRangeLow,
            'marketMedianRent': marketMedianRent
        }
    except Exception as e:
        print(f"Error fetching Zillow rental estimate for {address}: {e}")
        return None

def main():
    """
    Reads zillow_listings.csv, queries Zillow rental estimator for each address, and updates the CSV with rental estimate columns.
    """
    df = pd.read_csv('data/zillow_listings.csv')
    # Prepare columns for rental estimates
    df['rentZestimate'] = None
    df['rentZestimateRangeHigh'] = None
    df['rentZestimateRangeLow'] = None
    df['marketMedianRent'] = None
    df['rentToPriceRatio'] = None  # Add new column for rent to price ratio
    for idx, row in df.iterrows():
        address = row.get('address')
        beds = row.get('beds')
        baths = row.get('baths')
        print(f"Querying Zillow rental estimate for: {address} ({beds} beds, {baths} baths)")
        rent_data = get_rent_estimates(address, beds, baths)
        print(rent_data)
        if rent_data:
            df.at[idx, 'rentZestimate'] = rent_data.get('rentZestimate')
            df.at[idx, 'rentZestimateRangeHigh'] = rent_data.get('rentZestimateRangeHigh')
            df.at[idx, 'rentZestimateRangeLow'] = rent_data.get('rentZestimateRangeLow')
            df.at[idx, 'marketMedianRent'] = rent_data.get('marketMedianRent')
        # Calculate rent to price ratio
        try:
            rent = float(df.at[idx, 'rentZestimate']) if df.at[idx, 'rentZestimate'] not in [None, '', 'nan'] else None
            price_str = str(row.get('price'))
            if price_str not in [None, '', 'nan']:
                # Remove $ and commas
                price_str = price_str.replace('$', '').replace(',', '').strip()
                price = float(price_str)
            else:
                price = None
            if rent and price and price != 0:
                ratio = (rent / price) * 100
                df.at[idx, 'rentToPriceRatio'] = round(ratio, 2)
            else:
                df.at[idx, 'rentToPriceRatio'] = None
        except Exception as e:
            df.at[idx, 'rentToPriceRatio'] = None
        time.sleep(2)  # Be polite to Zillow
    
    # Sort by rentToPriceRatio in descending order (highest ratios first)
    df_sorted = df.sort_values('rentToPriceRatio', ascending=False, na_position='last')
    
    df_sorted.to_csv('data/zillow_listings-1.csv', index=False)
    print("Updated data/zillow_listings.csv with rental estimates, sorted by rent-to-price ratio (highest first).")

if __name__ == "__main__":
    main() 