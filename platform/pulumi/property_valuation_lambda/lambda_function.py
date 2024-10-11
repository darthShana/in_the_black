import json
from datetime import datetime, timedelta
from decimal import Decimal
from tempfile import mkdtemp

import boto3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('PropertyValuesCache')


def initialise_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-tools")
    chrome_options.add_argument("--no-zygote")
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument(f"--user-data-dir={mkdtemp()}")
    chrome_options.add_argument(f"--data-path={mkdtemp()}")
    chrome_options.add_argument(f"--disk-cache-dir={mkdtemp()}")
    chrome_options.add_argument("--remote-debugging-pipe")
    chrome_options.add_argument("--verbose")
    chrome_options.add_argument("--log-path=/tmp")
    chrome_options.binary_location = "/opt/chrome/chrome-linux64/chrome"

    service = Service(
        executable_path="/opt/chrome-driver/chromedriver-linux64/chromedriver",
        service_log_path="/tmp/chromedriver.log"
    )

    driver = webdriver.Chrome(
        service=service,
        options=chrome_options
    )
    # driver = webdriver.Chrome()

    return driver


# Keep the extract_number function as is
def extract_number(text: str) -> int:
    return int(''.join(char for char in text if char.isdigit()))


def handler(event, context):
    body = json.loads(event['body'])
    address1 = body.get('address1', '')
    suburb = body.get('suburb', '')
    city = body.get('city', '')
    property_type = body.get('property_type', '')
    bedrooms = body.get('bedrooms', '')

    if not address1 or not suburb or not city or not bedrooms or not property_type:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Address not provided'})
        }

    # Create a unique key for the cache
    cache_key = f"{address1}|{suburb}|{city}|{property_type}|{bedrooms}"

    # Try to get the cached value
    cached_value = get_cached_value(cache_key)
    print(cached_value)
    if cached_value:
        return {
            'statusCode': 200,
            'body': json.dumps(cached_value)
        }

    driver = initialise_driver()

    try:
        estimated_value = get_property_value(address1, driver)
        market_rental = get_rental_income(suburb, city, bedrooms, property_type, driver)
        store_in_cache(cache_key, {
            'address': address1,
            'estimated_value': estimated_value,
            'market_rental': market_rental,
            'source': 'cache'
        })

        return {
            'statusCode': 200,
            'body': json.dumps({
                'address': address1,
                'estimated_value': estimated_value,
                'market_rental': market_rental,
                'source': 'calculation'
            })
        }
    except Exception as e:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': e})
        }
    finally:
        driver.quit()


def get_rental_income(suburb, city, bedrooms, property_type, driver):

    rental_request = f"https://www.tenancy.govt.nz/rent-bond-and-bills/market-rent/?location={city}+-+{suburb.replace(' ', '+')}&period=17&action_doSearchValues=Find+Rent"
    driver.get(rental_request)

    # Wait for the table to be present
    table = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, f"//table[@class='css-table-tuck'][.//h5[text()='{property_type}']]"))
    )

    # Find the row for 3 bedrooms
    rows = table.find_elements(By.TAG_NAME, "tr")
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        if len(cells) > 0 and cells[0].text == f"{bedrooms} bedrooms":
            # The Median Rent is in the 4th column (index 3)
            median_rent = cells[3].text
            print(f"The Median Rent for the house is: {median_rent}")
            return extract_number(median_rent)
    else:
        print("bedroom house data not found in the table.")
        raise Exception('No rental results found for the given address')


def get_property_value(address1, driver):

    driver.get('https://www.qv.co.nz/property-search/#')
    # Wait for the input field to be present
    input_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'c-address_search__field'))
    )
    # Enter text into the input field
    input_field.send_keys(address1)
    # Wait for autofill options to appear
    autofill_container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'c-address_search__results'))  # Replace with the actual class of the container holding the autofill options
    )
    # Find all autofill options within the container
    autofill_options = autofill_container.find_elements(By.CLASS_NAME, 'c-address_search__result_item')
    # Select the first autofill option if any exist
    if autofill_options:
        autofill_options[0].click()

        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "c-property_estimate__est"))
        )

        # Find the div with the specified class
        estimate_div = driver.find_element(By.CLASS_NAME, "c-property_estimate__est")

        # Get the text from the div
        estimate_text = estimate_div.text
        print("Estimated:", estimate_text)
        return extract_number(estimate_text)

    else:
        print("No autofill options found")
        raise Exception('No autofill options found for the given address')


def get_cached_value(cache_key):
    try:
        response = table.get_item(Key={'cache_key': cache_key})
        item = response.get('Item')
        if item:
            timestamp = datetime.fromisoformat(item['timestamp'])
            if datetime.now() - timestamp < timedelta(weeks=1):
                # Convert the values using DecimalEncoder
                return json.loads(json.dumps(item['values'], cls=DecimalEncoder))
    except Exception as e:
        print(f"Error retrieving from cache: {str(e)}")
    return None


def store_in_cache(cache_key, values):
    try:
        table.put_item(
            Item={
                'cache_key': cache_key,
                'values': values,
                'timestamp': datetime.now().isoformat()
            }
        )
    except Exception as e:
        print(f"Error storing in cache: {str(e)}")


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


if __name__ == '__main__':
    result = handler(
        {
            'body': json.dumps(
                {
                    'address1': '54b Tawa Road',
                    'suburb': 'One Tree Hill',
                    'city': 'Auckland',
                    'property_type': 'House',
                    'bedrooms': 3
                 }
            )
        }, None)
    print(result)

