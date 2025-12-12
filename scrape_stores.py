import requests
from bs4 import BeautifulSoup
import gzip
import zipfile
import xml.etree.ElementTree as ET
import json
from io import BytesIO
from datetime import datetime
import re

def get_coordinates_from_address(address, city):
    """Get coordinates using Nominatim (OpenStreetMap)"""
    try:
        query = f"{address}, {city}, Israel"
        url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
        headers = {'User-Agent': 'ShoppingListApp/1.0'}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
    except:
        pass
    return None, None

def scrape_shufersal():
    """Scrape Shufersal stores"""
    stores = []

    url = 'https://prices.shufersal.co.il/FileObject/UpdateCategory?storeId=0&catID=5&sort=Time&sortdir=DESC'
    response = requests.get(url, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')

    links = soup.find_all('a', href=True)
    for link in links:
        href = link.get('href', '')
        if 'blob.core' in href and 'Stores' in href:
            response = requests.get(href, timeout=30)
            with gzip.GzipFile(fileobj=BytesIO(response.content)) as f:
                content = f.read().decode('utf-8')

            # Parse XML
            root = ET.fromstring(content)
            for store in root.findall('.//STORE'):
                store_data = {
                    'chain': 'shufersal',
                    'chain_name': store.findtext('CHAINNAME', 'שופרסל'),
                    'subchain': store.findtext('SUBCHAINNAME', ''),
                    'store_id': store.findtext('STOREID', ''),
                    'name': store.findtext('STORENAME', ''),
                    'address': store.findtext('ADDRESS', ''),
                    'city': store.findtext('CITY', ''),
                    'zipcode': store.findtext('ZIPCODE', ''),
                    'lat': None,
                    'lon': None
                }
                stores.append(store_data)
            break

    print(f"Shufersal: {len(stores)} stores")
    return stores

def scrape_kingstore():
    """Scrape King Store stores"""
    stores = []

    # Get stores file
    url = "https://kingstore.binaprojects.com/MainIO_Hok.aspx"
    params = {'Store': '', 'FileType': 'Stores', 'Date': '', 'Wession': ''}
    response = requests.get(url, params=params, timeout=30)
    data = response.json()

    stores_files = [f for f in data if 'Stores' in f.get('FileNm', '')]
    if stores_files:
        filename = stores_files[0]['FileNm']

        # Get download URL
        url = f"https://kingstore.binaprojects.com/Download.aspx?FileNm={filename}"
        response = requests.get(url, timeout=30)
        real_url = response.json()[0]['SPath']

        # Download ZIP
        response = requests.get(real_url, timeout=60)
        with zipfile.ZipFile(BytesIO(response.content)) as zf:
            content = zf.read(zf.namelist()[0]).decode('utf-8')

        # Parse XML
        root = ET.fromstring(content)
        chain_name = root.findtext('.//ChainName', 'קינג סטור')

        for store in root.findall('.//Store'):
            store_data = {
                'chain': 'kingstore',
                'chain_name': chain_name,
                'subchain': '',
                'store_id': store.findtext('StoreId', ''),
                'name': store.findtext('StoreName', ''),
                'address': store.findtext('Address', ''),
                'city': store.findtext('City', ''),
                'zipcode': store.findtext('ZipCode', ''),
                'lat': None,
                'lon': None
            }
            stores.append(store_data)

    print(f"King Store: {len(stores)} stores")
    return stores

def scrape_ramilevi():
    """Scrape Rami Levi stores from their API"""
    stores = []

    try:
        # Rami Levi uses publishedprices.co.il
        url = 'https://url.retail.publishedprices.co.il/file/json/dir'
        response = requests.get(url, timeout=30)
        data = response.json()

        # Find stores file
        for f in data:
            if 'Stores' in f.get('name', ''):
                file_url = f'https://url.retail.publishedprices.co.il/file/d/{f["name"]}'
                response = requests.get(file_url, timeout=30)

                with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
                    content = gz.read().decode('utf-8')

                root = ET.fromstring(content)
                for store in root.findall('.//STORE') or root.findall('.//Store'):
                    store_data = {
                        'chain': 'rami_levy',
                        'chain_name': 'רמי לוי',
                        'subchain': store.findtext('SUBCHAINNAME', '') or store.findtext('SubChainName', ''),
                        'store_id': store.findtext('STOREID', '') or store.findtext('StoreId', ''),
                        'name': store.findtext('STORENAME', '') or store.findtext('StoreName', ''),
                        'address': store.findtext('ADDRESS', '') or store.findtext('Address', ''),
                        'city': store.findtext('CITY', '') or store.findtext('City', ''),
                        'zipcode': store.findtext('ZIPCODE', '') or store.findtext('ZipCode', ''),
                        'lat': None,
                        'lon': None
                    }
                    stores.append(store_data)
                break
    except Exception as e:
        print(f"Rami Levi error: {e}")

    print(f"Rami Levi: {len(stores)} stores")
    return stores

def main():
    all_stores = []

    print("Scraping stores from supermarket chains...")
    print("=" * 50)

    # Scrape each chain
    all_stores.extend(scrape_shufersal())
    all_stores.extend(scrape_kingstore())
    all_stores.extend(scrape_ramilevi())

    print("=" * 50)
    print(f"Total: {len(all_stores)} stores")

    # Add some sample coordinates (geocoding all would take too long)
    print("\nAdding sample coordinates...")
    sample_cities = {
        'תל אביב': (32.0853, 34.7818),
        'ירושלים': (31.7683, 35.2137),
        'חיפה': (32.7940, 34.9896),
        'באר שבע': (31.2530, 34.7915),
        'נתניה': (32.3286, 34.8572),
        'ראשון לציון': (31.9730, 34.7925),
        'פתח תקווה': (32.0841, 34.8878),
        'אשדוד': (31.8044, 34.6553),
        'רמת גן': (32.0833, 34.8147),
        'גבעתיים': (32.0700, 34.8100),
        'הרצליה': (32.1656, 34.8467),
        'רעננה': (32.1836, 34.8708),
        'כפר סבא': (32.1780, 34.9065),
        'הוד השרון': (32.1500, 34.8917),
        'בני ברק': (32.0833, 34.8333),
        'חולון': (32.0158, 34.7789),
        'בת ים': (32.0231, 34.7518),
    }

    for store in all_stores:
        city = store['city'].strip()
        if city in sample_cities:
            store['lat'], store['lon'] = sample_cities[city]

    # Save to JSON
    with open('stores_db.json', 'w', encoding='utf-8') as f:
        json.dump(all_stores, f, ensure_ascii=False, indent=2)

    print(f"Saved to stores_db.json")

    # Show sample
    print("\nSample stores:")
    for store in all_stores[:10]:
        print(f"  {store['chain_name']} - {store['name']} ({store['city']})")

if __name__ == "__main__":
    main()
