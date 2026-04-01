import pytest
from real_estate_crm.models import LeadInput, LeadResponse, Qualification


def test_lead_input():
    lead = LeadInput(
        name="Sarah Chen",
        email="sarah@example.com",
        phone="+14155551234",
        message="Looking for a 3BR home in Oakland",
    )
    assert lead.name == "Sarah Chen"
    assert lead.source == "website_form"


def test_qualification():
    q = Qualification(
        score=92, category="hot", reasoning="Pre-approved, specific budget"
    )
    assert q.score == 92
    assert q.category == "hot"
