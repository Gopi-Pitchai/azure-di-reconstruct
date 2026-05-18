# LinkedIn Post

When processing complex structured documents with LLMs, the standard approach covers
text quality, chunking, model selection, and prompt design.

What is often missed is document layout -- and in certain documents, layout carries
as much meaning as the text itself.

Stripping layout before passing content to the model was silently limiting accuracy.

Azure Document Intelligence gives you polygon coordinates for every paragraph -- exact
positions in inches. Using that data, you can reconstruct the original two-dimensional
layout before the text reaches the LLM.

Two columns stay as two columns. Headers stay centred. Isolated blocks stay isolated.

Result: accuracy went from 85% to 90%. Prompt iterations dropped from 8-10 to 1-2.

We packaged this into an open source library:

```
pip install azure-di-reconstruct
```

Full writeup on Medium -- link in comments.

---

DocumentAI | LLM | AzureAI | Python | NLP | MachineLearning | OpenSource
