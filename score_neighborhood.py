import requests
import json
import re
from typing import Dict, Optional
from datetime import datetime

def calculate_neighbourhood_score(census_data: Dict) -> Dict:
    """
    Calculate a comprehensive neighbourhood score based on multiple factors.
    Returns the original data plus calculated scores and rankings.
    """
    if not census_data:
        return {}
    
    # Initialize scoring components
    scores = {}
    
    # Data freshness bonus (newer data gets slight bonus)
    data_age = census_data.get("data_age_years", 5)
    freshness_bonus = max(0, (5 - data_age) * 2)  # 0-10 point bonus for recent data
    
    # Income Score (0-100) - Higher income = higher score
    if census_data.get("median_household_income"):
        income = census_data["median_household_income"]
        if income < 30000:
            income_score = 0
        elif income < 50000:
            income_score = 25
        elif income < 75000:
            income_score = 50
        elif income < 100000:
            income_score = 75
        elif income < 150000:
            income_score = 90
        else:
            income_score = 100
        scores["income_score"] = round(income_score, 2)
    else:
        scores["income_score"] = 0
    
    # Property Value Score (0-100) - Higher property value = higher score
    if census_data.get("median_property_value"):
        prop_value = census_data["median_property_value"]
        if prop_value < 150000:
            prop_score = 0
        elif prop_value < 250000:
            prop_score = 25
        elif prop_value < 400000:
            prop_score = 50
        elif prop_value < 600000:
            prop_score = 75
        elif prop_value < 800000:
            prop_score = 90
        else:
            prop_score = 100
        scores["property_score"] = round(prop_score, 2)
    else:
        scores["property_score"] = 0
    
    # Homeownership Score (0-100) - Higher homeownership = higher score
    if census_data.get("homeownership_rate"):
        ownership_rate = census_data["homeownership_rate"]
        scores["homeownership_score"] = round(ownership_rate, 2)
    else:
        scores["homeownership_score"] = 0
    
    # Housing Age Score (0-100) - Newer housing = higher score
    if census_data.get("median_year_built"):
        year_built = census_data["median_year_built"]
        current_year = datetime.now().year
        if year_built >= 2010:
            year_score = 100
        elif year_built >= 2000:
            year_score = 85
        elif year_built >= 1990:
            year_score = 70
        elif year_built >= 1980:
            year_score = 55
        elif year_built >= 1970:
            year_score = 40
        elif year_built >= 1960:
            year_score = 25
        else:
            year_score = 10
        scores["housing_age_score"] = round(year_score, 2)
    else:
        scores["housing_age_score"] = 0
    
    # Population Density Score (0-100) - Moderate density = higher score
    if census_data.get("total_population"):
        population = census_data["total_population"]
        # Assume zipcode area of ~25 square miles, calculate density
        density = population / 25
        if 5000 <= density <= 15000:
            density_score = 100
        elif density < 5000:
            density_score = (density / 5000) * 100
        else:
            density_score = max(0, 100 - ((density - 15000) / 15000) * 100)
        scores["density_score"] = round(density_score, 2)
    else:
        scores["density_score"] = 0
    
    # Calculate weighted overall score
    weights = {
        "income_score": 0.25,
        "property_score": 0.25,
        "homeownership_score": 0.20,
        "housing_age_score": 0.15,
        "density_score": 0.15
    }
    
    overall_score = sum(scores[key] * weights[key] for key in weights.keys())
    overall_score += freshness_bonus
    scores["overall_score"] = round(overall_score, 2)
    scores["freshness_bonus"] = round(freshness_bonus, 2)
    
    # Add letter grade
    if overall_score >= 90:
        grade = "A+"
    elif overall_score >= 80:
        grade = "A"
    elif overall_score >= 70:
        grade = "B+"
    elif overall_score >= 60:
        grade = "B"
    elif overall_score >= 50:
        grade = "C+"
    elif overall_score >= 40:
        grade = "C"
    elif overall_score >= 30:
        grade = "D+"
    elif overall_score >= 20:
        grade = "D"
    else:
        grade = "F"
    
    scores["grade"] = grade
    
    # Combine original data with scores
    result = {**census_data, **scores}
    return result

