from zohocrmsdk import ZCRMModule, ZCRMRecord, ZCRMRestClient
import os

def create_account_with_images(account_data, image_paths):
    # Initialize the SDK
    initialize_sdk()

    # Get the module instance
    module_instance = ZCRMModule.get_instance('Accounts')

    # Create a new record
    record = ZCRMRecord.get_instance('Accounts')
    record.set_field_value('Account_Name', account_data['Account_Name'])
    record.set_field_value('Website', account_data['Website'])
    record.set_field_value('Phone', account_data['Phone'])
    record.set_field_value('Billing_Street', account_data['Billing_Street'])
    record.set_field_value('Billing_City', account_data['Billing_City'])
    record.set_field_value('Billing_State', account_data['Billing_State'])
    record.set_field_value('Billing_Code', account_data['Billing_Code'])
    record.set_field_value('Billing_Country', account_data['Billing_Country'])

    # Add images as attachments
    for image_path in image_paths:
        if os.path.exists(image_path):
            record.add_attachment(image_path)

    # Create the record in Zoho CRM
    response = module_instance.create_records([record])
    if response.status_code == 201:
        print("Account created successfully with images!")
    else:
        print("Failed to create account. Status code:", response.status_code)
        print("Response:", response.response_json)

# Example usage
account_data = {
    "Account_Name": "Example Account",
    "Website": "https://example.com",
    "Phone": "1234567890",
    "Billing_Street": "123 Example St",
    "Billing_City": "Example City",
    "Billing_State": "Example State",
    "Billing_Code": "123456",
    "Billing_Country": "Example Country"
}

image_paths = [
    "path/to/image1.jpg",
    "path/to/image2.jpg"
]

create_account_with_images(account_data, image_paths) 