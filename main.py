#!/usr/bin/env python3
"""
Main script to run Zillow scraping operations in sequence:
1. Scrape Zillow listings and save to data/zillow_listings.csv
2. Get rental price estimates for each listing and save to data/zillow_listings-1.csv
"""

import subprocess
import sys
import os

def run_script(script_name, description):
    """Run a Python script and handle any errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors:")
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}:")
        print(f"Return code: {e.returncode}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"Script {script_name} not found!")
        return False

def main():
    """Main function to run both scraping operations."""
    print("Zillow Scraping Pipeline")
    print("This will:")
    print("1. Scrape Zillow listings for Austin, TX")
    print("2. Get rental price estimates for each listing")
    print("3. Save results to data/ directory")
    
    # Check if data directory exists
    if not os.path.exists('data'):
        print("\nCreating data directory...")
        os.makedirs('data')
    
    # Step 1: Scrape Zillow listings
    success1 = run_script('scrape_zillow.py', 'Zillow Listings Scraper')
    
    if not success1:
        print("\n❌ Failed to scrape Zillow listings. Stopping.")
        return
    
    # Check if the listings file was created
    if not os.path.exists('data/zillow_listings.csv'):
        print("\n❌ No listings file created. Stopping.")
        return
    
    # Step 2: Get rental price estimates
    success2 = run_script('zillow_rental_price_scraper.py', 'Zillow Rental Price Scraper')
    
    if success2:
        print(f"\n{'='*60}")
        print("✅ SUCCESS! Both operations completed.")
        print("Files created:")
        if os.path.exists('data/zillow_listings.csv'):
            print("  - data/zillow_listings.csv (original listings)")
        if os.path.exists('data/zillow_listings-1.csv'):
            print("  - data/zillow_listings-1.csv (with rental estimates)")
        print(f"{'='*60}")
    else:
        print("\n❌ Failed to get rental price estimates.")

if __name__ == "__main__":
    main()
