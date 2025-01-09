import requests
import pandas as pd
import json
import time
import os
import csv
import base64
from data_scraper.scrapper import BusinessScraper
from base.webdriver_base import WebDriverBase

class ZohoCRMClient(WebDriverBase):
    def __init__(self, config_path='config.json'):
        # super().__init__()
        self.config = self.load_config(config_path)
        self.base_url = f"{self.config['api_domain']}/crm/v2"
        self.headers = {
            "Authorization": f"Zoho-oauthtoken {self.config['access_token']}"
        }
        self.scraper = BusinessScraper()

    def load_config(self, config_path):
        with open(config_path, 'r') as config_file:
            return json.load(config_file)

    def refresh_access_token(self):
        url = "https://accounts.zoho.com/oauth/v2/token"
        params = {
            "refresh_token": self.config['refresh_token'],
            "client_id": self.config['client_id'],
            "client_secret": self.config['client_secret'],
            "grant_type": "refresh_token"
        }
        response = requests.post(url, params=params)
        if response.status_code == 200:
            new_tokens = response.json()
            self.update_access_token(new_tokens['access_token'])
        else:
            print("Failed to refresh access token:", response.json())

    def update_access_token(self, new_access_token):
        self.config['access_token'] = new_access_token
        self.headers["Authorization"] = f"Zoho-oauthtoken {new_access_token}"
        with open('config.json', 'w') as config_file:
            json.dump(self.config, config_file)
            
    def get_account_id(self, record_id):
        url = f"{self.base_url}/Accounts/{record_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()['data'][0]["details"]['id']
        else:
            return None

    def create_account(self, data):
        url = f"{self.base_url}/Accounts"
        # Add content type header for file upload
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"
        
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 401:
            self.refresh_access_token()
            headers["Authorization"] = self.headers["Authorization"]
            response = requests.post(url, headers=headers, json=data)

        if response.status_code == 201:
            print("Data added successfully!")
            return response.json()['data'][0]["details"]['id']
        else:
            print("Failed to add data. Status code:", response.status_code)
            print("Response:", response.json())
            return None

    def encode_image_to_base64(self, image_path):
        if not image_path or image_path.strip() == '':
            return None
            
        if os.path.exists(image_path):
            with open(image_path, "rb") as image_file:
                # Add proper data URI prefix for images
                file_ext = os.path.splitext(image_path)[1].lower()
                mime_type = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.gif': 'image/gif'
                }.get(file_ext, 'application/octet-stream')
                
                base64_data = base64.b64encode(image_file.read()).decode("utf-8")
                return f"data:{mime_type};base64,{base64_data}"
        else:
            print(f"Warning: File {image_path} not found. Skipping this file.")
            return None

    def upload_photo(self, module_name, record_id, image_path):
        if not image_path or not os.path.exists(image_path):
            return False
            
        url = f"{self.base_url}/{module_name}/{record_id}/photo"
        headers = self.headers.copy()
        # Remove Content-Type as it will be set automatically for multipart/form-data
        if "Content-Type" in headers:
            del headers["Content-Type"]
            
        try:
            with open(image_path, 'rb') as image_file:
                files = {'file': (os.path.basename(image_path), image_file)}
                response = requests.post(url, headers=headers, files=files)
                
                if response.status_code == 401:
                    self.refresh_access_token()
                    headers["Authorization"] = self.headers["Authorization"]
                    response = requests.post(url, headers=headers, files=files)
                
                if response.status_code == 200:
                    print(f"Photo uploaded successfully for record {record_id}")
                    return True
                else:
                    print(f"Failed to upload photo. Status code: {response.status_code}")
                    print("Response:", response.json())
                    return False
        except Exception as e:
            print(f"Error uploading photo: {str(e)}")
            return False

    def update_account_images(self, record_id, field_name, image_data):
        url = f"{self.base_url}/Accounts/{record_id}"
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"

        update_data = {
            "data": [
                {
                    field_name: image_data
                }
            ]
        }

        response = requests.put(url, headers=headers, json=update_data)
        if response.status_code == 401:
            self.refresh_access_token()
            headers["Authorization"] = self.headers["Authorization"]
            response = requests.put(url, headers=headers, json=update_data)

        if response.status_code == 200:
            print(f"Images for account {record_id} updated successfully!")
        else:
            print(f"Failed to update images for account {record_id}. Status code:", response.status_code)
            print("Response:", response.json())

    def monitor_csv_and_update_crm(self, csv_file_path):
        while True:
            with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
                csvreader = csv.DictReader(csvfile)
                for row in csvreader:
                    data = {
                        "data": [
                            {
                                "Account_Name": row['Name'],
                                "Website": row['Website'],
                                "Number": row['Phone'],
                                "Billing_Street": 'Billing_Street',
                                "Billing_City": 'Billing_City',
                                "Billing_State": 'Billing_State',
                                "Billing_Code": 'Billing_Code',
                                "Billing_Country": 'Billing_Country',
                                "Images": row['Images'],
                                "Address": row['Address']
                            }
                        ]
                    }
                    record_id = self.create_account(data)
                    account_details = self.get_account_details(record_id)
                    print(account_details)

                    layout_id = account_details['$layout_id']['id']
                    business_name = row['Name'].replace(" ", "_")
                    image_paths = [
                        f'images/{business_name}/image_{i}.jpg' for i in range(3)
                    ]

                    self.scraper.update_images_in_zoho(record_id, layout_id, image_paths)
            time.sleep(10)

    def get_field_metadata(self):
        url = f"{self.base_url}/settings/fields?module=Accounts"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 401:
            self.refresh_access_token()
            response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            fields = response.json()['fields']
            for field in fields:
                print(f"Field Name: {field['field_label']}")
                print(f"API Name: {field['api_name']}")
                print("---")
        else:
            print("Failed to fetch fields:", response.json())

    def get_account_details(self, record_id):
        url = f"{self.base_url}/Accounts/{record_id}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 401:
            self.refresh_access_token()
            response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            account_data = response.json()['data'][0]
            print("Account Details:")
            print(json.dumps(account_data, indent=4))
            return account_data
        else:
            print("Failed to fetch account details. Status code:", response.status_code)
            print("Response:", response.json())
            return None

    def fetch_and_process_accounts(self):
        url = f"{self.base_url}/Accounts"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 401:
            self.refresh_access_token()
            response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            accounts = response.json()['data']
            processed_addresses = self.scraper.load_processed_addresses()

            for account in accounts:
                address = account.get('Address')
                if address and address not in processed_addresses:
                    print(f"Processing new address: {address}")
                    business_data = self.scraper.scrape_business_info([address])
                    if business_data:
                        self.update_account(account['id'], account['$layout_id']['id'], business_data[0])
                        self.scraper.save_processed_address(address)
                else:
                    print(f"Skipping already processed address: {address}")

        else:
            print("Failed to fetch accounts. Status code:", response.status_code)
            print("Response:", response.json())

    def update_account(self, record_id, layout_id, data):
        url = f"{self.base_url}/Accounts/{record_id}"
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"

        update_data = {
            "data": [
                {
                    "Account_Name": data['Name'],
                    "Website": data['Website'],
                    "Number": data['Phone'],
                    "Address": data['Address']
                }
            ]
        }

        response = requests.put(url, headers=headers, json=update_data)
        if response.status_code == 401:
            self.refresh_access_token()
            headers["Authorization"] = self.headers["Authorization"]
            response = requests.put(url, headers=headers, json=update_data)

        if response.status_code == 200:
            print(f"Account {record_id} updated successfully!")

            business_name = data['Name'].replace(" ", "_")
            image_paths = [
                f'images/{business_name}/image_{i}.jpg' for i in range(3)
            ]

            self.scraper.update_images_in_zoho(record_id, layout_id, image_paths)
        else:
            print(f"Failed to update account {record_id}. Status code:", response.status_code)
            print("Response:", response.json())

    def upload_images_to_account(self, record_id, image_paths):
        for image_path in image_paths:
            if os.path.exists(image_path):
                encoded_image = self.encode_image_to_base64(image_path)
                if encoded_image:
                    # Assuming there's a method to update images in Zoho
                    self.update_account_images(record_id, 'Images', encoded_image)