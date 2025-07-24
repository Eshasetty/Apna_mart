import os
from dotenv import load_dotenv

def main():
    # Load .env file
    load_dotenv()
    
    # List the variables you want to check
    keys = [
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "CLEVERTAP_JOURNEY_COOKIE",
        "CLEVERTAP_JOURNEY_DETAILS_COOKIE",
        "CLEVERTAP_JOURNEY_TOKEN"
    ]
    
    for key in keys:
        value = os.getenv(key)
        if value:
            print(f"{key}: {value[:6]}... (length: {len(value)})")
        else:
            print(f"{key}: NOT FOUND")

if __name__ == "__main__":
    main()