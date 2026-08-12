from pages.note_page import NotesPage
from test_page_data import negative_messages as msg
from test_page_data.note_data import notes_test_data
from test_page_data.test_entities import persist_my_deals_deal_name
from utils.lead_context import get_active_lead_name
from utils.logger import get_logger
from utils.reporting import register_test_data
from utils.validations import Validations

logger = get_logger()


def test_note_empty(authenticated_page, request):
    """Save empty note and verify validation message."""
    notes = NotesPage(authenticated_page)
    validator = Validations(authenticated_page)
    # lead_name = test_entities.MY_LEADS_DEAL_NAME
    lead_name = get_active_lead_name()

    notes.open()
    notes.open_lead(lead_name)
    notes.open_notes_tab()
    notes.click_add_note()
    notes.clear_note()
    notes.save_note()

    register_test_data(request.node, scenario="empty_note", lead_name=lead_name)
    validator.assert_field_error(msg.NOTE_EMPTY, item=request.node)


def test_add_edit_delete_note(authenticated_page):
    logger.info(f"Adding note with data: {notes_test_data}")
    lead_name = get_active_lead_name()

    notes_page = NotesPage(authenticated_page)
    notes_page.open()

    notes_page.open_lead(lead_name)
    notes_page.open_notes_tab()

    notes_page.click_add_note()
    notes_page.enter_note(notes_test_data["note"]["text"])
    notes_page.apply_formatting()
    notes_page.select_heading(notes_test_data["note"]["heading"])
    notes_page.select_note_status(notes_test_data["note"]["status"])
    notes_page.save_note_successfully()

    notes_page.edit_note(
        notes_test_data["note"]["text"],
        notes_test_data["note"]["updated_text"],
    )

    notes_page.delete_note(notes_test_data["note"]["updated_text"])

    notes_page.move_to_sales()
    notes_page.verify_moved_to_sales()
    notes_page.verify_lead_in_my_deals(lead_name)
    persist_my_deals_deal_name(lead_name)
