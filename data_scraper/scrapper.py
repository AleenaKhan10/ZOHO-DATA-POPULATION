from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import csv
import requests
import os
from base.webdriver_base import WebDriverBase
import base64

class BusinessScraper(WebDriverBase):
    def __init__(self):
        super().__init__()
        self.processed_file = 'processed_addresses.csv'

    def scrape_business_info(self, addresses):
        processed_addresses = self.load_processed_addresses()
        business_data = []

        for address in addresses:
            if address in processed_addresses:
                print(f"Skipping already processed address: {address}")
                continue

            self.driver.get("https://www.google.com")
            search_box = self.wait_for_element(By.NAME, "q")
            if search_box:
                search_box.clear()
                search_box.send_keys(address)
                search_box.send_keys(Keys.RETURN)

            time.sleep(3)  # Wait for the page to load

            try:
                # Extract business information
                name = self._get_element_text("//div[@data-attrid='title']")
                website = self._get_element_attribute("//a[.//span[text()='Website']]", "href")
                phone = self._get_element_attribute("//a[@data-phone-number]", "data-phone-number")
                image_urls = self._get_image_urls()

                self.download_images(image_urls, name)

                business_data.append({
                    "Name": name,
                    "Website": website,
                    "Phone": phone,
                    "Images": image_urls,
                    "Address": address
                })

                # Mark address as processed
                self.save_processed_address(address)

            except Exception as e:
                print(f"Error extracting data for {address}: {e}")

        return business_data

    def _get_element_text(self, xpath):
        try:
            return self.driver.find_element(By.XPATH, xpath).text
        except:
            return None

    def _get_element_attribute(self, xpath, attribute):
        try:
            return self.driver.find_element(By.XPATH, xpath).get_attribute(attribute)
        except:
            return None

    def _get_image_urls(self):
        image_urls = []
        try:
            image_element1 = self.driver.find_element(By.XPATH, "//div[@id='media_result_group']//span[text()='See photos']/preceding-sibling::g-img//img")
            image_urls.append(image_element1.get_attribute('src') if image_element1 else None)
        except:
            image_urls.append(None)

        try:
            image_element2 = self.driver.find_element(By.XPATH, "//div[@id='media_result_group']//img[contains(@alt, 'Map of')]")
            image_urls.append(image_element2.get_attribute('src') if image_element2 else None)
        except:
            image_urls.append(None)

        try:
            image_element3 = self.driver.find_element(By.XPATH, "//div[@id='media_result_group']//span[text()='See outside']/preceding-sibling::g-img//img")
            image_urls.append(image_element3.get_attribute('src') if image_element3 else None)
        except:
            image_urls.append(None)

        return image_urls

    def download_images(self, image_urls, business_name):
        business_name = business_name.replace(" ", "_")
        image_folder = os.path.join('images', business_name)
        os.makedirs(image_folder, exist_ok=True)

        for i, url in enumerate(image_urls):
            if url:
                if url.startswith('data:image'):
                    header, encoded = url.split(',', 1)
                    data = base64.b64decode(encoded)
                    with open(os.path.join(image_folder, f"image_{i}.jpg"), 'wb') as file:
                        file.write(data)
                else:
                    response = requests.get(url)
                    if response.status_code == 200:
                        with open(os.path.join(image_folder, f"image_{i}.jpg"), 'wb') as file:
                            file.write(response.content)

    def save_to_csv(self, data, filename='business_data.csv'):
        keys = data[0].keys()
        with open(filename, 'w', newline='', encoding='utf-8') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)

    def update_images_in_zoho(self, record_id, layout_id, image_paths):
        url = f"https://crm.zoho.com/crm/org875401012/tab/Accounts/{record_id}/edit?layoutId={layout_id}"
        self.driver.get(url)
        time.sleep(10)

        try:
            for i, image_path in enumerate(image_paths, start=1):
                absolute_image_path = os.path.abspath(image_path)
                if os.path.exists(absolute_image_path):
                    if not self.click_element(By.XPATH, f"//lyte-button[@data-zcqa='Image Upload {i}']"):
                        self.click_element(By.XPATH, f"//crux-image-component")
                        time.sleep(2)
                        self.click_element(By.XPATH, f"//lyte-button[@data-zcqa='Image Upload {i}']")
                    time.sleep(2)
                    file_input = self.wait_for_element(By.XPATH, "//input[@type='file']")
                    if file_input:
                        file_input.send_keys(absolute_image_path)
                        time.sleep(10)
                        self.click_element(By.XPATH, "//button[.//text()='Attach']")
                        time.sleep(2)

            self.click_element(By.XPATH, "//button[.//text()='Save']")
            time.sleep(3)

        except Exception as e:
            print(f"Error updating images: {e}")

    def load_processed_addresses(self):
        if not os.path.exists(self.processed_file):
            return set()

        with open(self.processed_file, 'r', newline='', encoding='utf-8') as file:
            return set(line.strip() for line in file)

    def save_processed_address(self, address):
        with open(self.processed_file, 'a', newline='', encoding='utf-8') as file:
            file.write(f"{address}\n")
