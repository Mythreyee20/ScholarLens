# ScholarLens — Evaluation v0

**Evaluation date:** November 9, 2026  
**Dataset:** NSP scholarship guidelines and FAQ PDFs  
**Retrieval:** Sentence Transformers + PostgreSQL pgvector  
**Embedding model:** all-MiniLM-L6-v2  
**Retrieval limit:** Top 5 chunks  
**LLM used for evaluation:** Groq — openai/gpt-oss-120b

## Evaluation Questions and Results

| No. | Question | Result | Score |
|---|---|---|---:|
| 1 | What is the eligibility criteria for AICTE Pragati Scholarship? | Correct eligibility answer. Some retrieved citations were unrelated. | 8/10 |
| 2 | What is the family income limit for AICTE Pragati Scholarship? | Correctly answered ₹8 lakh per annum. Citation relevance needs improvement. | 8/10 |
| 3 | Who can apply for AICTE Saksham Scholarship? | Covered admission, disability, income and other scholarship restrictions. One unrelated citation. | 8.5/10 |
| 4 | What is the AICTE Swanath Scholarship? | Provided a detailed overview covering eligible categories, income limit, academic requirements and scholarship restrictions. One unrelated citation and citation-reference mismatch identified. | 8/10 |
| 5 | What documents are required for PM-USP CSSS? | Relevant information was not retrieved. The system correctly avoided inventing an answer. | 5/10 |
| 6 | What is the eligibility criteria for Top Class ST Scholarship? | Relevant information was not retrieved. Returned citations were unrelated. | 4/10 |
| 7 | Who can apply for Beedi Post Matric Scholarship? | Relevant information was not retrieved. Returned citations were unrelated. | 4/10 |
| 8 | What is the objective of Ishan Uday Scholarship? | Relevant PDF was retrieved, but the answer did not provide the objective. | 5/10 |
| 9 | What are the eligibility conditions for NMMSS? | Correctly covered academic marks, school type and selection test. Some unrelated citations. | 8/10 |
| 10 | What is the renewal procedure for a scholarship? | Provided renewal steps, but some conditions require scheme-specific verification. | 7/10 |

**Total Questions Evaluated:** 10  
**Average Evaluation Score:** 6.55/10

## Key Observations

### Strengths
- The system answers several scholarship eligibility questions correctly.
- Document names and page numbers are returned as citations.
- The LLM avoids making up answers when retrieved context is insufficient.
- Groq fallback provides successful responses when Gemini times out.

### Issues Identified
- Top-5 retrieval sometimes returns unrelated scholarship documents.
- Some relevant documents are retrieved, but the exact answer is missing from the selected chunks.
- Citation relevance needs improvement.
- Some general questions require scheme-specific context.
- Q4 returned a detailed answer, but one unrelated citation and citation-reference mismatch were identified.

### Planned Improvements
1. Improve retrieval relevance and ranking.
2. Evaluate different chunk sizes and overlap.
3. Improve citation selection.
4. Add more test questions for every scholarship.
5. Verify answers against the original guideline PDFs.

## Evaluation Note

Scores are provisional and based on the observed API responses and citation relevance. All 10 evaluation questions have been tested. This evaluation is an initial baseline, not a final accuracy benchmark.