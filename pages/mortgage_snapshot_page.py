from pages.base_page import BasePage
from playwright.sync_api import expect
from utils.config import Config
from utils.entity_navigation import MY_DEALS_BUCKET, open_bucket_record
from datetime import datetime
import re


class MortgageSnapshotPage(BasePage):

    def __init__(self, page):
        super().__init__(page)

        # ==========================================================
        # Navigation
        # ==========================================================

        self.my_deals = page.get_by_role("link",name="My Deals")

        self.snapshot_tab = page.get_by_role("tab", name="Mortgage Snapshot", exact=True)

        self.snapshot_form_tab = page.get_by_role("tab",name="Mortgage Snapshot Form")

        self.snapshot_meeting_tab = page.get_by_role("tab",name="Mortgage Snapshot Meeting")

        # ==========================================================
        # Video Section
        # ==========================================================

        self.vfli_number = page.locator("#vfliNo")

        self.introduction_script = page.get_by_role("textbox",name="e.g., In this video, I'll")

        # ==========================================================
        # Client Needs
        # ==========================================================

        self.first_need = page.locator("#firstNeed")

        self.ok_got_it = page.get_by_role("textbox",name="Ok, got it.")

        self.second_need = page.locator("#secondNeed")

        self.lets_get_to_work = page.get_by_role("textbox",name="Let's get to work.")

        # ==========================================================
        # Primary Credit
        # ==========================================================

        self.credit_score = page.locator("#creditScore")

        self.tds_score = page.locator("#tdsScore")

        self.credit_utilization = page.locator("#creditUtilization")

        self.high_utilization = page.get_by_role("checkbox",name="High utilization warning").first

        self.negative_credit = page.get_by_role("checkbox",name="Negative credit reported").first

        self.limited_credit = page.get_by_role("checkbox",name="Limited credit reporting").first

        self.collections = page.get_by_role("checkbox",name="Collections reported").first

        self.new_credit = page.get_by_role("checkbox",name="New to credit - No credit").first

        self.bankruptcy = page.get_by_role("checkbox",name="Bankruptcy reported").first

        self.proposal = page.get_by_role("checkbox",name="Proposal reported").first

        # ==========================================================
        # Co Applicant Credit
        # ==========================================================

        self.co_credit_score = page.locator("#coApplicantCreditScore")

        self.co_tds_score = page.locator("#coApplicantTdsScore")

        self.co_credit_utilization = page.locator("#coApplicantCreditUtilization")

        # ==========================================================
        # Cost Of Doing Nothing
        # ==========================================================

        self.current_balance = page.get_by_role("textbox",name="e.g., 65000")

        self.current_rate = page.get_by_role("textbox",name="e.g., 18.5%")

        self.years_to_pay = page.get_by_role("textbox",name="e.g., 31")

        self.total_interest = page.get_by_role("textbox",name="e.g., 89250")

        self.total_cost = page.get_by_role("textbox",name="e.g., 154250")

        self.monthly_payment = page.get_by_role("textbox",name="e.g., 1650")

        # ==========================================================
        # Mortgage Option 4
        # ==========================================================

        self.option4_dropdown = page.locator("select[name='mortgageOption4ProductType']").locator("..").get_by_role("combobox")

        self.option4_loan = page.locator("#mortgageOption4LoanAmount")

        self.option4_payment = page.locator("#mortgageOption4MonthlyPayment")

        self.option4_savings = page.locator("#mortgageOption4MonthlySavings")

        self.option4_point1 = page.locator("#mortgageOption4PointOne")

        self.option4_point2 = page.locator("#mortgageOption4PointTwo")

        self.option4_point3 = page.locator("#mortgageOption4PointThree")

        # ==========================================================
        # Mortgage Option 5
        # ==========================================================

        self.option5_dropdown = page.locator("select[name='mortgageOption5ProductType']").locator("..").get_by_role("combobox")

        self.option5_loan = page.locator("#mortgageOption5LoanAmount")

        self.option5_payment = page.locator("#mortgageOption5MonthlyPayment")

        self.option5_savings = page.locator("#mortgageOption5MonthlySavings")

        self.option5_point1 = page.locator("#mortgageOption5PointOne")

        self.option5_point2 = page.locator("#mortgageOption5PointTwo")

        self.option5_point3 = page.locator("#mortgageOption5PointThree")

        # ==========================================================
        # Home Appraised
        # ==========================================================

        self.get_opta_value = page.get_by_role("button",name="Get OPTA Value")

        self.maximum_value = page.locator("#mortgageAppraisedMaximumValue")
        self.minimum_value = page.locator("#mortgageAppraisedMinimumValue")
        self.less_all_mortgages = page.locator("#mortgageAppraisedLessAllMortgages")

        self.value_used = page.locator("#mortgageAppraisedValueUsed")

        self.ltv = page.get_by_role("textbox",name="e.g., 63.3%")

        self.plan_type = page.locator("select[name='finalClientSlidePlanType']").locator("..").get_by_role("combobox")

        # ==========================================================
        # Final Prompt
        # ==========================================================

        self.benefit_one = page.get_by_role("textbox",name="e.g., Monthly payments drop")

        self.benefit_two = page.get_by_role("textbox",name="e.g., Fixed rate locks in")

        self.benefit_three = page.get_by_role("textbox",name="e.g., Pre-approval gives you")

        self.final_prompt = page.get_by_role("textbox",name="e.g., What would your life")

        # ==========================================================
        # Buttons
        # ==========================================================

        self.save_button = page.get_by_role("button",name="Save")

        self.mortgage_snapshot_application_btn = page.get_by_role(
            "button", name="Mortgage Snapshot Application", exact=True
        ).first

        

        self.updated_success_toast = page.get_by_text(
            "Mortgage snapshot updated successfully"
        ).first
        self.created_success_toast = page.get_by_text("Mortgage snapshot created successfully").first
        self.meeting_saved_success_toast = page.get_by_text("Meeting reminder saved successfully").first
        self.meeting_updated_success_toast = page.get_by_text("Meeting reminder updated successfully").first
        self.meeting_deleted_success_toast = page.get_by_text("Meeting reminder deleted successfully").first
        



        #============================================================
        # Meeting Details
        #============================================================
        self.set_meeting_reminder_btn = page.get_by_role("button", name="Set Meeting Reminder")
        self.meeting_room_input = page.locator("select[name='meetingRoom']").locator("..").get_by_role("combobox")
        self.recipient_input = page.locator("select[name='reminderSetFor']").locator("..").get_by_role("combobox")
        self.start_date_input = page.locator("#start")
        self.end_date_input = page.locator("#end")
        self.description_input = page.locator("#description")
        self.meeting_link_input = page.get_by_role("textbox", name="https://example.com/meeting-")
        self.email_notify_checkbox = page.get_by_role("checkbox", name="Client get notified via Email?")
        self.save_meeting_reminder_btn = page.get_by_role('button', name="Save")

        self.search_keyword_input = page.get_by_role('textbox', name= 'Search by description, start, end, remind...')

        self.export_button = page.get_by_role('button', name= 'Export')

        self.meeting_menu = page.locator("button[aria-haspopup='menu']")
        self.view_option = page.get_by_role("menuitem", name="View")
        self.edit_option = page.get_by_role("menuitem", name="Edit")
        self.delete_option = page.get_by_role("menuitem", name="Delete")

        self.view_description = (page.locator("div").filter(has=page.get_by_text("Description", exact=True)).locator("p.font-medium"))

        self.view_remind = page.locator("div").filter(has=self.page.get_by_text("Remind", exact=True)).locator("p.font-medium")
        

        self.view_start = (page.locator("div").filter(has=page.get_by_text("Start", exact=True)).locator("p.font-medium"))

        self.view_end = (page.locator("div").filter(has=page.get_by_text("End", exact=True)).locator("p.font-medium"))

        self.view_meeting_room = (page.locator("div").filter(has=page.get_by_text("Meeting Room", exact=True)).locator("p.font-medium"))

        self.view_client_notified = (page.locator("div").filter(has=page.get_by_text("Client Notified", exact=True)).locator("p.font-medium"))

        self.view_meeting_url = (page.locator("div").filter(has=page.get_by_text("Meeting URL", exact=True)).locator("a"))

        self.close_view_popup_btn = page.get_by_role("button", name="Close")

        self.update_meeting_reminder_btn = page.get_by_role('button', name="Update")

        #===========================================================
        #stage Complete
        #===========================================================
        self.stage_complete_btn = page.get_by_role('button', name="Complete Stage")
        self.move_to_next_stage_btn = page.get_by_role('button', name="Move to Next Stage")
        self.stage_completed_success_toast = page.get_by_text(
            "Lead moved to Appraisal Ordered"
        ).first


        #============================================================
        # Global Search
        #============================================================
        self.global_search = page.get_by_role(
            "textbox", name=re.compile("Search leads", re.I)
        )




    # ==============================================================
    # Dynamic Locators
    # ==============================================================

    def deal(self, deal_name: str):
        return self.page.get_by_role("link",name=deal_name).first

        

    def checkbox(self, name: str):
        return self.page.get_by_role("checkbox",name=name)

    # ==============================================================
    # Navigation
    # ==============================================================
    def open(self):
        self.page.goto(Config.BASE_URL)
        self.page.wait_for_load_state("domcontentloaded")
        try:
            self.page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass


    def open_snapshot(self, deal_name, bucket=MY_DEALS_BUCKET):

        open_bucket_record(self.page, bucket, deal_name)

        self.click(self.snapshot_tab)

        self.click(self.snapshot_form_tab)

    # ==============================================================
    # Video Section
    # ==============================================================

    def fill_video_section(self, data):

        self.fill(self.vfli_number,data.vfli_number)

        self.fill(self.introduction_script,data.introduction_script)

    def clear_video_section(self):
        self.fill(self.vfli_number, "")
        self.fill(self.introduction_script, "")

    def fill_invalid_vfli(self, value: str):
        self.fill(self.vfli_number, value)

    _SNAPSHOT_FIELD_ATTRS = {
        "vfliNo": "vfli_number",
        "introScript": "introduction_script",
        "firstNeed": "first_need",
        "firstClientResponse": "ok_got_it",
        "secondNeed": "second_need",
        "secondClientResponse": "lets_get_to_work",
        "creditScore": "credit_score",
        "tdsScore": "tds_score",
        "creditUtilization": "credit_utilization",
        "coApplicantCreditScore": "co_credit_score",
        "coApplicantTdsScore": "co_tds_score",
        "coApplicantCreditUtilization": "co_credit_utilization",
        "debtProfileCurrentTotalDebt": "current_balance",
        "debtProfileAverageInterestRate": "current_rate",
        "debtProfileAverageTimeToPayOff": "years_to_pay",
        "debtProfileInterestPaidOverTime": "total_interest",
        "debtProfileTrueCostOfDebt": "total_cost",
        "debtProfileMinimumPaymentNeeded": "monthly_payment",
        "mortgageOption4LoanAmount": "option4_loan",
        "mortgageOption4MonthlyPayment": "option4_payment",
        "mortgageOption4MonthlySavings": "option4_savings",
        "mortgageOption4PointOne": "option4_point1",
        "mortgageOption4PointTwo": "option4_point2",
        "mortgageOption4PointThree": "option4_point3",
        "mortgageOption5LoanAmount": "option5_loan",
        "mortgageOption5MonthlyPayment": "option5_payment",
        "mortgageOption5MonthlySavings": "option5_savings",
        "mortgageOption5PointOne": "option5_point1",
        "mortgageOption5PointTwo": "option5_point2",
        "mortgageOption5PointThree": "option5_point3",
        "mortgageAppraisedMinimumValue": "minimum_value",
        "mortgageAppraisedMaximumValue": "maximum_value",
        "mortgageAppraisedValueUsed": "value_used",
        "mortgageAppraisedLessAllMortgages": "less_all_mortgages",
        "mortgageAppraisedEstimatedLoanToValue": "ltv",
        "finalPrompt": "final_prompt",
        "finalClientSlidePointOne": "benefit_one",
        "finalClientSlidePointTwo": "benefit_two",
        "finalClientSlidePointThree": "benefit_three",
    }

    def snapshot_field(self, field_id: str):
        attr = self._SNAPSHOT_FIELD_ATTRS.get(field_id)
        if attr:
            return getattr(self, attr)
        return self.page.locator(f"#{field_id}")

    def set_snapshot_field(self, field_id: str, value: str):
        locator = self.snapshot_field(field_id)
        locator.scroll_into_view_if_needed()
        self.fill(locator, value)

    def clear_snapshot_field(self, field_id: str):
        self.set_snapshot_field(field_id, "")

    def clear_all_snapshot_fields(self):
        for field_id in self._SNAPSHOT_FIELD_ATTRS:
            locator = self.snapshot_field(field_id)
            if locator.count() > 0:
                locator.scroll_into_view_if_needed()
                self.fill(locator, "")
        for checkbox in self.page.get_by_role("checkbox").all():
            if checkbox.is_checked():
                checkbox.uncheck()

    def fill_valid_baseline(self, data):
        """Fill every snapshot section with valid data (no navigation or save)."""
        self.fill_video_section(data)
        self.fill_client_needs(data)
        self.fill_primary_credit(data)
        self.fill_co_applicant_credit(data)
        self.fill_cost_of_doing_nothing(data)
        self.fill_option_four(data)
        self.fill_option_five(data)
        self.fill_home_appraised(data)
        self.fill_final_prompt(data)

    # ==============================================================
    # Client Needs
    # ==============================================================

    def fill_client_needs(self, data):

        self.fill(self.first_need,data.first_need)

        self.fill(self.ok_got_it,data.ok_got_it)

        self.fill(self.second_need,data.second_need)

        self.fill(self.lets_get_to_work,data.lets_get_to_work)

    # ==============================================================
    # Primary Credit
    # ==============================================================

    def fill_primary_credit(self, data):

        self.fill(self.credit_score,data.credit_score)

        self.fill(self.tds_score,data.tds_score)

        self.fill(self.credit_utilization,data.credit_utilization)

        for warning in data.primary_warnings:

            self.check(self.checkbox(warning).first)

    # ==============================================================
    # Co Applicant Credit
    # ==============================================================

    def fill_co_applicant_credit(self, data):

        self.fill(self.co_credit_score,data.co_credit_score)

        self.fill(self.co_tds_score,data.co_tds_score)

        self.fill(self.co_credit_utilization,data.co_credit_utilization)

        for warning in data.co_warnings:

            self.check(self.checkbox(warning).nth(1))

        

    # ==============================================================
    # Cost Of Doing Nothing
    # ==============================================================

    def fill_cost_of_doing_nothing(self, data):

        self.fill(self.current_balance,data.current_balance)

        self.fill(self.current_rate,data.current_rate)

        self.fill(self.years_to_pay,data.years_to_pay)

        self.fill(self.total_interest,data.total_interest)

        self.fill(self.total_cost,data.total_cost)

        self.fill(self.monthly_payment,data.monthly_payment)

    # ==============================================================
    # Mortgage Option 4
    # ==============================================================

    def fill_option_four(self, data):

        self.click(self.option4_dropdown)

        self.click(self.page.get_by_role("option", name=data.option4_type, exact=True))

        self.fill(self.option4_loan,data.option4_loan)

        self.fill(self.option4_payment,data.option4_payment)

        self.fill(self.option4_savings,data.option4_savings)

        self.fill(self.option4_point1,data.option4_point1)

        self.fill(self.option4_point2,data.option4_point2)

        self.fill(self.option4_point3,data.option4_point3)

    # ==============================================================
    # Mortgage Option 5
    # ==============================================================

    def fill_option_five(self, data):

        self.click(self.option5_dropdown)

        # self.click(
        #     self.option(data.option5_type))
        self.click(self.page.get_by_role("option",name=data.option5_type, exact=True))

        self.fill(self.option5_loan,data.option5_loan)

        self.fill(self.option5_payment,data.option5_payment)

        self.fill(self.option5_savings,data.option5_savings)

        self.fill(self.option5_point1,data.option5_point1)

        self.fill(self.option5_point2,data.option5_point2)

        self.fill(self.option5_point3,data.option5_point3)

    # ==============================================================
    # Home Appraised
    # ==============================================================

    def fill_home_appraised(self, data):

        self.fill(self.minimum_value,data.min_value)
        self.fill(self.maximum_value,data.max_value)

        self.fill(self.value_used,data.value_used)
        self.fill(self.less_all_mortgages,data.less_all_mortgages)

        self.fill(self.ltv, data.ltv)

        self.click(self.plan_type)

        self.click(self.page.get_by_role("option", name=data.plan_type, exact=True))

    # ==============================================================
    # Final Prompt
    # ==============================================================

    def fill_final_prompt(self, data):

        self.fill(self.benefit_one,data.benefit_one)

        self.fill( self.benefit_two,data.benefit_two)

        self.fill(self.benefit_three,data.benefit_three)

        self.fill(self.final_prompt,data.final_prompt)

    # ==============================================================
    # Save
    # ==============================================================

    def save(self):
        self.click(self.save_button)



    # ==============================================================
    # Verify
    # ==============================================================

    def verify_saved(self):
        toast = self.page.locator('section[aria-label="Notifications alt+T"]')
        success = toast.get_by_text(
            "Mortgage snapshot created successfully"
        ).or_(toast.get_by_text("Mortgage snapshot updated successfully"))
        self.wait_visible(success.first)
        self.verify_visible(success.first)



    @property
    def active_tab(self):
        return self.page.get_by_role("tab",name="Mortgage Snapshot Meeting")


    #==============================================================
    #Mee
    #==============================================================

    def open_meeting_menu(self, data):
            self.meeting_row = self.page.get_by_role("row").filter(has_text=data.description)
            self.click(self.meeting_row.locator("button[aria-haspopup='menu']"))

            

    def view_meeting(self):
        self.wait_visible(self.view_option)
        self.click(self.view_option)


    def edit_meeting(self):
        self.wait_visible(self.edit_option)
        self.click(self.edit_option)


    def delete_meeting(self, data):
        self.open_meeting_menu(data)
        self.wait_visible(self.delete_option)
        self.click(self.delete_option)

        self.click(self.page.get_by_role("button", name="Delete"))



    def get_meeting_description(self):
        return (
        self.page
        .get_by_label("Meeting Reminder Details")
        .locator("p:text-is('Description') + p.font-medium")
 
    )

    def get_reminder(self):
        return self.page.get_by_label("Meeting Reminder Details").locator(
        "p:text-is('Remind') + p.font-medium"
    )

    def get_start_datetime(self):
        return self.page.get_by_label("Meeting Reminder Details").locator(
        "p:text-is('Start') + p.font-medium"
    )

    def get_end_datetime(self):
        return self.page.get_by_label("Meeting Reminder Details").locator(
        "p:text-is('End') + p.font-medium"
    )

    def get_meeting_room(self):
        return self.page.get_by_label("Meeting Reminder Details").locator(
        "p:text-is('Meeting Room') + p.font-medium"
    )

    def get_client_notified(self):
        return self.page.get_by_label("Meeting Reminder Details").locator(
        "p:text-is('Client Notified') + p.font-medium"
    )

    def get_meeting_url(self):
        return self.page.get_by_label("Meeting Reminder Details").locator(
        "p:text-is('Meeting URL') + a"
    )

    def close_view_popup(self):
        self.click(self.close_view_popup_btn)

    def enter_meeting_details(self, data):
        self.fill(self.description_input, data.description)
        self.fill(self.start_date_input, data.start_datetime)
        self.fill(self.end_date_input, data.end_datetime)
        self.click(self.meeting_room_input)
        self.click(self.page.get_by_role("option", name=data.meeting_room, exact=True))
        self.click(self.recipient_input)
        self.click(self.page.get_by_role("option", name=data.recipient, exact=True))
        self.fill(self.meeting_link_input, data.meeting_link)
        self.click(self.email_notify_checkbox)
        self.click(self.update_meeting_reminder_btn)

    # ==============================================================
    # Complete Flow
    # ==============================================================

    def complete_snapshot(
        self, deal_name, 
        data
    ):

        self.open_snapshot(deal_name)

        self.fill_video_section(data)

        self.fill_client_needs(data)

        self.fill_primary_credit(data)

        self.fill_co_applicant_credit(data)

        self.fill_cost_of_doing_nothing(data)

        self.fill_option_four(data)

        self.fill_option_five(data)

        self.fill_home_appraised(data)

        self.fill_final_prompt(data)

        self.save()

    def create_meeting(self, data):
        self.click(self.set_meeting_reminder_btn)

    def fill_meeting_details(self, data):

        self.description_data = data.description
        self.start_datetime_data = data.start_datetime
        self.end_datetime_data = data.end_datetime
        self.meeting_room_data = data.meeting_room
        self.recipient_data = data.recipient
        self.meeting_link_data = data.meeting_link
        self.fill(self.start_date_input, self.start_datetime_data)  
        self.fill(self.end_date_input, self.end_datetime_data)      

        self.click(self.meeting_room_input)
        self.click(self.page.get_by_role("option", name=self.meeting_room_data, exact=True))
        self.click(self.recipient_input)
        self.click(self.page.get_by_role("option", name=self.recipient_data, exact=True))

        
        self.fill(self.description_input, self.description_data)
        self.fill(self.meeting_link_input, self.meeting_link_data)
        self.click(self.email_notify_checkbox)

        self.click(self.save_meeting_reminder_btn)

    def meeting_search_export(self, data):

        self.click(self.search_keyword_input)
        keyword = data.description.split(" ")[0]
        self.fill(self.search_keyword_input, keyword.lower())
        meeting_row = self.page.get_by_role("row").filter(
            has_text=re.compile(re.escape(keyword), re.I)
        )
        expect(meeting_row.first).to_be_visible(timeout=Config.TIMEOUT)
        self.click(self.export_button)
        expect(self.export_button).to_be_enabled(timeout=Config.TIMEOUT)

    def meeting_menu_actions(self, data):


        self.open_meeting_menu(data)
        self.view_meeting()
        self.verify_meeting_details(data)
        self.open_meeting_menu(data)
        self.edit_meeting()
        self.enter_meeting_details(data)

        

    def verify_searched(self):
        return self.page.locator("#meeting-reminder-table").get_by_role("row").filter(has_text="Mortgage Meeting").get_by_role("cell").filter(has_text="Mortgage Meeting")

    def verify_meeting_details(self, data):


        self.verify_equal(self.get_meeting_description(), self.description_data)
        if self.recipient_data == "Client & Agent":
            self.verify_equal(self.get_reminder(), "both")
        else:
            self.verify_equal(self.get_reminder(), self.recipient_data.lower())
        self.expected_start = data.start_dt.strftime("%b %d, %Y, %I:%M %p")
        self.expected_end = data.end_dt.strftime("%b %d, %Y, %I:%M %p")
        self.verify_datetime_equal(self.get_start_datetime(), self.expected_start)
        self.verify_datetime_equal(self.get_end_datetime(), self.expected_end)
        self.verify_equal(self.get_meeting_room(), self.meeting_room_data)
        self.verify_equal(self.get_meeting_url(), self.meeting_link_data)
        self.close_view_popup()

    def verify_meeting_saved(self):
        auth_error = self.page.get_by_text(
            re.compile(r"Missing authentication token", re.I)
        )
        if auth_error.count() > 0:
            raise AssertionError(
                "Meeting save failed: CRM session lost auth token after MS App RBAC. "
                f"Page text sample: {auth_error.first.inner_text()!r}"
            )
        self.wait_visible(self.meeting_saved_success_toast)
        self.verify_visible(self.meeting_saved_success_toast)


    def verify_meeting_updated(self):
        self.wait_visible(self.meeting_updated_success_toast)
        self.verify_visible(self.meeting_updated_success_toast)


    def verify_meeting_deleted(self):
        self.wait_visible(self.meeting_deleted_success_toast)
        self.verify_visible(self.meeting_deleted_success_toast)
            
        
    def open_meeting_tab(self):
        self.click(self.active_tab)

    @staticmethod
    def read_combobox_text(combobox) -> str:
        combobox.scroll_into_view_if_needed()
        text = combobox.inner_text()
        for placeholder in ("Select an option...", "Select product type"):
            text = text.replace(placeholder, "")
        return " ".join(text.split())

    def capture_snapshot_form_values(self) -> dict[str, str]:
        """Read editable snapshot fields for persistence verification."""
        values = {
            field_id: self.snapshot_field(field_id).input_value()
            for field_id in self._SNAPSHOT_FIELD_ATTRS
            if self.snapshot_field(field_id).count() > 0
        }
        if self.option4_dropdown.count() > 0:
            values["mortgageOption4Type"] = self.read_combobox_text(self.option4_dropdown)
        if self.option5_dropdown.count() > 0:
            values["mortgageOption5Type"] = self.read_combobox_text(self.option5_dropdown)
        values.update(self._capture_credit_warning_checkboxes())
        return values

    _CREDIT_WARNING_NAMES = (
        "High utilization warning",
        "Negative credit reported",
        "Limited credit reporting",
        "Collections reported",
        "New to credit - No credit",
        "Bankruptcy reported",
        "Proposal reported",
    )

    def _checkbox_capture_value(self, checkbox) -> str:
        return "checked" if checkbox.is_checked() else "unchecked"

    def _capture_credit_warning_checkboxes(self) -> dict[str, str]:
        """Persist credit-warning checkbox states through stage transitions."""
        values: dict[str, str] = {}
        for name in self._CREDIT_WARNING_NAMES:
            primary = self.page.get_by_role("checkbox", name=name).first
            if primary.count() > 0:
                try:
                    if primary.is_visible():
                        values[f"primaryCreditWarning:{name}"] = (
                            self._checkbox_capture_value(primary)
                        )
                except Exception:
                    pass
            co = self.page.get_by_role("checkbox", name=name).nth(1)
            if co.count() > 1:
                try:
                    if co.is_visible():
                        values[f"coCreditWarning:{name}"] = self._checkbox_capture_value(
                            co
                        )
                except Exception:
                    pass
        return values

    def reopen_snapshot_form_tab(self) -> None:
        self.click(self.snapshot_tab)
        expect(self.snapshot_tab).to_have_attribute("data-state", "active", timeout=30000)
        self.click(self.snapshot_form_tab)
        expect(self.snapshot_form_tab).to_have_attribute("data-state", "active", timeout=30000)

    def reopen_snapshot_meeting_tab(self) -> None:
        self.click(self.snapshot_tab)
        expect(self.snapshot_tab).to_have_attribute("data-state", "active", timeout=30000)
        self.click(self.snapshot_meeting_tab)
        expect(self.snapshot_meeting_tab).to_have_attribute("data-state", "active", timeout=30000)
        expect(self.set_meeting_reminder_btn).to_be_visible(timeout=Config.TIMEOUT)

    def open_mortgage_snapshot_application(self, context):
        """Open MS App in a new tab via CRM footer button (save-only flow)."""
        from playwright.sync_api import Page

        self.reopen_snapshot_form_tab()
        expect(self.mortgage_snapshot_application_btn).to_be_enabled(timeout=30000)
        with context.expect_page() as new_page_info:
            self.click(self.mortgage_snapshot_application_btn)
        app_page: Page = new_page_info.value
        app_page.set_default_timeout(Config.TIMEOUT)
        app_page.wait_for_load_state("domcontentloaded")
        app_page.wait_for_url(re.compile(r".*/leads(?:\?.*)?$"), timeout=60000)
        return app_page

    def complete_stage(self):
        self.click(self.stage_complete_btn)
        dialog = self.page.get_by_role("alertdialog", name="Move to Next Stage?")
        self.wait_visible(dialog)
        self.click(dialog.get_by_role("button", name="Move to Next Stage"))

    def verify_stage_completed(self):
        self.wait_visible(self.stage_completed_success_toast)
        self.verify_visible(self.stage_completed_success_toast)
    
   