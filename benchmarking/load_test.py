import requests
import random

import time
import concurrent.futures
import statistics
import random
from colorama import init, Fore, Style
from tqdm import tqdm

# Initialize colorama
init(autoreset=True)

# API base URL
BASE_URL = "http://localhost:8080"  # Adjust this to your API's URL

# Test parameters
MAX_CONCURRENT = 50  # Maximum number of concurrent requests

# Endpoints to test
ENDPOINTS = [
    ("/submit-request", "POST", {"query": "Test query"}),
    ("/fetch-requests", "GET", None),
    ("/submit-result", "POST", {"request_id": 1, "result": "Test result"}),
    ("/get-result/1", "GET", None)
]

def get_session_token():
    # You can return the session token retrieved from the auth flow of github or google
    return "session_token"

def make_request(endpoint, method, data):
    url = f"{BASE_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {get_session_token()}"}
    
    start_time = time.time()
    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        response = requests.post(url, json=data, headers=headers)
    
    end_time = time.time()
    return response.status_code, end_time - start_time

def test_endpoint(endpoint, method, data, duration):
    start_time = time.time()
    request_count = 0
    success_count = 0
    response_times = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as executor:
        future_to_request = {}
        with tqdm(total=duration, desc=f"{method} {endpoint}", unit="s", bar_format="{l_bar}{bar}| {n:.1f}/{total:.1f}s") as pbar:
            while time.time() - start_time < duration:
                # Submit new requests
                while len(future_to_request) < MAX_CONCURRENT:
                    future = executor.submit(make_request, endpoint, method, data)
                    future_to_request[future] = time.time()
                
                # Check for completed requests
                done, _ = concurrent.futures.wait(future_to_request, timeout=0.1, return_when=concurrent.futures.FIRST_COMPLETED)
                
                for future in done:
                    status_code, response_time = future.result()
                    request_count += 1
                    response_times.append(response_time)
                    if 200 <= status_code < 300:
                        success_count += 1
                    del future_to_request[future]

                pbar.update(time.time() - start_time - pbar.n)

            # Wait for any remaining requests to complete
            for future in concurrent.futures.as_completed(future_to_request):
                status_code, response_time = future.result()
                request_count += 1
                response_times.append(response_time)
                if 200 <= status_code < 300:
                    success_count += 1

    avg_response_time = statistics.mean(response_times) if response_times else 0
    max_response_time = max(response_times) if response_times else 0
    min_response_time = min(response_times) if response_times else 0
    success_rate = (success_count / request_count) * 100 if request_count > 0 else 0
    
    return {
        "endpoint": endpoint,
        "method": method,
        "requests_completed": request_count,
        "avg_response_time": avg_response_time,
        "max_response_time": max_response_time,
        "min_response_time": min_response_time,
        "success_rate": success_rate
    }


def run_random_test(duration):
    start_time = time.time()
    results = {endpoint: {"requests": 0, "successes": 0, "response_times": []} for endpoint, _, _ in ENDPOINTS}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as executor:
        future_to_endpoint = {}
        with tqdm(total=duration, desc="Random Testing", unit="s", bar_format="{l_bar}{bar}| {n:.1f}/{total:.1f}s") as pbar:
            while time.time() - start_time < duration:
                # Submit new requests
                while len(future_to_endpoint) < MAX_CONCURRENT:
                    endpoint, method, data = random.choice(ENDPOINTS)
                    future = executor.submit(make_request, endpoint, method, data)
                    future_to_endpoint[future] = endpoint
                
                # Check for completed requests
                done, _ = concurrent.futures.wait(future_to_endpoint, timeout=0.1, return_when=concurrent.futures.FIRST_COMPLETED)
                
                for future in done:
                    endpoint = future_to_endpoint[future]
                    status_code, response_time = future.result()
                    results[endpoint]["requests"] += 1
                    results[endpoint]["response_times"].append(response_time)
                    if 200 <= status_code < 300:
                        results[endpoint]["successes"] += 1
                    del future_to_endpoint[future]

                pbar.update(time.time() - start_time - pbar.n)

            # Wait for any remaining requests to complete
            for future in concurrent.futures.as_completed(future_to_endpoint):
                endpoint = future_to_endpoint[future]
                status_code, response_time = future.result()
                results[endpoint]["requests"] += 1
                results[endpoint]["response_times"].append(response_time)
                if 200 <= status_code < 300:
                    results[endpoint]["successes"] += 1

    return results

def run_load_test(duration, random_testing=False):
    print(f"{Fore.CYAN}Starting load test for {duration} seconds with max {MAX_CONCURRENT} concurrent requests{Style.RESET_ALL}")
    
    if random_testing:
        results = run_random_test(duration)
        for endpoint, result in results.items():
            method = next(m for e, m, _ in ENDPOINTS if e == endpoint)
            avg_response_time = statistics.mean(result["response_times"]) if result["response_times"] else 0
            max_response_time = max(result["response_times"]) if result["response_times"] else 0
            min_response_time = min(result["response_times"]) if result["response_times"] else 0
            success_rate = (result["successes"] / result["requests"]) * 100 if result["requests"] > 0 else 0
            
            print(f"\n{Fore.YELLOW}Results for {method} {endpoint}:{Style.RESET_ALL}")
            print(f"{Fore.GREEN}Requests completed: {result['requests']}{Style.RESET_ALL}")
            print(f"Average Response Time: {Fore.MAGENTA}{avg_response_time:.4f}{Style.RESET_ALL} seconds")
            print(f"Max Response Time: {Fore.MAGENTA}{max_response_time:.4f}{Style.RESET_ALL} seconds")
            print(f"Min Response Time: {Fore.MAGENTA}{min_response_time:.4f}{Style.RESET_ALL} seconds")
            print(f"Success Rate: {Fore.BLUE}{success_rate:.2f}%{Style.RESET_ALL}")
    else:
        for endpoint, method, data in ENDPOINTS:
            print(f"\n{Fore.YELLOW}Testing {method} {endpoint}{Style.RESET_ALL}")
            result = test_endpoint(endpoint, method, data, duration)
            print_results(result, duration)


def print_results(result, duration):
    print(f"{Fore.GREEN}Requests completed in {duration} seconds: {result['requests_completed']}{Style.RESET_ALL}")
    print(f"Average Response Time: {Fore.MAGENTA}{result['avg_response_time']:.4f}{Style.RESET_ALL} seconds")
    print(f"Max Response Time: {Fore.MAGENTA}{result['max_response_time']:.4f}{Style.RESET_ALL} seconds")
    print(f"Min Response Time: {Fore.MAGENTA}{result['min_response_time']:.4f}{Style.RESET_ALL} seconds")
    print(f"Success Rate: {Fore.BLUE}{result['success_rate']:.2f}%{Style.RESET_ALL}")
    
if __name__ == "__main__":
    while True:
        try:
            duration = int(input("Enter the duration of the test in seconds: "))
            if duration <= 0:
                raise ValueError
            break
        except ValueError:
            print("Please enter a positive integer for the duration.")

    while True:
        testing_mode = input("Do you want random endpoint testing? (y/n): ").lower()
        if testing_mode in ['y', 'n']:
            break
        print("Please enter 'y' for yes or 'n' for no.")

    random_testing = testing_mode == 'y'

    run_load_test(duration, random_testing)