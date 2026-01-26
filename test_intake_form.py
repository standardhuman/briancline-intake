#!/usr/bin/env python3
"""
Comprehensive test suite for Brian Cline's intake form
Tests all form fields, validations, file uploads, and submission flow
"""

from playwright.sync_api import sync_playwright, expect
import time
import os

class IntakeFormTester:
    def __init__(self, base_url='http://localhost:5173'):
        self.base_url = base_url
        self.test_results = []

    def log_test(self, test_name, status, details=""):
        """Log test result"""
        result = {
            'test': test_name,
            'status': status,
            'details': details
        }
        self.test_results.append(result)
        status_symbol = "✓" if status == "PASS" else "✗"
        print(f"{status_symbol} {test_name}: {details}")

    def test_page_load(self, page):
        """Test that the page loads correctly"""
        print("\n=== Testing Page Load ===")
        try:
            page.goto(self.base_url)
            page.wait_for_load_state('networkidle')

            # Check title
            title = page.title()
            assert "Project Intake" in title
            self.log_test("Page Load", "PASS", f"Title: {title}")

            # Check hero heading
            hero = page.locator('h1')
            expect(hero).to_contain_text("Fast launch, faster results")
            self.log_test("Hero Section", "PASS", "Hero text displayed correctly")

            # Check form exists
            form = page.locator('#intake-form')
            expect(form).to_be_visible()
            self.log_test("Form Visibility", "PASS", "Form is visible on page")

        except Exception as e:
            self.log_test("Page Load", "FAIL", str(e))

    def test_required_fields_validation(self, page):
        """Test that required fields show validation errors"""
        print("\n=== Testing Required Field Validations ===")
        try:
            page.goto(self.base_url)
            page.wait_for_load_state('networkidle')

            # Try to submit empty form
            submit_btn = page.locator('button[type="submit"]')
            submit_btn.click()

            # Check if browser validation prevents submission
            # Required fields: name, email, company, business-description, project-type
            required_fields = [
                {'selector': '#name', 'label': 'Name'},
                {'selector': '#email', 'label': 'Email'},
                {'selector': '#company', 'label': 'Company'},
                {'selector': '#business-description', 'label': 'Business Description'},
                {'selector': '#project-type', 'label': 'Project Type'}
            ]

            for field in required_fields:
                input_field = page.locator(field['selector'])
                is_required = input_field.get_attribute('required')
                if is_required is not None:
                    self.log_test(f"Required: {field['label']}", "PASS", "Field marked as required")
                else:
                    self.log_test(f"Required: {field['label']}", "FAIL", "Field not marked as required")

        except Exception as e:
            self.log_test("Required Field Validation", "FAIL", str(e))

    def test_contact_information_fields(self, page):
        """Test all contact information fields"""
        print("\n=== Testing Contact Information Fields ===")
        try:
            page.goto(self.base_url)
            page.wait_for_load_state('networkidle')

            # Test Name field
            name_field = page.locator('#name')
            name_field.fill('John Smith')
            assert name_field.input_value() == 'John Smith'
            self.log_test("Name Field", "PASS", "Can fill and retrieve name")

            # Test Email field
            email_field = page.locator('#email')
            email_field.fill('john.smith@example.com')
            assert email_field.input_value() == 'john.smith@example.com'
            self.log_test("Email Field", "PASS", "Can fill and retrieve email")

            # Test Phone field (optional)
            phone_field = page.locator('#phone')
            phone_field.fill('555-123-4567')
            assert phone_field.input_value() == '555-123-4567'
            self.log_test("Phone Field", "PASS", "Can fill and retrieve phone")

            # Test Company field
            company_field = page.locator('#company')
            company_field.fill('Acme Corporation')
            assert company_field.input_value() == 'Acme Corporation'
            self.log_test("Company Field", "PASS", "Can fill and retrieve company")

        except Exception as e:
            self.log_test("Contact Information Fields", "FAIL", str(e))

    def test_business_section(self, page):
        """Test business description and website fields"""
        print("\n=== Testing Business Section ===")
        try:
            page.goto(self.base_url)
            page.wait_for_load_state('networkidle')

            # Test business description textarea
            desc_field = page.locator('#business-description')
            test_description = "We provide innovative software solutions for small businesses."
            desc_field.fill(test_description)
            assert desc_field.input_value() == test_description
            self.log_test("Business Description", "PASS", "Can fill textarea")

            # Test current website URL field
            website_field = page.locator('#current-website')
            website_field.fill('https://example.com')
            assert website_field.input_value() == 'https://example.com'
            self.log_test("Current Website", "PASS", "Can fill URL field")

        except Exception as e:
            self.log_test("Business Section", "FAIL", str(e))

    def test_project_details_section(self, page):
        """Test project type, pages needed, and features fields"""
        print("\n=== Testing Project Details Section ===")
        try:
            page.goto(self.base_url)
            page.wait_for_load_state('networkidle')

            # Test project type select
            project_type = page.locator('#project-type')
            project_type.select_option('landing-page')
            assert project_type.input_value() == 'landing-page'
            self.log_test("Project Type Select", "PASS", "Can select landing page")

            # Test other options
            project_type.select_option('simple-site')
            assert project_type.input_value() == 'simple-site'
            self.log_test("Project Type Options", "PASS", "Can change selection")

            # Test pages needed
            pages_field = page.locator('#pages-needed')
            pages_field.fill('Home, About, Services, Contact, Portfolio')
            assert 'Home' in pages_field.input_value()
            self.log_test("Pages Needed", "PASS", "Can list pages")

            # Test features
            features_field = page.locator('#features')
            features_field.fill('Contact form, Photo gallery, Google Maps integration')
            assert 'Contact form' in features_field.input_value()
            self.log_test("Features", "PASS", "Can list features")

        except Exception as e:
            self.log_test("Project Details Section", "FAIL", str(e))

    def test_radio_button_groups(self, page):
        """Test all radio button groups"""
        print("\n=== Testing Radio Button Groups ===")
        try:
            page.goto(self.base_url)
            page.wait_for_load_state('networkidle')

            # Test logo radio buttons
            logo_yes = page.locator('input[name="has-logo"][value="yes"]')
            logo_yes.check()
            assert logo_yes.is_checked()
            self.log_test("Logo Radio - Yes", "PASS", "Can select 'Yes'")

            logo_need = page.locator('input[name="has-logo"][value="need-design"]')
            logo_need.check()
            assert logo_need.is_checked()
            assert not logo_yes.is_checked()
            self.log_test("Logo Radio - Need Design", "PASS", "Can change selection")

            # Test photos radio buttons
            photos_yes = page.locator('input[name="has-photos"][value="yes"]')
            photos_yes.check()
            assert photos_yes.is_checked()
            self.log_test("Photos Radio - Yes", "PASS", "Can select photos option")

            # Test copy radio buttons
            copy_yes = page.locator('input[name="has-copy"][value="yes"]')
            copy_yes.check()
            assert copy_yes.is_checked()
            self.log_test("Copy Radio - Yes", "PASS", "Can select copy option")

            # Test post-launch radio buttons
            post_maintenance = page.locator('input[name="post-launch"][value="maintenance"]')
            post_maintenance.check()
            assert post_maintenance.is_checked()
            self.log_test("Post-Launch Radio", "PASS", "Can select maintenance option")

        except Exception as e:
            self.log_test("Radio Button Groups", "FAIL", str(e))

    def test_design_section(self, page):
        """Test design inspiration field"""
        print("\n=== Testing Design Section ===")
        try:
            page.goto(self.base_url)
            page.wait_for_load_state('networkidle')

            # Test inspiration textarea
            inspiration = page.locator('#inspiration')
            test_urls = "https://stripe.com\nhttps://linear.app"
            inspiration.fill(test_urls)
            assert 'stripe.com' in inspiration.input_value()
            self.log_test("Design Inspiration", "PASS", "Can add inspiration URLs")

        except Exception as e:
            self.log_test("Design Section", "FAIL", str(e))

    def test_file_upload_ui(self, page):
        """Test file upload drop zone and UI interactions"""
        print("\n=== Testing File Upload UI ===")
        try:
            page.goto(self.base_url)
            page.wait_for_load_state('networkidle')

            # Check drop zone exists
            drop_zone = page.locator('#drop-zone')
            expect(drop_zone).to_be_visible()
            self.log_test("Drop Zone Visibility", "PASS", "Drop zone is visible")

            # Check file input exists (hidden)
            file_input = page.locator('#file-input')
            assert file_input.get_attribute('type') == 'file'
            assert file_input.get_attribute('accept') == 'image/*'
            assert file_input.get_attribute('multiple') is not None
            self.log_test("File Input Configuration", "PASS", "File input properly configured")

            # Note: Actual file upload testing would require creating test files
            # and using page.set_input_files() method
            self.log_test("File Upload Note", "INFO", "File upload functionality exists, actual upload requires test files")

        except Exception as e:
            self.log_test("File Upload UI", "FAIL", str(e))

    def test_timeline_and_budget_selects(self, page):
        """Test timeline and budget select fields"""
        print("\n=== Testing Timeline & Budget Selects ===")
        try:
            page.goto(self.base_url)
            page.wait_for_load_state('networkidle')

            # Test timeline select
            timeline = page.locator('#timeline')
            timeline.select_option('asap')
            assert timeline.input_value() == 'asap'
            self.log_test("Timeline Select - ASAP", "PASS", "Can select ASAP")

            timeline.select_option('flexible')
            assert timeline.input_value() == 'flexible'
            self.log_test("Timeline Select - Flexible", "PASS", "Can change to flexible")

            # Test budget select
            budget = page.locator('#budget')
            budget.select_option('2k-4k')
            assert budget.input_value() == '2k-4k'
            self.log_test("Budget Select", "PASS", "Can select budget range")

        except Exception as e:
            self.log_test("Timeline & Budget", "FAIL", str(e))

    def test_additional_fields(self, page):
        """Test additional details and referral fields"""
        print("\n=== Testing Additional Fields ===")
        try:
            page.goto(self.base_url)
            page.wait_for_load_state('networkidle')

            # Test additional details
            additional = page.locator('#additional')
            additional.fill('Looking forward to working together!')
            assert 'forward' in additional.input_value()
            self.log_test("Additional Details", "PASS", "Can fill additional details")

            # Test referral field
            referral = page.locator('#referral')
            referral.fill('LinkedIn')
            assert referral.input_value() == 'LinkedIn'
            self.log_test("Referral Field", "PASS", "Can fill referral source")

        except Exception as e:
            self.log_test("Additional Fields", "FAIL", str(e))

    def test_navigation_links(self, page):
        """Test navigation links"""
        print("\n=== Testing Navigation Links ===")
        try:
            page.goto(self.base_url)
            page.wait_for_load_state('networkidle')

            # Check nav logo link
            nav_logo = page.locator('nav a[href="https://briancline.co"]').first
            expect(nav_logo).to_be_visible()
            assert nav_logo.text_content().strip() == 'Brian Cline'
            self.log_test("Navigation Logo Link", "PASS", "Logo link is correct")

            # Check portfolio link
            portfolio_link = page.locator('nav a:has-text("View Portfolio")').first
            expect(portfolio_link).to_be_visible()
            self.log_test("Portfolio Link", "PASS", "Portfolio link is visible")

        except Exception as e:
            self.log_test("Navigation Links", "FAIL", str(e))

    def test_complete_form_fill(self, page):
        """Test filling out the entire form with valid data"""
        print("\n=== Testing Complete Form Fill ===")
        try:
            page.goto(self.base_url)
            page.wait_for_load_state('networkidle')

            # Fill all required fields
            page.locator('#name').fill('Jane Doe')
            page.locator('#email').fill('jane.doe@example.com')
            page.locator('#phone').fill('555-987-6543')
            page.locator('#company').fill('Tech Innovations Inc')
            page.locator('#business-description').fill('We build cutting-edge mobile applications')
            page.locator('#current-website').fill('https://techinnovations.example.com')
            page.locator('#project-type').select_option('standard-site')
            page.locator('#pages-needed').fill('Home, About, Services, Team, Contact, Blog')
            page.locator('#features').fill('Blog, Contact forms, Team profiles, Case studies')

            # Select radio options
            page.locator('input[name="has-logo"][value="yes"]').check()
            page.locator('input[name="has-photos"][value="some"]').check()
            page.locator('input[name="has-copy"][value="rough"]').check()

            # Fill design section
            page.locator('#inspiration').fill('https://apple.com\nhttps://airbnb.com')

            # Timeline and budget
            page.locator('#timeline').select_option('2-4-weeks')
            page.locator('#budget').select_option('4k-6k')

            # Post-launch
            page.locator('input[name="post-launch"][value="maintenance"]').check()

            # Additional
            page.locator('#additional').fill('Excited to get started!')
            page.locator('#referral').fill('Google Search')

            # Verify all fields are filled
            assert page.locator('#name').input_value() == 'Jane Doe'
            assert page.locator('#project-type').input_value() == 'standard-site'
            assert page.locator('input[name="has-logo"][value="yes"]').is_checked()

            self.log_test("Complete Form Fill", "PASS", "All fields filled successfully")

        except Exception as e:
            self.log_test("Complete Form Fill", "FAIL", str(e))

    def test_form_responsiveness(self, page):
        """Test form at different viewport sizes"""
        print("\n=== Testing Form Responsiveness ===")
        try:
            # Test mobile viewport
            page.set_viewport_size({"width": 375, "height": 667})
            page.goto(self.base_url)
            page.wait_for_load_state('networkidle')

            form = page.locator('#intake-form')
            expect(form).to_be_visible()
            self.log_test("Mobile Responsiveness", "PASS", "Form visible on mobile")

            # Test tablet viewport
            page.set_viewport_size({"width": 768, "height": 1024})
            page.reload()
            page.wait_for_load_state('networkidle')
            expect(form).to_be_visible()
            self.log_test("Tablet Responsiveness", "PASS", "Form visible on tablet")

            # Test desktop viewport
            page.set_viewport_size({"width": 1920, "height": 1080})
            page.reload()
            page.wait_for_load_state('networkidle')
            expect(form).to_be_visible()
            self.log_test("Desktop Responsiveness", "PASS", "Form visible on desktop")

        except Exception as e:
            self.log_test("Form Responsiveness", "FAIL", str(e))

    def generate_report(self):
        """Generate test summary report"""
        print("\n" + "="*60)
        print("TEST SUMMARY REPORT")
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
        """Run all tests"""
        print("Starting Intake Form Test Suite")
        print("="*60)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Run all test methods
            self.test_page_load(page)
            self.test_required_fields_validation(page)
            self.test_contact_information_fields(page)
            self.test_business_section(page)
            self.test_project_details_section(page)
            self.test_radio_button_groups(page)
            self.test_design_section(page)
            self.test_file_upload_ui(page)
            self.test_timeline_and_budget_selects(page)
            self.test_additional_fields(page)
            self.test_navigation_links(page)
            self.test_complete_form_fill(page)
            self.test_form_responsiveness(page)

            browser.close()

        # Generate report
        self.generate_report()

if __name__ == '__main__':
    tester = IntakeFormTester()
    tester.run_all_tests()
