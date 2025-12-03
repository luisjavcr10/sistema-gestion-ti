import requests
import sys
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8000")

def check_health():
    print(f"Checking system health at {GATEWAY_URL}...")
    try:
        response = requests.get(f"{GATEWAY_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ API Gateway is UP")
            
            services = data.get("services", {})
            all_healthy = True
            
            for name, status in services.items():
                icon = "✅" if status == "up" else "❌"
                print(f"{icon} Service {name}: {status.upper()}")
                if status != "up":
                    all_healthy = False
            
            if all_healthy:
                print("\nSystem is fully operational.")
                sys.exit(0)
            else:
                print("\nSome services are down.")
                sys.exit(1)
        else:
            print(f"❌ API Gateway returned status {response.status_code}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API Gateway. Is it running?")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_health()
