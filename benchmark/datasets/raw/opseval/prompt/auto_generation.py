auto_generation_prompt = """
As an operations engineer, your task is to transform the content from a textbook into a knowledge-based question. 
The question should be based solely on the content from textbook, without excessive external knowledge; 
it should consist of a single concise sentence without excessive length and phrased as deductive question.
content: {content} question: {question}
"""