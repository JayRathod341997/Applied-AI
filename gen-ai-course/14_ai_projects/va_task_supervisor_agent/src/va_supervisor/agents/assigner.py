from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from typing import Dict, List
from ..config import settings
from ..utils.logger import logger
import json


ASSIGN_PROMPT = """Assign this task to the best VA based on skills match and workload.

Task:
Title: {title}
Priority: {priority}
Skills Required: {skills}
Estimated Hours: {hours}

VA Profiles:
{va_profiles}

Current Workloads:
{workloads}

Select the VA with the best skills match AND lowest current workload.
Return JSON:
{{
  "assigned_to": "<VA name>",
  "reasoning": "<why this VA>"
}}
"""


class AssignerAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model_name=settings.groq_model_primary,
            groq_api_key=settings.groq_api_key,
            temperature=0.2,
        )

    async def assign(
        self, task: Dict, va_profiles: List[Dict], workloads: Dict[str, float]
    ) -> Dict:
        profiles_text = "\n".join(
            f"- {p.get('name', 'Unknown')}: {p.get('skills', [])}" for p in va_profiles
        )
        workloads_text = "\n".join(f"- {k}: {v}hrs" for k, v in workloads.items())
        prompt = ASSIGN_PROMPT.format(
            title=task.get("title", ""),
            priority=task.get("priority", "medium"),
            skills=task.get("skills_required", []),
            hours=task.get("estimated_hours", 0),
            va_profiles=profiles_text,
            workloads=workloads_text,
        )
        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return json.loads(response.content)
        except Exception as e:
            logger.error(f"Assignment failed: {e}")
            return {"assigned_to": "Unassigned", "reasoning": f"Error: {e}"}
