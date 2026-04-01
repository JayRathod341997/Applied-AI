from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TaskInput(BaseModel):
    title: str
    priority: str = "medium"
    due_date: str = ""
    skills_required: List[str] = []
    estimated_hours: float = 0


class AssignmentRequest(BaseModel):
    action: str = "assign_task"
    task: TaskInput


class Assignment(BaseModel):
    task_id: str = ""
    assigned_to: str = ""
    reasoning: str = ""
    current_workload: Dict[str, float] = {}


class AssignmentResponse(BaseModel):
    assignment: Assignment
    notifications: Dict[str, bool] = {}
    daily_digest: Dict[str, int] = {}
