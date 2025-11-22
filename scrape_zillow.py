import requests
from bs4 import BeautifulSoup
import urllib.parse
import json
import pandas as pd

def get_city_region_info(city, state=None):
    """Get region ID and type for a city. This is a simplified mapping."""
    # Common city mappings - you can expand this
    city_mappings = {
        "austin": {"region_id": 6752, "region_type": 6, "url_slug": "austin-tx"},
        "richmond": {"region_id": 6752, "region_type": 6, "url_slug": "richmond-va"},
        "houston": {"region_id": 6752, "region_type": 6, "url_slug": "houston-tx"},
        "dallas": {"region_id": 6752, "region_type": 6, "url_slug": "dallas-tx"},
        "san antonio": {"region_id": 6752, "region_type": 6, "url_slug": "san-antonio-tx"},
        "fort worth": {"region_id": 6752, "region_type": 6, "url_slug": "fort-worth-tx"},
        "arlington": {"region_id": 6752, "region_type": 6, "url_slug": "arlington-tx"},
        "plano": {"region_id": 6752, "region_type": 6, "url_slug": "plano-tx"},
        "irving": {"region_id": 6752, "region_type": 6, "url_slug": "irving-tx"},
        "frisco": {"region_id": 6752, "region_type": 6, "url_slug": "frisco-tx"}
    }
    
    city_key = city.lower()
    if city_key in city_mappings:
        return city_mappings[city_key]
    else:
        # Default to Austin for now - you can expand the mappings
        print(f"City '{city}' not found in mappings. Using Austin as default.")
        return city_mappings["austin"]

def build_zillow_url(
    city="austin",
    state=None,
    max_price=None,
    min_beds=None,
    min_baths=None,
    single_family=True,
    min_year_built=None,
    max_year_built=None,
    page=1
):
    """Builds a Zillow search URL with the given filters."""
    region_info = get_city_region_info(city, state)
    base_url = f"https://www.zillow.com/{region_info['url_slug']}/houses/"
    
    filter_state = {}
    if max_price is not None:
        filter_state["price"] = {"max": max_price}
    if min_beds is not None:
        filter_state["beds"] = {"min": min_beds}
    if min_baths is not None:
        filter_state["baths"] = {"min": min_baths}
    if single_family:
        filter_state["singleFamily"] = {"value": True}
    if min_year_built is not None or max_year_built is not None:
        year_built_filter = {}
        if min_year_built is not None:
            year_built_filter["min"] = min_year_built
        if max_year_built is not None:
            year_built_filter["max"] = max_year_built
        filter_state["built"] = year_built_filter
    
    search_query_state = {
        "pagination": {"currentPage": page},
        "regionSelection": [
            {"regionId": region_info["region_id"], "regionType": region_info["region_type"]}
        ],
        "filterState": filter_state,
        "isListVisible": True
    }
    search_query_state_json = json.dumps(search_query_state)
    encoded_state = urllib.parse.quote(search_query_state_json)
    return f"{base_url}?searchQueryState={encoded_state}"

def get_total_pages(soup):
    """Extracts the total number of pages from the pagination section."""
    pagination = soup.find('ul', class_=lambda x: x and 'PaginationList' in x)
    if pagination:
        page_links = pagination.find_all('a', title=True)
        page_numbers = []
        for link in page_links:
            try:
                num = int(link.text.strip())
                page_numbers.append(num)
            except Exception:
                continue
        if page_numbers:
            return max(page_numbers)
    return 1

