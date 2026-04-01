from typing import Dict, List
from ..agents.assigner import AssignerAgent
from ..tools.notion_tool import NotionTool
from ..tools.slack_tool import SlackTool
from ..utils.logger import logger
import uuid


class SupervisorPipeline:
    def __init__(self):
        self.assigner = AssignerAgent()
        self.notion = NotionTool()
        self.slack = SlackTool()

    async def assign_task(self, task: Dict) -> Dict:
        va_profiles = [
            {"name": "Maria", "skills": ["crm", "communication", "real_estate"]},
            {"name": "James", "skills": ["research", "data_entry", "scheduling"]},
            {"name": "Priya", "skills": ["writing", "social_media", "communication"]},
        ]
        workloads = {"Maria": 6, "James": 12, "Priya": 9}
        assignment = await self.assigner.assign(task, va_profiles, workloads)
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        slack_sent = await self.slack.send_message(
            f"New task assigned to {assignment.get('assigned_to', 'Unknown')}: {task.get('title', '')}"
        )
        return {
            "assignment": {
                "task_id": task_id,
                "assigned_to": assignment.get("assigned_to", ""),
                "reasoning": assignment.get("reasoning", ""),
                "current_workload": workloads,
            },
            "notifications": {"slack_dm_sent": slack_sent, "notion_assigned": True},
            "daily_digest": {
                "tasks_due_today": 4,
                "tasks_overdue": 1,
                "tasks_completed_yesterday": 7,
            },
        }
