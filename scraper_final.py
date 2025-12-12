import requests
import zipfile
import xml.etree.ElementTree as ET
import json
from io import BytesIO
from datetime import datetime

BASE_URL = "https://kingstore.binaprojects.com"

def get_files():
    """Get list of price files"""
    url = f"{BASE_URL}/MainIO_Hok.aspx"
    today = datetime.now().strftime("%d/%m/%Y")

    params = {
        'Store': '',
        'FileType': 'PriceFull',
        'Date': today,
        'Wession': ''
    }

    response = requests.get(url, params=params, timeout=30)
    return response.json()

def get_download_url(filename):
    """Get actual download URL for a file"""
    url = f"{BASE_URL}/Download.aspx?FileNm={filename}"
    response = requests.get(url, timeout=30)
    data = response.json()
    if data and len(data) > 0 and 'SPath' in data[0]:
        return data[0]['SPath']
    return None

def download_and_parse(file_url):
    """Download ZIP file and parse XML"""
    products = {}

    print(f"Downloading: {file_url}")
    response = requests.get(file_url, timeout=120)
    print(f"Size: {len(response.content)} bytes")

    # Extract from ZIP
    with zipfile.ZipFile(BytesIO(response.content)) as zf:
        xml_filename = zf.namelist()[0]
        xml_content = zf.read(xml_filename).decode('utf-8')

    print(f"Parsing XML ({len(xml_content)} chars)...")

    # Parse XML
    root = ET.fromstring(xml_content)

    # Find all items
    items = root.findall('.//Item')
    print(f"Found {len(items)} items")

    for item in items:
        barcode = item.findtext('ItemCode')
        name = item.findtext('ItemNm') or item.findtext('ManufacturerItemDescription')
        price = item.findtext('ItemPrice')
        manufacturer = item.findtext('ManufacturerName')
        unit = item.findtext('UnitOfMeasure')

        if barcode and name:
            products[barcode] = {
                'name': name.strip(),
                'price': float(price) if price else 0,
                'manufacturer': manufacturer.strip() if manufacturer else '',
                'unit': unit.strip() if unit else ''
            }

    return products

def main():
    all_products = {}

    print("Getting file list...")
    files = get_files()
    print(f"Found {len(files)} files")

    # Get PriceFull files (usually contains all products)
    price_full_files = [f for f in files if 'PriceFull' in f.get('FileNm', '')]
    print(f"Found {len(price_full_files)} PriceFull files")

    # Download more files to get more products
    for f in price_full_files[:10]:
        filename = f.get('FileNm')
        print(f"\nProcessing: {filename}")

        # Get actual download URL
        download_url = get_download_url(filename)
        if not download_url:
            print("  Could not get download URL")
            continue

        # Download and parse
        try:
            products = download_and_parse(download_url)
            all_products.update(products)
            print(f"  Added {len(products)} products (total: {len(all_products)})")
        except Exception as e:
            print(f"  Error: {e}")

    print(f"\n{'='*50}")
    print(f"Total: {len(all_products)} products")

    # Save to JSON
    with open('products_db.json', 'w', encoding='utf-8') as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)

    print(f"Saved to products_db.json")

    # Show sample
    print("\nSample products:")
    for barcode, info in list(all_products.items())[:20]:
        print(f"  {barcode}: {info['name']} - ₪{info['price']}")

if __name__ == "__main__":
    main()