def scrape_zillow_all_pages(city="austin", state=None, max_price=None, min_beds=None, min_baths=None, single_family=True, min_year_built=None, max_year_built=None):
    """Scrapes all Zillow pages for listings matching the given filters."""
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Connection": "keep-alive",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1"
    }
    all_listings = []
    prev_page_addresses = set()
    url = build_zillow_url(city=city, state=state, max_price=max_price, min_beds=min_beds, min_baths=min_baths, single_family=single_family, min_year_built=min_year_built, max_year_built=max_year_built, page=1)
    response = session.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch Zillow page 1: {response.status_code}")
        return []
    soup = BeautifulSoup(response.text, 'html.parser')
    total_pages = get_total_pages(soup)
    print(f"Total pages detected: {total_pages}")
    for page in range(1, total_pages + 1):
        url = build_zillow_url(city=city, state=state, max_price=max_price, min_beds=min_beds, min_baths=min_baths, single_family=single_family, min_year_built=min_year_built, max_year_built=max_year_built, page=page)
        url = "https://www.zillow.com/austin-tx/?searchQueryState=%7B%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22north%22%3A30.523705492376354%2C%22south%22%3A30.063628840598806%2C%22east%22%3A-97.48038334667967%2C%22west%22%3A-98.1519226533203%7D%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22globalrelevanceex%22%7D%2C%22price%22%3A%7B%22min%22%3Anull%2C%22max%22%3A450000%7D%2C%22beds%22%3A%7B%22min%22%3A4%2C%22max%22%3Anull%7D%2C%22baths%22%3A%7B%22min%22%3A3%2C%22max%22%3Anull%7D%2C%22built%22%3A%7B%22min%22%3A2000%2C%22max%22%3A2024%7D%7D%2C%22isListVisible%22%3Atrue%2C%22mapZoom%22%3A11%2C%22usersSearchTerm%22%3A%22Austin%2C%20TX%22%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A10221%2C%22regionType%22%3A6%7D%5D%7D"
        print(f"Scraping page {page}: {url}")
        response = session.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch Zillow page {page}: {response.status_code}")
            break
        soup = BeautifulSoup(response.text, 'html.parser')
        data_script = None
        for script in soup.find_all('script', type='application/json'):
            if 'cat1' in script.text:
                data_script = script.text
                break
        if not data_script:
            print(f"No embedded JSON data found on page {page}. Stopping.")
            break
        try:
            data = json.loads(data_script)
            search_results = data.get('props', {}).get('pageProps', {}).get('searchPageState', {}).get('cat1', {}).get('searchResults', {}).get('listResults', [])
            if not search_results:
                print(f"No more results on page {page}. Stopping.")
                break
            current_page_addresses = set()
            new_listings = []
            for item in search_results:
                address = item.get('address')
                price = item.get('price')
                link = item.get('detailUrl')
                beds = item.get('beds')
                baths = item.get('baths')
                if link and link.startswith('/'):
                    link = f"https://www.zillow.com/austin-tx/?searchQueryState=%7B%22isMapVisible%22%3Atrue%2C%22mapBounds%22%3A%7B%22north%22%3A30.523705492376354%2C%22south%22%3A30.063628840598806%2C%22east%22%3A-97.48038334667967%2C%22west%22%3A-98.1519226533203%7D%2C%22filterState%22%3A%7B%22sort%22%3A%7B%22value%22%3A%22globalrelevanceex%22%7D%2C%22price%22%3A%7B%22min%22%3Anull%2C%22max%22%3A450000%7D%2C%22beds%22%3A%7B%22min%22%3A4%2C%22max%22%3Anull%7D%2C%22baths%22%3A%7B%22min%22%3A3%2C%22max%22%3Anull%7D%2C%22built%22%3A%7B%22min%22%3A2000%2C%22max%22%3A2024%7D%7D%2C%22isListVisible%22%3Atrue%2C%22mapZoom%22%3A11%2C%22usersSearchTerm%22%3A%22Austin%2C%20TX%22%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A10221%2C%22regionType%22%3A6%7D%5D%7D"
                current_page_addresses.add(address)
                if address and address not in prev_page_addresses:
                    new_listings.append({
                        'address': address,
                        'price': price,
                        'beds': beds,
                        'baths': baths,
                        'link': link
                    })
            if not new_listings or current_page_addresses == prev_page_addresses:
                print(f"No new listings or repeated page on page {page}. Stopping.")
                break
            all_listings.extend(new_listings)
            prev_page_addresses = current_page_addresses
            print(f"Scraped page {page}, found {len(new_listings)} new listings.")
        except Exception as e:
            print(f"Error parsing embedded JSON on page {page}: {e}")
            break
    return all_listings

def main(city="austin", state=None):
    """Main entry point for scraping Zillow listings and saving to CSV."""
    max_price = 300000
    min_beds = 4
    min_baths = 3
    single_family = True
    min_year_built = 2023
    max_year_built = 2024
    
    print(f"Scraping listings for {city}{', ' + state if state else ''}")
    listings = scrape_zillow_all_pages(
        city=city,
        state=state,
        max_price=max_price,
        min_beds=min_beds,
        min_baths=min_baths,
        single_family=single_family,
        min_year_built=min_year_built,
        max_year_built=max_year_built
    )
    print(f"\nTotal listings found: {len(listings)}\n")
    if listings:
        df = pd.DataFrame(listings)
        df.to_csv('data/zillow_listings.csv', index=False)
        print("Listings saved to data/zillow_listings.csv")
    else:
        print("No listings found.")

if __name__ == "__main__":
    import sys
    
    city = "austin"
    state = None
    
    if len(sys.argv) > 1:
        city = sys.argv[1]
        if len(sys.argv) > 2:
            state = sys.argv[2]
        print(f"Using city: {city}{', ' + state if state else ''}")
    
    main(city, state)
