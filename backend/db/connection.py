import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from the backend/.env file
load_dotenv(dotenv_path="backend/.env")

# Fetch credentials from the environment
URL: str = os.getenv("SUPABASE_URL")
KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not URL or not KEY:
    raise ValueError("❌ Missing Credentials: Check your backend/.env file.")

# Initialize the Supabase client
# Using the Service Role Key allows the backend to bypass RLS policies
supabase: Client = create_client(URL, KEY)

def test_connection():
    print("Initiating database connection test...")
    try:
        # Attempt to fetch the top 1 row from the container_health table
        response = supabase.table("container_health").select("*").limit(1).execute()
        print("✅ SUCCESS: Aegis Backend is securely connected to Supabase!")
        print(f"📡 Current data payload: {response.data}")
    except Exception as e:
        print(f"❌ CONNECTION FAILED: {e}")

if __name__ == "__main__":
    test_connection()