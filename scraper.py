import requests
import gzip
import xml.etree.ElementTree as ET
import json
import os
from io import BytesIO

# Shufersal prices URL
SHUFERSAL_URL = "http://prices.shufersal.co.il/FileObject/UpdateCategory?catID=2&storeId=0"

def scrape_shufersal():
    """Scrape Shufersal prices from their public XML files"""
    products = {}
    
    print("Fetching Shufersal file list...")
    
    try:
        # Get the list of price files
        response = requests.get(SHUFERSAL_URL, timeout=30)
        response.raise_for_status()
        
        # Parse HTML to find gz file links
        from html.parser import HTMLParser
        
        class LinkParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.links = []
            
            def handle_starttag(self, tag, attrs):
                if tag == 'a':
                    for attr, value in attrs:
                        if attr == 'href' and value.endswith('.gz'):
                            self.links.append(value)
        
        parser = LinkParser()
        parser.feed(response.text)
        
        print(f"Found {len(parser.links)} price files")
        
        # Download and parse first few files (for demo)
        for i, link in enumerate(parser.links[:3]):
            print(f"Processing file {i+1}: {link}")
            try:
                file_response = requests.get(link, timeout=60)
                file_response.raise_for_status()
                
                # Decompress gzip
                with gzip.GzipFile(fileobj=BytesIO(file_response.content)) as f:
                    xml_content = f.read().decode('utf-8')
                
                # Parse XML
                root = ET.fromstring(xml_content)
                
                # Find all items
                for item in root.findall('.//Item'):
                    barcode = item.findtext('ItemCode') or item.findtext('Barcode')
                    name = item.findtext('ItemName') or item.findtext('ManufacturerItemDescription')
                    price = item.findtext('ItemPrice')
                    
                    if barcode and name:
                        products[barcode] = {
                            'name': name,
                            'price': float(price) if price else 0
                        }
                
                print(f"  Found {len(products)} products so far")
                
            except Exception as e:
                print(f"  Error processing file: {e}")
                continue
                
    except Exception as e:
        print(f"Error fetching file list: {e}")
    
    return products

def main():
    print("Starting Shufersal scraper...")
    products = scrape_shufersal()
    
    print(f"\nTotal products found: {len(products)}")
    
    # Save to JSON
    output_file = "products_db.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    print(f"Saved to {output_file}")
    
    # Show sample
    print("\nSample products:")
    for i, (barcode, info) in enumerate(list(products.items())[:10]):
        print(f"  {barcode}: {info['name']} - ₪{info['price']}")

if __name__ == "__main__":
    main()
