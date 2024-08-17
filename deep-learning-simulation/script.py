import requests
import time
import random
import os
from dotenv import load_dotenv
import jwt

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = "http://localhost:8080"  # Adjust this to your API's URL
OAUTH_PROVIDER = "google"  # or "github"
CLIENT_ID = os.getenv(f"{OAUTH_PROVIDER.upper()}_OAUTH_CLIENT_ID")
CLIENT_SECRET = os.getenv(f"{OAUTH_PROVIDER.upper()}_OAUTH_CLIENT_SECRET")
REDIRECT_URI = os.getenv(f"{OAUTH_PROVIDER.upper()}_OAUTH_REDIRECT_URI")

headers = {
    "Content-Type": "application/json"
}

def get_auth_code():
    """
    In a real scenario, this would involve redirecting the user to the OAuth provider's login page
    and capturing the returned authorization code. For this simulation, we'll assume you have
    obtained this code manually and stored it in an environment variable.
    """
    return os.getenv("AUTH_CODE")

def authenticate():
    """Authenticate with the API using OAuth2."""
    auth_code = get_auth_code()
    if not auth_code:
        raise Exception("No authorization code found. Please set the AUTH_CODE environment variable.")

    response = requests.post(
        f"{API_BASE_URL}/api/auth/{OAUTH_PROVIDER}",
        json={"code": auth_code},
        headers=headers
    )

    if response.status_code == 200:
        return response.json()["session_token"]
    else:
        raise Exception(f"Authentication failed: {response.text}")
    
def get_session_code():
    """
    Use this method to get the session token without the need to authenticate.
    """
    return os.getenv("SESSION_TOKEN")

def refresh_token_if_needed(session_token):
    """Check if the token is expired and refresh if necessary."""
    try:
        # Decode the token without verification to check expiration
        decoded = jwt.decode(session_token, options={"verify_signature": False})
        print(decoded)
        exp = decoded.get('exp', 0)
        if exp < time.time():
            print("Token expired. Re-authenticating...")
            return authenticate()
        return session_token
    except jwt.DecodeError:
        print("Invalid token. Re-authenticating...")
        return authenticate()

def simulate_deep_learning_process(query):
    """Simulate a deep learning process."""
    time.sleep(random.uniform(1, 5))  # Simulate processing time
    return f"Processed result for query: {query}"

def fetch_request(session_token):
    """Fetch a request from the API."""
    headers["Authorization"] = f"Bearer {session_token}"
    response = requests.get(f"{API_BASE_URL}/fetch-requests", headers=headers)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        print("No requests in queue.")
        return None
    else:
        print(f"Error fetching request: {response.status_code}")
        return None

def submit_result(session_token, request_id, result):
    """Submit the processed result back to the API."""
    headers["Authorization"] = f"Bearer {session_token}"
    data = {
        "request_id": request_id,
        "result": result
    }
    response = requests.post(f"{API_BASE_URL}/submit-result", json=data, headers=headers)
    if response.status_code == 200:
        print(f"Result submitted successfully for request {request_id}")
    else:
        print(f"Error submitting result: {response.status_code}")

def main():
    print("Deep Learning Server Simulation Started")
    session_token = get_session_code()
    
    while True:
        session_token = refresh_token_if_needed(session_token)
        request = fetch_request(session_token)
        if request:
            print(f"Processing request {request['request_id']}: {request['query']}")
            result = simulate_deep_learning_process(request['query'])
            submit_result(session_token, request['request_id'], result)
        else:
            print("No requests to process. Waiting...")
        time.sleep(5)  # Wait for 5 seconds before next fetch

if __name__ == "__main__":
    main()