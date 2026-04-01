# Remote Job Ops Engine - Interview Q&A

## Q1: Why classify roles with LLM instead of keyword matching?
**A:** Job titles vary wildly - "Customer Success Manager" is essentially a CSR role. The LLM understands semantic equivalence.

## Q2: How does resume tailoring work?
**A:** The resume generator takes the candidate's base profile and the specific job requirements, then rewrites the summary and reorders skills to match the job's priorities.

## Q3: What about PDF generation?
**A:** ReportLab generates professional PDFs from the LLM-generated content. Templates define the layout, and the LLM fills in the content sections.
