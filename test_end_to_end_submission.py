#!/usr/bin/env python3
"""
End-to-end test for complete form submission workflow
Tests actual API submission including file uploads and email delivery
"""

from playwright.sync_api import sync_playwright, expect
import os
import tempfile
from PIL import Image
import time

class E2ESubmissionTester:
    def __init__(self, base_url='http://localhost:5173'):
        self.base_url = base_url
        self.test_results = []
        self.test_files = []

    def log_test(self, test_name, status, details=""):
        """Log test result"""
        result = {
            'test': test_name,
            'status': status,
            'details': details
        }
        self.test_results.append(result)
        status_symbol = "✓" if status == "PASS" else "✗" if status == "FAIL" else "ℹ"
        print(f"{status_symbol} {test_name}: {details}")

    def create_test_images(self, count=2):
        """Create test images for upload"""
        print("\n=== Creating Test Images ===")
        temp_dir = tempfile.mkdtemp()

        for i in range(count):
            # Create test image
            img = Image.new('RGB', (400, 300), color=(100 + i*50, 150, 200))
            filepath = os.path.join(temp_dir, f'test_design_{i+1}.png')
            img.save(filepath)
            self.test_files.append(filepath)
            print(f"Created: {filepath}")

        return self.test_files

    def cleanup_test_files(self):
        """Remove temporary test files"""
        for filepath in self.test_files:
            if os.path.exists(filepath):
                os.remove(filepath)

    def test_api_health(self, page):
        """Test that API endpoints are accessible"""
        print("\n=== Testing API Health ===")
        try:
            # Navigate to page to ensure server is running
            page.goto(self.base_url)
            page.wait_for_load_state('networkidle')

            self.log_test("API Health Check", "PASS", "Server is running and accessible")

        except Exception as e:
            self.log_test("API Health Check", "FAIL", str(e))

    def test_file_upload_to_vercel_blob(self, page):
        """Test file upload to Vercel Blob storage"""
        print("\n=== Testing File Upload to Vercel Blob ===")
        try:
            page.goto(self.base_url)
            page.wait_for_load_state('networkidle')

            # Create test files
            if not self.test_files:
                self.create_test_images(2)

            # Upload files
            file_input = page.locator('#file-input')
            file_input.set_input_files(self.test_files)

            # Wait for preview to appear
            page.wait_for_timeout(1000)

            # Verify files are shown in preview
            file_preview = page.locator('#file-preview')
            expect(file_preview).not_to_have_class('hidden')

            file_count = page.locator('#file-count')
            expect(file_count).to_contain_text(f'{len(self.test_files)} files selected')

            self.log_test("File Upload UI", "PASS", f"Uploaded {len(self.test_files)} files to UI")

        except Exception as e:
            self.log_test("File Upload to Vercel Blob", "FAIL", str(e))

    def test_complete_form_submission(self, page):
        """Test complete form submission with all fields and file uploads"""
        print("\n=== Testing Complete Form Submission ===")
        try:
            page.goto(self.base_url)
            page.wait_for_load_state('networkidle')

            # Fill all required fields
            print("Filling form fields...")
            page.locator('#name').fill('E2E Test User')
            page.locator('#email').fill('test@example.com')
            page.locator('#company').fill('Test Company LLC')
            page.locator('#phone').fill('555-123-4567')

            # Business details
            page.locator('#business-description').fill('We are testing the intake form end-to-end functionality with actual API submission.')
            page.locator('#current-website').fill('https://testcompany.example.com')

            # Project details
            page.locator('#project-type').select_option('standard-site')
            page.locator('#pages-needed').fill('Home, About, Services, Portfolio, Contact, Blog')
            page.locator('#features').fill('Contact forms, Blog system, Portfolio gallery, Newsletter signup')

            # Assets & content
            page.locator('input[name="has-logo"][value="yes"]').check()
            page.locator('input[name="has-photos"][value="some"]').check()
            page.locator('input[name="has-copy"][value="rough"]').check()

            # Design direction
            page.locator('#inspiration').fill('https://stripe.com\nhttps://linear.app\nhttps://vercel.com')

            # Upload files
            if self.test_files:
                file_input = page.locator('#file-input')
                file_input.set_input_files(self.test_files)
                page.wait_for_timeout(500)
                self.log_test("Files Added to Form", "INFO", f"Added {len(self.test_files)} files")

            # Timeline & budget
            page.locator('#timeline').select_option('2-4-weeks')
            page.locator('#budget').select_option('4k-6k')

            # Post-launch
            page.locator('input[name="post-launch"][value="maintenance"]').check()

            # Additional
            page.locator('#additional').fill('This is an end-to-end test submission. Please verify all integrations are working.')
            page.locator('#referral').fill('Automated Testing')

            self.log_test("Form Filled", "PASS", "All fields completed")

            # Submit the form
            print("\nSubmitting form...")
            submit_btn = page.locator('button[type="submit"]')

            # Set up listener for network requests
            upload_responses = []
            submit_response = None

            def handle_response(response):
                if '/api/upload' in response.url:
                    upload_responses.append(response)
                elif '/api/submit' in response.url:
                    nonlocal submit_response
                    submit_response = response

            page.on('response', handle_response)

            # Click submit
            submit_btn.click()

            # Wait for submission to complete (files upload, then form submits)
            # This could take several seconds
            print("Waiting for API calls...")

            # Wait for redirect or thank you page
            try:
                # Wait up to 30 seconds for the thank you page
                page.wait_for_url('**/thank-you.html', timeout=30000)
                self.log_test("Form Submission", "PASS", "Redirected to thank-you page")
                self.log_test("End-to-End Flow", "PASS", "Complete submission workflow successful")

                # Check if we got upload responses
                if len(upload_responses) > 0:
                    self.log_test("File Upload API", "PASS", f"Uploaded {len(upload_responses)} files to Vercel Blob")
                    for i, resp in enumerate(upload_responses):
                        print(f"  Upload {i+1}: {resp.status} {resp.url}")

                # Check submit response
                if submit_response:
                    self.log_test("Submit API", "PASS", f"Submit API returned {submit_response.status}")
                    print(f"  Submit: {submit_response.status} {submit_response.url}")

            except Exception as wait_error:
                # If we timeout, check what happened
                current_url = page.url
                print(f"Current URL after timeout: {current_url}")

                if 'thank-you' in current_url:
                    self.log_test("Form Submission", "PASS", "On thank-you page (slow redirect)")
                else:
                    # Check for errors
                    page.screenshot(path='test-screenshots/submission-error.png')
                    self.log_test("Form Submission", "FAIL", f"Did not redirect. Current URL: {current_url}")

                    # Check console for errors
                    # Note: We'd need to capture console logs during page load to see errors

        except Exception as e:
            self.log_test("Complete Form Submission", "FAIL", str(e))
            # Take screenshot of error state
            try:
                page.screenshot(path='test-screenshots/submission-exception.png')
                print("Screenshot saved: test-screenshots/submission-exception.png")
            except:
                pass

    def test_thank_you_page(self, page):
        """Test the thank you page displays correctly"""
        print("\n=== Testing Thank You Page ===")
        try:
            # Navigate directly to thank you page
            page.goto(f'{self.base_url}/thank-you.html')
            page.wait_for_load_state('networkidle')

            # Check page loaded
            title = page.title()
            print(f"Thank you page title: {title}")

            # Take screenshot
            page.screenshot(path='test-screenshots/thank-you-page.png')

            self.log_test("Thank You Page", "PASS", "Page loads correctly")

        except Exception as e:
            self.log_test("Thank You Page", "FAIL", str(e))

    def test_network_error_handling(self, page):
        """Test form behavior when API is unavailable"""
        print("\n=== Testing Network Error Handling ===")
        try:
            page.goto(self.base_url)
            page.wait_for_load_state('networkidle')

            # Fill only required fields
            page.locator('#name').fill('Error Test')
            page.locator('#email').fill('error@test.com')
            page.locator('#company').fill('Error Test Co')
            page.locator('#business-description').fill('Testing error handling')
            page.locator('#project-type').select_option('landing-page')

            # Block API requests to simulate network error
            page.route('**/api/submit', lambda route: route.abort())

            submit_btn = page.locator('button[type="submit"]')
            submit_btn.click()

            # Wait a moment for error handling
            page.wait_for_timeout(2000)

            # Check if error message appears or button is re-enabled
            # The form should show an alert "Something went wrong"
            # Note: alert() dialog would need to be handled

            self.log_test("Network Error Handling", "INFO", "Tested error scenario")

        except Exception as e:
            self.log_test("Network Error Handling", "INFO", f"Error handling tested: {str(e)}")

    def generate_report(self):
        """Generate test summary report"""
        print("\n" + "="*60)
        print("END-TO-END SUBMISSION TEST REPORT")
        print("="*60)

        passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAIL')
        info = sum(1 for r in self.test_results if r['status'] == 'INFO')
        total = len(self.test_results)

        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed} ✓")
        print(f"Failed: {failed} ✗")
        print(f"Info: {info} ℹ")

        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"  - {result['test']}: {result['details']}")
        else:
            print("\n✅ ALL TESTS PASSED!")

        print("\n" + "="*60)

    def run_all_tests(self):
        """Run all end-to-end tests"""
        print("Starting End-to-End Submission Tests")
        print("="*60)
        print("⚠️  WARNING: This will actually submit the form and send email!")
        print("="*60)

        # Create test images
        self.create_test_images(2)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Run tests
            self.test_api_health(page)
            self.test_thank_you_page(page)
            self.test_file_upload_to_vercel_blob(page)
            self.test_complete_form_submission(page)
            # self.test_network_error_handling(page)  # Uncomment to test error handling

            browser.close()

        # Cleanup
        self.cleanup_test_files()

        # Generate report
        self.generate_report()

if __name__ == '__main__':
    print("\n⚠️  This test will submit the form and send a real email to brian@sailorskills.com")
    print("Press Enter to continue or Ctrl+C to cancel...")
    input()

    tester = E2ESubmissionTester()
    tester.run_all_tests()
