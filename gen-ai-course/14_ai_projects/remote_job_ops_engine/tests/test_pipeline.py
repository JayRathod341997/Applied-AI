import pytest
from remote_job_ops.models import PipelineRequest, PipelineResponse


def test_pipeline_request():
    req = PipelineRequest()
    assert req.role_types == ["CSR", "Admin", "VA"]
    assert req.max_applications == 10


def test_pipeline_response():
    resp = PipelineResponse(listings_scraped=50, roles_classified={"CSR": 10})
    assert resp.listings_scraped == 50
