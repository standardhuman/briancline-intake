#!/usr/bin/env python3
"""
Debug test to capture console logs and network errors
"""

from playwright.sync_api import sync_playwright
import tempfile
from PIL import Image
import os

def create_test_image():
    """Create a single test image"""
    temp_dir = tempfile.mkdtemp()
    img = Image.new('RGB', (400, 300), color=(100, 150, 200))
    filepath = os.path.join(temp_dir, 'test_image.png')
    img.save(filepath)
    return filepath

def test_submission_with_debug():
    print("=== Debugging Form Submission ===\n")

    test_file = create_test_image()
    console_logs = []
    network_failures = []
    network_requests = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Headless for automated testing
        page = browser.new_page()

        # Capture console messages
        page.on('console', lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

        # Capture network failures
        page.on('requestfailed', lambda request: network_failures.append(f"FAILED: {request.method} {request.url} - {request.failure}"))

        # Capture all network requests
        page.on('request', lambda request: network_requests.append(f"→ {request.method} {request.url}"))
        page.on('response', lambda response: print(f"← {response.status} {response.url}"))

        # Navigate
        print("Navigating to form...")
        page.goto('http://localhost:5173')
        page.wait_for_load_state('networkidle')

        # Fill minimum required fields
        print("\nFilling form...")
        page.locator('#name').fill('Debug Test')
        page.locator('#email').fill('debug@test.com')
        page.locator('#company').fill('Debug Co')
        page.locator('#business-description').fill('Testing submission')
        page.locator('#project-type').select_option('landing-page')

        # Add file
        print("Adding file...")
        page.locator('#file-input').set_input_files(test_file)
        page.wait_for_timeout(1000)

        print("\nSubmitting form...")
        submit_btn = page.locator('button[type="submit"]')
        submit_btn.click()

        # Wait and observe
        print("\nWaiting for response (30 seconds)...")
        page.wait_for_timeout(30000)

        print(f"\n=== Final URL: {page.url} ===")

        # Print diagnostics
        print("\n=== Console Logs ===")
        for log in console_logs:
            print(log)

        print("\n=== Network Failures ===")
        if network_failures:
            for failure in network_failures:
                print(failure)
        else:
            print("No network failures")

        print("\n=== Network Requests (last 10) ===")
        for req in network_requests[-10:]:
            print(req)

        # Take final screenshot
        page.screenshot(path='test-screenshots/debug-final.png')
        print("\nScreenshot saved: test-screenshots/debug-final.png")

        browser.close()

    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)

if __name__ == '__main__':
    test_submission_with_debug()
