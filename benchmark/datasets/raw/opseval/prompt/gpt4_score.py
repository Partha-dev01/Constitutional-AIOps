score_prompt = """
As an operations engineer, your task is to score an output of a model to a Ops question.
{question}
Answer: {keypoint}
Explanation: {reference}
Output of a model: {prediction}
Give a score between 1 to 10 without any other outputs according to the answer and explanation.
"""