# VA Task Supervisor - Interview Q&A

## Q1: How does the LLM decide task assignment?
**A:** The assigner agent receives the task requirements (skills, priority, hours) alongside VA profiles and current workloads. It weighs skills match against workload balance to find the optimal assignee.

## Q2: What if all VAs are overloaded?
**A:** The system flags the situation and suggests deferring lower-priority tasks. It can also recommend splitting larger tasks across multiple VAs.

## Q3: How do you track workload?
**A:** Each VA's current workload is calculated from assigned tasks' estimated hours. When a task is completed, the hours are deducted. This is tracked in the Notion VA Profiles database.

## Q4: How does the daily digest work?
**A:** APScheduler triggers a daily summary at 8 AM showing tasks due today, overdue items, and yesterday's completions. Sent via email using SendGrid.
