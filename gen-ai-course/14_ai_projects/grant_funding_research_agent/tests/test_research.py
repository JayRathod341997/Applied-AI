import pytest
from grant_research.models import ResearchRequest, ResearchCriteria


def test_research_criteria():
    criteria = ResearchCriteria(veteran_owned=True, industry=["security"])
    assert criteria.veteran_owned is True


def test_research_request():
    req = ResearchRequest(criteria=ResearchCriteria())
    assert req.action == "run_research"
