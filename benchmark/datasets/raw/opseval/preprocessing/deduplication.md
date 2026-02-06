# Deduplication

Any repeated or highly similar questions are identified and removed to avoid redundancy in the test set. We calculate the cosine similarity of the question stems to detect duplicate questions and identify pairs of questions with a similarity above a certain threshold (th=0.7). These pairs are later manually reviewed to confirm if they are duplicates.