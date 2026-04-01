# Grant & Funding Research - Interview Q&A

## Q1: How does the relevance scoring work?
**A:** The filter agent receives the grant listing and user criteria (veteran status, industry, minimum amount). It scores 0-100 based on how well the grant matches all criteria.

## Q2: How do you handle deduplication?
**A:** Each grant is hashed (title + source + deadline). Before adding to Notion, we check for existing hashes. New grants only are added.

## Q3: Why scrape Grants.gov instead of using their API?
**A:** Grants.gov's API has limited filtering capabilities. Scraping gives us access to full grant details including eligibility text that the API doesn't expose.
