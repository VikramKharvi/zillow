import base64
import json
import mimetypes
import os
from pathlib import Path
from typing import List, Dict, Any
from openai import AzureOpenAI

import requests
import re
from bs4 import BeautifulSoup
import time

api_key = os.getenv("api_key")
api_version = os.getenv("api_version")
deployment_name = os.getenv("deployment_name")
api_base = os.getenv("api_base")

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff"}

def is_url(candidate: str) -> bool:
    """Return True if candidate looks like an HTTP(S) URL."""
    return candidate.startswith(("http://", "https://"))


def to_data_url(image_path: Path) -> str:
    """Convert a local image file to a data URL suitable for OpenAI Vision input."""
    mime_type, _ = mimetypes.guess_type(str(image_path))
    if not mime_type:
        mime_type = "image/png"

    with image_path.open("rb") as file_handle:
        encoded = base64.b64encode(file_handle.read()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"

def analyze_images(image_paths: List[str], model: str = "gpt-5-nano") -> Dict[str, Any]:
    """Analyze images using OpenAI's vision model and return structured assessment."""
    # Build content array starting with the prompt text
    content = [{"type": "text", "text": INSPECTION_PROMPT}]
    
    # Add each image to the content
    print("IMAGE URLS: ", image_paths)
    for image_path in image_paths:
        if is_url(image_path):
            # Direct URL
            image_url = image_path
        else:
            # Local file - convert to data URL
            path = Path(image_path)
            if not path.exists():
                print(f"Warning: File {image_path} not found, skipping...")
                continue
            if path.suffix.lower() not in IMAGE_EXTENSIONS:
                print(f"Warning: {image_path} is not a supported image format, skipping...")
                continue
            image_url = to_data_url(path)
        
        content.append({
            "type": "image_url",
            "image_url": {"url": image_url}
        })

    if len(content) == 1:  # Only the text prompt, no images
        raise ValueError("No valid images found to analyze.")

    response = client.chat.completions.create(
        model=model,
        messages=[
        {
            "role": "system",
            "content": "You are an expert real estate property inspector and appraiser."
        },
        {
            "role": "user",
            "content": content
        }]
        # response_format={"type": "json_object"}
    )

    response_content = response.choices[0].message.content or ""
    
    try:
        # Parse the JSON response
        analysis_result = json.loads(response_content)
        return analysis_result
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        print(f"Raw response: {response_content}")

        # Return a basic error structure
        return {
            "error": "Failed to parse response as JSON",
            "raw_response": response_content
        }

def extract_zillow_images(listing_url: str, max_images: int = 25) -> List[str]:
    """
    Extract image URLs from a Zillow property listing page.
    
    Args:
        listing_url (str): The Zillow listing URL
        max_images (int): Maximum number of images to return
    
    Returns:
        List[str]: List of image URLs
    """
    
    # More sophisticated headers to avoid detection
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    try:
        print(f"Fetching page: {listing_url}")
        
        # Add a small delay to appear more human-like
        time.sleep(1)
        
        response = session.get(listing_url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        image_urls = set()
        
        print("Searching for images...")
        
        # Method 1: Target the specific gallery div structure
        gallery_div = soup.find('div', {'data-testid': 'hollywood-gallery-images-tile-list'})
        if gallery_div:
            print("Found gallery div!")
            
            # Find all picture elements within the gallery
            pictures = gallery_div.find_all('picture')
            for picture in pictures:
                # Extract from srcset attributes in source tags
                sources = picture.find_all('source')
                for source in sources:
                    srcset = source.get('srcset', '')
                    if srcset and 'zillowstatic.com' in srcset:
                        # Parse srcset to get individual URLs
                        urls = re.findall(r'(https://photos\.zillowstatic\.com/[^\s,]+)', srcset)
                        for url in urls:
                            if any(ext in url for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                                image_urls.add(url)
                
                # Also check img tags within pictures
                img = picture.find('img')
                if img:
                    src = img.get('src', '')
                    if src and 'zillowstatic.com' in src:
                        image_urls.add(src)
        
        # Method 2: Look for any img tags with Zillow URLs as fallback
        img_tags = soup.find_all('img')
        for img in img_tags:
            src = img.get('src', '')
            data_src = img.get('data-src', '')
            
            for url in [src, data_src]:
                if url and 'zillowstatic.com' in url and any(ext in url for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                    image_urls.add(url)
        
        # Method 3: Look for images in script tags (JSON data)
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string and 'zillowstatic.com' in script.string:
                # Look for Zillow photo URLs in the script content
                zillow_urls = re.findall(r'https://photos\.zillowstatic\.com/[^"\']*\.(?:jpg|jpeg|png|webp)', script.string)
                for url in zillow_urls:
                    # Clean up the URL (remove any escaping)
                    clean_url = url.replace('\\', '')
                    image_urls.add(clean_url)
        
        # Method 4: Look for srcset attributes anywhere
        elements_with_srcset = soup.find_all(attrs={'srcset': True})
        for element in elements_with_srcset:
            srcset = element.get('srcset', '')
            if 'zillowstatic.com' in srcset:
                urls = re.findall(r'(https://photos\.zillowstatic\.com/[^\s,]+)', srcset)
                for url in urls:
                    if any(ext in url for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                        image_urls.add(url)
        
        print(f"Raw image URLs found: {len(image_urls)}")
        
        # Filter and prioritize URLs
        filtered_urls = []
        prioritized_urls = []
        
        for url in image_urls:
            # Skip very small images
            if any(size in url for size in ['_xs', '_s', 'thumbnail', '96x96', '144x144', '192']):
                continue
            
            # Prioritize larger images
            if any(size in url for size in ['_xl', '_l', 'uncropped', '1536', '1344', '1152', '960']):
                prioritized_urls.append(url)
            elif any(size in url for size in ['_m', '768', '576']):
                filtered_urls.append(url)
            else:
                filtered_urls.append(url)
        
        # Combine prioritized and regular URLs
        all_urls = prioritized_urls + filtered_urls
        print(f"Total images found: {len(all_urls)}")
        
        # Remove duplicates while preserving order
        unique_urls = list(dict.fromkeys(all_urls))[:max_images]
        return unique_urls
        
    except requests.RequestException as e:
        print(f"Error fetching the page: {e}")
        if "403" in str(e):
            print("Zillow is blocking the request. You may need to:")
            print("1. Use a VPN or different IP address")
            print("2. Try accessing the page in a browser first")
            print("3. Use a more sophisticated scraping solution")
        return []
    except Exception as e:
        print(f"Error parsing the page: {e}")
        return []

def analyze_zillow_property(listing_url: str, model: str = "gpt-4o", max_images: int = 25) -> Dict[str, Any]:
    """
    Extract images from a Zillow listing and analyze them.
    
    Args:
        listing_url (str): The Zillow listing URL
        model (str): The OpenAI model to use for analysis
    
    Returns:
        Dict[str, Any]: Property analysis results
    """
    
    # Extract image URLs from the listing
    image_urls = extract_zillow_images(listing_url, max_images)
    
    if not image_urls:
        return {
            "error": "No images found on the listing page",
            "listing_url": listing_url
        }
        
    # Analyze the images
    try:
        analysis = analyze_images(image_urls, model=model)
        
        # Add metadata about the source
        analysis["source"] = {
            "listing_url": listing_url,
            "images_analyzed": len(image_urls),
            "image_urls": image_urls
        }
        
        return analysis
    
    except Exception as e:
        return {
            "error": f"Analysis failed: {str(e)}",
            "listing_url": listing_url,
            "images_found": len(image_urls)
        }


if __name__ == "__main__":
    with open("prompts/image_analysis_prompt.txt", "r") as file:
        INSPECTION_PROMPT = file.read()

    client = AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        base_url=f"{api_base}/openai/deployments/{deployment_name}"
    )

    # listing_url = "https://www.zillow.com/homedetails/1261-Dirigo-Rd-Upper-Enchanted-Twp-ME-04945/2070181769_zpid/"
    LISTING_URL = "https://www.zillow.com/homedetails/35-Nancy-St-Moncton-NB-E1E-3T2/448708442_zpid/"
    MODEL = "gpt-4o"
    MAX_IMAGES = 20

    print("Running complete property analysis...")
    property_analysis = None
    RETRIES = 3
    while property_analysis is None or "error" in property_analysis:
        property_analysis = analyze_zillow_property(LISTING_URL, 
                                                    model=MODEL,
                                                    max_images=MAX_IMAGES)
        RETRIES -= 1
        if RETRIES == 0:
            print("Failed to analyze property after 3 retries.")
            break

    # Display the analysis results
    print("\n" + "="*60)
    print("PROPERTY IMAGES ANALYSIS REPORT")
    print("="*60)

    if "error" in property_analysis:
        print(f"Error: {property_analysis['error']}")
    else:
        # Display source information
        if "source" in property_analysis:
            source = property_analysis["source"]
            print(f"Property URL: {source['listing_url']}")
            print(f"Images Analyzed: {source['images_analyzed']}")
            print()
        
        # Use the same display logic as before
        if "exterior_curb_appeal" in property_analysis:
            print("EXTERIOR & CURB APPEAL:")
            exterior = property_analysis["exterior_curb_appeal"]
            for key, value in exterior.items():
                if isinstance(value, dict) and "score" in value:
                    print(f"  • {key.replace('_', ' ').title()}: {value['score']}/5")
                    print(f"    {value.get('explanation', 'No explanation provided')}\n")
        
        if "interior_condition" in property_analysis:
            print("INTERIOR CONDITION & QUALITY:")
            interior = property_analysis["interior_condition"]
            for key, value in interior.items():
                if isinstance(value, dict) and "score" in value:
                    print(f"  • {key.replace('_', ' ').title()}: {value['score']}/5")
                    print(f"    {value.get('explanation', 'No explanation provided')}\n")
        
        if "overall_summary" in property_analysis:
            print("OVERALL SUMMARY:")
            print(f"  {property_analysis['overall_summary']}\n")
        
        if "pros" in property_analysis:
            print("PROS:")
            for i, rec in enumerate(property_analysis["pros"], 1):
                print(f"  {i}. {rec}")
            print()
        
        if "cons" in property_analysis:
            print("CONS:")
            for i, rec in enumerate(property_analysis["cons"], 1):
                print(f"  {i}. {rec}")
            print()
        
        if "average_score" in property_analysis:
            print(f"AVERAGE SCORE: {property_analysis['average_score']}/5")
    

    