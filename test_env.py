from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# List of required environment variables
required_vars = [
    'CLEVERTAP_CSRF_TOKEN',
    'CLEVERTAP_COOKIE',
    'CLEVERTAP_DETAIL_CSRF_TOKEN',
    'CLEVERTAP_DETAIL_COOKIE',
    'SUPABASE_URL',
    'SUPABASE_KEY',
    'OPENAI_API_KEY',
]

print("Testing .env variable loading:\n")
all_ok = True
for var in required_vars:
    value = os.getenv(var)
    if value:
        print(f"{var}: [LOADED] {value[:6]}... (length: {len(value)})")
    else:
        print(f"{var}: [MISSING]")
        all_ok = False

if all_ok:
    print("\nAll required environment variables are loaded correctly!")
else:
    print("\nSome required environment variables are missing. Please check your .env file.") 