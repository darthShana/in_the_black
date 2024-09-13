import json
from tempfile import mkdtemp

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


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

    return driver


# Keep the extract_number function as is
def extract_number(text: str) -> int:
    return int(''.join(char for char in text if char.isdigit()))


def handler(event, context):
    body = json.loads(event['body'])
    address = body.get('address', '')

    if not address:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Address not provided'})
        }

    driver = initialise_driver()

    try:
        driver.get('https://www.qv.co.nz/property-search/#')

        # Wait for the input field to be present
        input_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'c-address_search__field'))
        )

        # Enter text into the input field
        input_field.send_keys(address)

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

            driver.quit()

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'address': address,
                    'estimated_value': extract_number(estimate_text)
                })
            }

        else:
            print("No autofill options found")
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'No results found for the given address'})
            }
    finally:
        driver.quit()


if __name__ == '__main__':
    handler({}, None)
