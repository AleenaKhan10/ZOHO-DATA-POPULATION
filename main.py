import time
from crm_integration.crm_client import ZohoCRMClient


def main():
    crm_client = ZohoCRMClient()
    while True:
        crm_client.fetch_and_process_accounts()
        time.sleep(30)

if __name__ == "__main__":
    main()  