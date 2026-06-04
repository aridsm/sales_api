import json
import urllib.request
import urllib.error
import random
import string

BASE_URL = "http://127.0.0.1:8000"

def generate_random_email():
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"user_{random_str}@example.com"

def make_request(path, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    
    url = f"{BASE_URL}{path}"
    
    req_data = None
    if data is not None:
        if headers.get("Content-Type") == "application/x-www-form-urlencoded":
            req_data = urllib.parse.urlencode(data).encode("utf-8")
        else:
            req_data = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
            
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            if response.status == 204:
                return None
            return json.loads(res_body)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"HTTP Error {e.code}: {err_body}")
        raise e

def test_sales_endpoints():
    email = generate_random_email()
    password = "testpassword"
    
    print(f"[*] Registering user: {email}")
    signup_data = {
        "name": "Test Sales User",
        "email": email,
        "password": password
    }
    signup_res = make_request("/users/signup", method="POST", data=signup_data)
    print("[+] User registered successfully.")
    
    print("[*] Logging in...")
    login_data = {
        "username": email,
        "password": password
    }
    login_res = make_request(
        "/users/login",
        method="POST",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token = login_res["access_token"]
    print("[+] Login successful. Token obtained.")
    
    auth_headers = {"Authorization": f"Bearer {token}"}
    
    print("[*] Creating Sale 1 (default status = 1 done)...")
    sale1 = make_request("/sales/", method="POST", data={}, headers=auth_headers)
    print(f"[+] Sale 1 created: ID={sale1['id']}, code={sale1['code']}, status={sale1['status']}")
    
    print("[*] Creating Sale 2 (status = 2 canceled)...")
    sale2 = make_request("/sales/", method="POST", data={"status": 2}, headers=auth_headers)
    print(f"[+] Sale 2 created: ID={sale2['id']}, code={sale2['code']}, status={sale2['status']}")
    
    print("[*] Creating Sale 3...")
    sale3 = make_request("/sales/", method="POST", data={}, headers=auth_headers)
    print(f"[+] Sale 3 created: ID={sale3['id']}, code={sale3['code']}, status={sale3['status']}")
    
    # Assert codes are incrementing
    assert sale1["code"] < sale2["code"] < sale3["code"], "Codes are not incrementing!"
    print("[+] Verification: Codes are correctly incrementing!")
    
    print("[*] Listing sales...")
    sales_list = make_request("/sales/", method="GET", headers=auth_headers)
    print(f"[+] Found {sales_list['total_items']} items in sales list.")
    items = sales_list["items"]
    codes = [item["code"] for item in items]
    print(f"    Codes in list: {codes}")
    
    print("[*] Retrieving Sale 2 by ID...")
    get_sale2 = make_request(f"/sales/{sale2['id']}", method="GET", headers=auth_headers)
    print(f"[+] Sale 2 retrieved. Status={get_sale2['status']}, code={get_sale2['code']}")
    assert get_sale2["code"] == sale2["code"], "Mismatch in retrieved sale code!"
    
    print("[*] Updating Sale 2 status to 1 (done)...")
    patched_sale2 = make_request(f"/sales/{sale2['id']}", method="PATCH", data={"status": 1}, headers=auth_headers)
    print(f"[+] Sale 2 updated. New status={patched_sale2['status']}")
    assert patched_sale2["status"] == 1, "Status update failed!"
    
    print("[*] Deleting Sale 3...")
    make_request(f"/sales/{sale3['id']}", method="DELETE", headers=auth_headers)
    print("[+] Sale 3 deleted.")
    
    print("[*] Verifying deletion of Sale 3...")
    try:
        make_request(f"/sales/{sale3['id']}", method="GET", headers=auth_headers)
        print("[X] Error: Sale 3 was not deleted!")
        assert False, "Sale 3 was not deleted!"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print("[+] Verified: Sale 3 is no longer accessible (404).")
        else:
            raise e
            
    print("\n==========================================")
    print("[+] ALL SALES API VERIFICATIONS PASSED!")
    print("==========================================\n")

if __name__ == "__main__":
    test_sales_endpoints()
