import requests
import gzip
import xml.etree.ElementTree as ET
import json
from io import BytesIO
from datetime import datetime

BASE_URL = "https://kingstore.binaprojects.com"

def get_stores():
    """Get list of stores"""
    url = f"{BASE_URL}/Select_Store.aspx"
    response = requests.get(url, timeout=30)
    return response.json()

def get_files(store_id="", file_type="PriceFull"):
    """Get list of price files"""
    url = f"{BASE_URL}/MainIO_Hok.aspx"
    today = datetime.now().strftime("%d/%m/%Y")
    
    params = {
        'Store': store_id,
        'FileType': file_type,
        'Date': today,
        'Wession': ''
    }
    
    response = requests.get(url, params=params, timeout=30)
    return response.json()

def download_file(filename):
    """Download a price file"""
    url = f"{BASE_URL}/Download.aspx"
    params = {'FileNm': filename}
    response = requests.get(url, params=params, timeout=60)
    return response.content

def parse_xml_content(content, is_gzipped=True):
    """Parse XML content from price file"""
    products = {}
    
    try:
        if is_gzipped:
            with gzip.GzipFile(fileobj=BytesIO(content)) as f:
                xml_content = f.read().decode('utf-8')
        else:
            xml_content = content.decode('utf-8')
        
        root = ET.fromstring(xml_content)
        
        # Try different XML structures
        for item in root.findall('.//Item') or root.findall('.//Product') or root.findall('.//item'):
            barcode = (item.findtext('ItemCode') or 
                      item.findtext('Barcode') or 
                      item.findtext('barcode') or
                      item.findtext('ItemBarcode'))
            
            name = (item.findtext('ItemName') or 
                   item.findtext('ManufacturerItemDescription') or
                   item.findtext('ItemNm') or
                   item.findtext('ProductName'))
            
            price = (item.findtext('ItemPrice') or 
                    item.findtext('Price') or
                    item.findtext('price'))
            
            if barcode and name:
                products[barcode] = {
                    'name': name.strip(),
                    'price': float(price) if price else 0
                }
    except Exception as e:
        print(f"Error parsing XML: {e}")
    
    return products

def main():
    all_products = {}
    
    print("Getting file list...")
    try:
        files = get_files()
        print(f"Response: {files}")
        
        if isinstance(files, list) and len(files) > 0:
            # Get first PriceFull file
            for f in files[:5]:
                filename = f.get('FileNm') or f.get('filename') or f.get('FileName')
                if filename and 'PriceFull' in str(filename):
                    print(f"Downloading: {filename}")
                    content = download_file(filename)
                    
                    # Try to parse
                    products = parse_xml_content(content)
                    if not products:
                        products = parse_xml_content(content, is_gzipped=False)
                    
                    all_products.update(products)
                    print(f"Found {len(products)} products")
                    
                    if len(all_products) > 1000:
                        break
                        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\nTotal: {len(all_products)} products")
    
    # Save
    with open('products_db.json', 'w', encoding='utf-8') as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)
    
    # Sample
    for barcode, info in list(all_products.items())[:10]:
        print(f"{barcode}: {info['name']} - ₪{info['price']}")

if __name__ == "__main__":
    main()
