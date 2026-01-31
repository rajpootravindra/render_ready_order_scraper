
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from selenium.common.exceptions import StaleElementReferenceException
# import requests
import os
import json

def setup_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials_dict = json.loads(os.environ["GOOGLE_SHEET_CREDS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)

    client = gspread.authorize(creds)
    sheet = client.open("February2026").sheet1
    return sheet

def get_existing_orders(sheet):
    try:
        data = sheet.get_all_records()
        existing_orders = {row['Order Id'] for row in data}
        return existing_orders
    except Exception as e:
        print(f"Error fetching existing orders: {e}")
        return set()

def login_to_website(driver):
    driver.get("https://admin.foodzoid.in/")
    wait = WebDriverWait(driver, 20)
    try:
        username_input = wait.until(EC.presence_of_element_located((By.NAME, "txtUser")))
        password_input = driver.find_element(By.NAME, "txtPassword")
        login_button = driver.find_element(By.ID, "btnLogin")

        # Use environment variables
        username = os.getenv("ADMIN_USERNAME")
        password = os.getenv("ADMIN_PASSWORD")

        username_input.send_keys(username)
        password_input.send_keys(password)
        login_button.click()

        wait.until(EC.presence_of_element_located((By.ID, "kt_body")))
        driver.get("https://admin.foodzoid.in/order-history")
        wait.until(EC.presence_of_element_located((By.ID, "example_filter")))
    except Exception as e:
        print(f"Error during login or navigation: {e}")
        raise

def scrape_orders_for_date(driver, target_date):
    wait = WebDriverWait(driver, 30)
    try:
        search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#example_filter input[type='search']")))
        search_input.clear()
        search_input.send_keys(target_date)
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table tbody tr")))
    except Exception as e:
        print(f"Error locating or interacting with the search input: {e}")
        return []

    def table_is_filtered_by_date():
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) > 2 and target_date not in cols[2].text:
                return False
        return True

    try:
        wait.until(lambda driver: table_is_filtered_by_date())
    except Exception as e:
        print(f"Table did not filter correctly: {e}")
        return []

    data = []
    page_number = 1
    max_retries = 3
    sn = 1
    while True:
        try:
            print(f"Scraping page {page_number}...")
            retry_count = 0
            while retry_count < max_retries:
                try:
                    rows = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table tbody tr")))
                    for row in rows:
                        cols = row.find_elements(By.TAG_NAME, "td")
                        if len(cols) > 3 and "Order Delivered" in cols[7].text:
                            order_id = cols[0].text
                            shop_name = cols[1].text
                            date = cols[2].text.split(" ")[0]
                            delivery_boy = cols[3].text
                            net_amount = round(float(cols[4].text))
                            delivery_charge = 0 if net_amount > 499 else 30
                            
                            product_value = net_amount - delivery_charge
                            payable_amount = round(product_value * 0.85) # (17 / 20)
                            profit = round((product_value * 0.15) + delivery_charge) # (3 / 20)
                            
                            data.append([
                                sn,
                                order_id,
                                date,
                                shop_name,
                                net_amount,
                                product_value,
                                payable_amount,
                                profit,
                                delivery_boy
                            ])
                            sn += 1
                    break
                except StaleElementReferenceException:
                    print("Encountered stale element, retrying...")
                    retry_count += 1
                    continue
            if retry_count == max_retries:
                print("Exceeded maximum retries for stale elements on this page.")
                break
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, ".paginate_button.next")
                if "disabled" in next_button.get_attribute("class"):
                    break
                next_button.click()
                wait.until(EC.staleness_of(rows[0]))
                page_number += 1
            except Exception as e:
                print(f"Error with pagination: {e}")
                break
        except Exception as e:
            print(f"Error during scraping: {e}")
            break
    return data

# def send_message(new_orders_count):
#     message_text = f"  Orders Added to The Sheet {new_orders_count} ."
#     url = "http://api.foodzoid.in:8081/sendMessage"
#     payload = {
#         "TYPE": "GROUP",
#         "SenderId": "",
#         "message": {
#             "text": message_text
#         }
#     }
    # response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
    # print("Response:", response.status_code, response.text)

def append_new_orders(sheet, existing_orders, new_data):
    new_orders = [row for row in new_data if str(row[1]) not in existing_orders]
    new_orders_count = len(new_orders)
    for order in new_orders:
        sheet.append_row(order)
    print(f"{len(new_orders)} new orders added to the sheet.")
    if new_orders_count > 0:
        send_message(new_orders_count)

def log_message(msg):
    with open("log.txt", "a") as f:
        f.write(msg + "\n")

def run_order_scraper(target_date):
    sheet = setup_google_sheet()
    existing_orders = get_existing_orders(sheet)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    log_message(f"Started scraping for {target_date}...")

    try:
        login_to_website(driver)
        log_message("✅ Logged in successfully")
        new_data = scrape_orders_for_date(driver, target_date)
        log_message(f"✅ Scraped {len(new_data)} orders")

        append_new_orders(sheet, existing_orders, new_data)
        log_message("✅ Orders appended successfully")
    except Exception as e:
        log_message(f"❌ Error: {str(e)}")
    finally:
        driver.quit()

