import pytest
from ep_job_app.models import ScrapeRequest, ScrapeResponse


def test_scrape_request():
    req = ScrapeRequest()
    assert req.min_rate_per_day == 600
    assert req.location == "SF Bay Area"


def test_scrape_response():
    resp = ScrapeResponse(jobs_found=10, jobs_qualified=3)
    assert resp.jobs_found == 10
