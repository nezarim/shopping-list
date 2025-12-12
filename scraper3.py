import requests
import gzip
import xml.etree.ElementTree as ET
import json
from io import BytesIO

BASE_URL = "https://kingstore.binaprojects.com"

def download_and_parse():
    """Download PriceFull file and parse it"""
    products = {}
    
    # Get one PriceFull file
    filename = "PriceFull7290058108879-001-202512121031.gz"
    url = f"{BASE_URL}/Download.aspx?FileNm={filename}"
    
    print(f"Downloading: {url}")
    response = requests.get(url, timeout=120)
    print(f"Response size: {len(response.content)} bytes")
    
    # Save raw for debugging
    with open('raw_file.gz', 'wb') as f:
        f.write(response.content)
    
    # Try to decompress
    try:
        with gzip.GzipFile(fileobj=BytesIO(response.content)) as f:
            xml_content = f.read().decode('utf-8')
        print(f"Decompressed size: {len(xml_content)} chars")
        
        # Save XML for debugging
        with open('raw_file.xml', 'w', encoding='utf-8') as f:
            f.write(xml_content[:50000])  # First 50k chars
        
        # Parse XML
        root = ET.fromstring(xml_content)
        print(f"Root tag: {root.tag}")
        
        # Find items - try various paths
        items = root.findall('.//Item')
        if not items:
            items = root.findall('.//Product')
        if not items:
            items = root.findall('.//*[ItemCode]')
        
        print(f"Found {len(items)} items")
        
        # Parse items
        for item in items:
            barcode = item.findtext('ItemCode') or item.findtext('Barcode')
            name = item.findtext('ItemName') or item.findtext('ManufacturerItemDescription') or item.findtext('ItemNm')
            price = item.findtext('ItemPrice') or item.findtext('Price')
            
            if barcode and name:
                products[barcode] = {
                    'name': name.strip(),
                    'price': float(price) if price else 0
                }
        
        print(f"Parsed {len(products)} products")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Try without gzip
        try:
            xml_content = response.content.decode('utf-8')
            print("Trying without gzip...")
            root = ET.fromstring(xml_content)
            print(f"Root: {root.tag}")
        except:
            print("Not valid XML either")
    
    return products

def main():
    products = download_and_parse()
    
    # Save to JSON
    with open('products_db.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    print(f"\nTotal: {len(products)} products saved to products_db.json")
    
    # Show sample
    print("\nSample:")
    for barcode, info in list(products.items())[:15]:
        print(f"  {barcode}: {info['name']} - ₪{info['price']}")

if __name__ == "__main__":
    main()
