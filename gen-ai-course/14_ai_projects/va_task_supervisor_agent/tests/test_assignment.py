import pytest
from va_supervisor.models import AssignmentRequest, TaskInput


def test_task_input():
    task = TaskInput(
        title="Follow up with leads",
        priority="high",
        skills_required=["crm", "communication"],
    )
    assert task.title == "Follow up with leads"
    assert task.priority == "high"


def test_assignment_request():
    req = AssignmentRequest(task=TaskInput(title="Test task"))
    assert req.action == "assign_task"
