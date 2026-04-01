# EP Job Application Agent - Interview Q&A

## Q1: How does the scraping work?
**A:** Playwright loads job board pages in a headless browser, extracts listing data via BeautifulSoup, and returns structured job objects. The scraper handles pagination and rate limiting.

## Q2: Why use LLM for filtering instead of SQL queries?
**A:** Job descriptions use varied language. "Executive Protection Agent" and "Close Protection Officer" are the same role. The LLM understands semantic equivalence that regex can't capture.

## Q3: How are duplicate applications prevented?
**A:** Each job is hashed (title + company + location). Before applying, we check the Notion database for matching hashes. If found, the job is skipped.
