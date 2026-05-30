import time
import requests
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

RETRYABLE = {429, 503, 504}

def make_request_with_retry(url, headers, params=None, max_retries=None):
    if max_retries is None:
        max_retries = config.MAX_RETRIES
    attempt = 0
    while attempt <= max_retries:
        try:
            r = requests.get(url, headers=headers, params=params, timeout=30)
            if r.status_code == 200:
                return r
            elif r.status_code in RETRYABLE:
                attempt += 1
                wait = int(r.headers.get("Retry-After", config.RETRY_BACKOFF * (2 ** (attempt-1))))
                time.sleep(wait)
            elif r.status_code == 401:
                raise Exception("HTTP 401 Unauthorized")
            elif r.status_code == 403:
                raise Exception("HTTP 403 Forbidden")
            else:
                raise Exception(f"HTTP {r.status_code}")
        except requests.exceptions.Timeout:
            attempt += 1
            time.sleep(30)
    raise Exception(f"Max retries exceeded for {url}")