def get_census_data(zipcode: int, api_key: str, year: str = "2022") -> Optional[Dict]:
    """
    Get comprehensive census data for a zipcode
    """
    try:
        url = f"https://api.census.gov/data/{year}/acs/acs5"
        
        params = {
            "get": "B19013_001E,B01003_001E,B25077_001E,B25064_001E,B25035_001E,B25003_002E,B25003_003E,B25002_002E,B25002_003E",
            "for": f"zip code tabulation area:{zipcode}",
            "key": api_key
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if len(data) < 2:
            print(f"No data found for zipcode {zipcode} in {year}")
            return None
            
        columns = data[0]
        values = data[1]
        
        census_data = {
            "zipcode": zipcode,
            "data_year": year,
            "median_household_income": int(values[0]) if values[0] != "null" else None,
            "total_population": int(values[1]) if values[1] != "null" else None,
            "median_property_value": int(values[2]) if values[2] != "null" else None,
            "median_gross_rent": int(values[3]) if values[3] != "null" else None,
            "median_year_built": int(values[4]) if values[4] != "null" else None,
            "owner_occupied_units": int(values[5]) if values[5] != "null" else None,
            "renter_occupied_units": int(values[6]) if values[6] != "null" else None,
            "occupied_units": int(values[7]) if values[7] != "null" else None,
            "vacant_units": int(values[8]) if values[8] != "null" else None
        }
        
        # Calculate additional metrics
        if census_data["total_population"] and census_data["occupied_units"]:
            total_units = census_data["occupied_units"] + census_data.get("vacant_units", 0)
            if total_units > 0:
                census_data["homeownership_rate"] = round(census_data["owner_occupied_units"] / total_units * 100, 2)
                census_data["rental_rate"] = round(census_data["renter_occupied_units"] / total_units * 100, 2)
                census_data["vacancy_rate"] = round(census_data.get("vacant_units", 0) / total_units * 100, 2)
        
        # Add current year context
        current_year = datetime.now().year
        census_data["current_year"] = current_year
        census_data["data_age_years"] = current_year - int(year)
        
        return census_data
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None
    except (ValueError, IndexError, KeyError) as e:
        print(f"Error parsing data: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def get_recent_census_data(zipcode: int, api_key: str) -> Optional[Dict]:
    """
    Try to get the most recent available census data by testing multiple years
    """
    years_to_try = ["2022", "2021", "2020", "2019"]
    
    for year in years_to_try:
        print(f"Trying to get {year} data for zipcode {zipcode}...")
        data = get_census_data(zipcode, api_key, year)
        if data:
            print(f"✅ Successfully retrieved {year} data (age: {data['data_age_years']} years)")
            return data
    
    print(f"❌ No data available for zipcode {zipcode} in any recent year")
    return None

def extract_zipcode_from_address(address: str) -> Optional[int]:
    """
    Extract zipcode from an address string
    """
    # Look for 5-digit zipcode pattern
    zipcode_match = re.search(r'\b(\d{5})\b', address)
    if zipcode_match:
        return int(zipcode_match.group(1))
    return None

def get_neighbourhood_score_for_address(address: str, api_key: str) -> Optional[Dict]:
    """
    Get neighbourhood score for a given address
    """
    print(f"Getting neighbourhood score for: {address}")
    
    # Extract zipcode from address
    zipcode = extract_zipcode_from_address(address)
    if not zipcode:
        print("❌ Could not extract zipcode from address")
        return None
    
    print(f"Extracted zipcode: {zipcode}")
    
    # Get census data
    census_data = get_recent_census_data(zipcode, api_key)
    if not census_data:
        print("❌ Could not retrieve census data")
        return None
    
    # Calculate neighbourhood score
    scored_data = calculate_neighbourhood_score(census_data)
    
    return scored_data

def main():
    """
    Main function to get neighbourhood score for a given address
    """
    # Your API key
    API_KEY = "49cf2b9501e8bb00629a9916d68f8b88ccd5ac9d"
    
    # Get address from user input
    address = input("Enter an address: ").strip()
    
    if not address:
        print("No address provided")
        return
    
    # Get neighbourhood score
    result = get_neighbourhood_score_for_address(address, API_KEY)
    
    if result:
        print("\n" + "="*60)
        print("NEIGHBOURHOOD SCORE RESULTS")
        print("="*60)
        print(f"Address: {address}")
        print(f"Zipcode: {result['zipcode']}")
        print(f"Overall Score: {result['overall_score']} ({result['grade']})")
        print(f"Data Year: {result['data_year']} (Age: {result['data_age_years']} years)")
        print("\nScore Breakdown:")
        print(f"  Income Score: {result['income_score']}")
        print(f"  Property Score: {result['property_score']}")
        print(f"  Homeownership Score: {result['homeownership_score']}")
        print(f"  Housing Age Score: {result['housing_age_score']}")
        print(f"  Density Score: {result['density_score']}")
        print(f"  Freshness Bonus: {result['freshness_bonus']}")
        print("\nKey Metrics:")
        print(f"  Median Household Income: ${result.get('median_household_income', 'N/A'):,}")
        print(f"  Median Property Value: ${result.get('median_property_value', 'N/A'):,}")
        print(f"  Homeownership Rate: {result.get('homeownership_rate', 'N/A')}%")
        print(f"  Median Year Built: {result.get('median_year_built', 'N/A')}")
        print("="*60)
    else:
        print("❌ Could not get neighbourhood score for this address")

if __name__ == "__main__":
    main()