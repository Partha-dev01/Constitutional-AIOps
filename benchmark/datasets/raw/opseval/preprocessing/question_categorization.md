# Question Categorization

In the complex landscape of Ops, recognizing the multidimensional nature of tasks is essential. We devise a categorization that captures many tasks that professionals confront in practical applications. The categorization process consists of two steps: automated screening and manual review. 

We first use GPT-4 for topic modeling to gain rough insights about the dataset, leveraging its capabilities to determine the relevance of each question to Ops. The topic modeling resulted in more than 20 tasks but had an imbalanced distribution. The prompt we used to let GPT-4 do the categorization is in [prompt/gpt_screening.py](../prompt/gpt_screening.py)

Secondly, during the [manual review](manual_review.md) process, we involved dozens of experts in manual screening. By merging similar tasks and labeling different ability levels, we categorize the questions into eight tasks and three ability levels, respectively. Check out the final distribution in [Dataset Distribution](../docs/dataset_distribution.md).