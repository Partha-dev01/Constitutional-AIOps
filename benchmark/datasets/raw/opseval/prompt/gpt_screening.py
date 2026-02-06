

screening_prompt = """
I need your help in analyzing a multi-choice question, determine the domain and the task type it belongs to.
Domains:
When classifying the domain, be specific, dive deeper into domains such as:
- Database
- Network Operations
Task Types:
For the task type, consider categories like:
- Monitoring and Alerts
- Performance Optimization
Summary your response as JSON format: {{"domain": "specific_domain", "task": "specific_task_type"}}

The question is:
{question}
"""
