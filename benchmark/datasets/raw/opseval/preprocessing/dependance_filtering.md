# Dependance Filtering

We filtered out the questions with extra context dependency by 2 parallel lists of keywords in the question stems and the responds of GPT-3.5-turbo, more details are provided below:

- For the question stems, we used empirical keywords to find the questions referencing extra context.
- In the meantime, we provided GPT-3.5-turbo with each question and asked it to determine if the question stem contains sufficient information for the LLMs to answer.
    - The keyword lists for selecting questions with failed question stems or failed responses are listed below:
        ```python
        question_keywords = ['the figure', 'the scenario', 'the previous question', r'question \d+' ]
        fail_pred_keywords = ['unclear', 'scenario is not provided', 'cannot be determined', 'none of the options', 'none of the given options']
        ```

-  After the keyword selection, we asked labelers to mannually check if the questions are indeed unable to answer. We have filtered out 59 questions with extra context dependency in total.
