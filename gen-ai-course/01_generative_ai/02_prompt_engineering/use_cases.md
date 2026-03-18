# Prompt Engineering - Use Cases by Domain

This document provides practical prompt engineering examples across various industries and functional areas. Each use case demonstrates the difference between vague prompts and well-crafted prompts using best practices from the concepts.md file.

---

## Table of Contents

1. [Healthcare](#1-healthcare)
2. [Finance](#2-finance)
3. [Human Resources (HR)](#3-human-resources-hr)
4. [Writing Proposals](#4-writing-proposals)
5. [Education](#5-education)
6. [Learning & Development](#6-learning--development)
7. [Marketing](#7-marketing)
8. [Legal](#8-legal)
9. [Sales](#9-sales)

---

## 1. Healthcare

### Problem Statement

A healthcare provider needs to generate patient-friendly explanations of medical test results. Medical terminology is often confusing for patients, but accuracy is critical since misinterpretation could lead to improper self-treatment or delayed care.

### Dataset Link

- [Medical Questions Dataset](https://huggingface.co/datasets/medical_dialog)
- [HealthFinder API](https://health.gov/myhealthfinder/)

### Vague Prompt

```
Prompt: Explain this blood test result to a patient.
Result: "The test shows elevated levels. This could indicate various conditions. Please consult your doctor."
```

**Issues with vague prompt:**
- No specific test parameters provided
- Doesn't define patient's knowledge level
- No actionable next steps
- Uses vague language ("various conditions")

### Enhanced Prompt (Best Practices)

```
Role: You are a compassionate healthcare communicator with 15 years of experience explaining medical results to patients.

Task: Explain the following blood test results in patient-friendly language.

Context: The patient is a 45-year-old adult with no medical background. They received these results from their annual physical exam.

Format: Use the following structure:
1. What the test measures (simple terms)
2. Their specific results with normal ranges
3. What the results mean in plain English
4. Any lifestyle recommendations (if applicable)
5. Questions to ask their doctor

Constraints:
- Use layperson's terms, avoid medical jargon
- Be encouraging but honest
- Do not diagnose or suggest treatment
- Highlight any values that need urgent attention

Test Results:
- Hemoglobin: 14.5 g/dL (Normal: 12.0-16.0)
- Fasting Glucose: 112 mg/dL (Normal: 70-100)
- LDL Cholesterol: 145 mg/dL (Normal: <100)
- HDL Cholesterol: 55 mg/dL (Normal: >40)
```

### Dos and Don'ts with AI in Healthcare

| ✅ Do | ❌ Don't |
|-------|---------|
| Use AI for patient education, not diagnosis | Diagnose conditions or prescribe treatments |
| Always include disclaimer to consult professionals | Share unverified medical information |
| Verify medical facts with authoritative sources | Rely solely on AI for critical health decisions |
| Consider patient literacy levels | Use complex medical terminology without explanation |
| Include citations when possible | Make definitive health claims without evidence |

### Real World Risk Scenario

**Risk:** A patient uses AI-generated health information to self-diagnose and delays visiting a doctor, leading to progression of a serious condition like cancer.

**Mitigation:**
- Always include clear disclaimers
- Prompt users to verify with healthcare providers
- Include urgency indicators in responses
- Never provide definitive diagnoses

---

## 2. Finance

### Problem Statement

A financial advisor needs to create personalized investment recommendations for clients. The AI must consider risk tolerance, financial goals, and market conditions while remaining compliant with financial regulations.

### Dataset Link

- [Yahoo Finance Dataset](https://finance.yahoo.com/)
- [SEC Financial Statement Data](https://www.sec.gov/dera/data/financial-statement-data-sets.html)

### Vague Prompt

```
Prompt: Give me investment advice for retirement.
Result: "Consider diversifying your portfolio with stocks, bonds, and real estate. Past performance doesn't guarantee future results."
```

**Issues with vague prompt:**
- No information about client's age, income, or timeline
- Doesn't specify retirement goals
- Ignores current portfolio composition
- No risk tolerance assessment

### Enhanced Prompt (Best Practices)

```
Role: You are a Certified Financial Planner (CFP) with expertise in retirement planning and portfolio management.

Task: Create a personalized investment strategy for retirement planning.

Context: Client Profile:
- Age: 35 years old
- Annual Income: $85,000
- Current Retirement Savings: $50,000
- Monthly Contribution Capacity: $1,000
- Target Retirement Age: 65
- Risk Tolerance: Moderate (can accept 10-15% portfolio volatility)
- Existing Portfolio: 60% stocks, 40% bonds
- Employer 401(k) Match: 4% (currently contributing 6%)

Market Context (as of 2024):
- Current bull market with elevated valuations
- Interest rates stabilizing
- Inflation moderating from peak

Format: Provide:
1. Asset allocation recommendation with rationale
2. Specific fund categories to consider
3. Annual contribution strategy
4. Milestone checkpoints (ages 40, 50, 55, 60)
5. Important disclaimers

Constraints:
- Follow fiduciary standard
- Include appropriate regulatory disclosures
- Recommend diversified, low-cost index funds where appropriate
- Consider tax-advantaged accounts priority
- Do not recommend specific individual stocks
```

### Dos and Don'ts with AI in Finance

| ✅ Do | ❌ Don't |
|-------|---------|
| Include comprehensive disclaimers | Provide specific stock recommendations |
| Consider regulatory requirements (SEC, FINRA) | Promise specific returns or performance |
| Factor in client's complete financial picture | Ignore tax implications |
| Recommend diversification | Over-concentrate in any single asset |
| Suggest professional consultation | Provide legal/tax advice beyond scope |

### Real World Risk Scenario

**Risk:** AI recommends aggressive investment strategy to someone who actually has low risk tolerance, causing significant emotional distress and financial loss during a market downturn.

**Mitigation:**
- Always verify risk tolerance through detailed assessment
- Include stress-test scenarios in recommendations
- Require human review before final advice delivery
- Include strong volatility disclaimers

---

## 3. Human Resources (HR)

### Problem Statement

An HR department needs to generate job descriptions that attract qualified candidates while avoiding biased language that could deter diverse applicants. The descriptions must be both compelling and compliant with employment laws.

### Dataset Link

- [LinkedIn Job Posts Dataset](https://www.linkedin.com/)
- [O*NET Database](https://www.onetcenter.org/)

### Vague Prompt

```
Prompt: Write a job description for a software developer.
Result: "We need a software developer. You should know how to code. Good salary and benefits."
```

**Issues with vague prompt:**
- No specific requirements or qualifications
- Missing key responsibilities
- No information about benefits or culture
- Doesn't specify seniority level
- Biased language not considered

### Enhanced Prompt (Best Practices)

```
Role: You are an HR professional with 10 years of experience in talent acquisition and job description writing.

Task: Write a comprehensive, inclusive job description for a Software Engineer position.

Context:
- Company: Mid-size tech startup (150 employees)
- Location: Remote-first (US-based)
- Team: 8-person engineering team
- Tech Stack: Python, React, AWS
- Salary Range: $120,000-$160,000 + equity
- Experience Level: Mid-level (3-5 years)

Format: Include:
1. Engaging job title
2. About the company section
3. What you'll do (5-7 bullet points)
4. What we're looking for (required vs preferred)
5. Benefits and perks
6. Equal opportunity statement

Constraints:
- Use inclusive, gender-neutral language
- Avoid age-biased terms ("young", "energetic")
- Focus on essential job functions
- Include remote work considerations
- Comply with EEOC guidelines
- Do not include unnecessary credential requirements
- Use action-oriented, engaging language
```

### Dos and Don'ts with AI in HR

| ✅ Do | ❌ Don't |
|-------|---------|
| Use inclusive, bias-free language | Include age, gender, or ethnicity indicators |
| Focus on essential qualifications | Add unnecessary degree requirements |
| Include equal opportunity statements | Imply preference for certain backgrounds |
| Consider accessibility requirements | Ignore ADA compliance |
| Be specific about requirements | Use vague terms like "young and dynamic" |

### Real World Risk Scenario

**Risk:** A biased job description attracts litigation under Title VII or leads to a homogeneous workforce, missing out on diverse talent that drives innovation.

**Mitigation:**
- Review all AI-generated content for bias
- Include legal review for compliance
- Test descriptions with diverse focus groups
- Document hiring criteria objectively

---

## 4. Writing Proposals

### Problem Statement

A consulting firm needs to generate compelling project proposals that address client needs, demonstrate expertise, and win business. Each proposal must be tailored to the specific client while maintaining consistency in quality and format.

### Dataset Link

- [Proposal Sample Dataset](https://www.scribd.com/)
- [Business Writing Templates](https://www.britishcouncil.org/)

### Vague Prompt

```
Prompt: Write a proposal for a digital transformation project.
Result: "We can help you with your digital transformation. We have experienced team. Contact us for more details."
```

**Issues with vague prompt:**
- No client-specific context
- Doesn't address specific pain points
- No measurable objectives
- Missing deliverables or timeline
- No differentiation from competitors

### Enhanced Prompt (Best Practices)

```
Role: You are a Senior Management Consultant with expertise in digital transformation and proposal writing.

Task: Write a compelling consulting proposal for a digital transformation engagement.

Context:
Client: Regional healthcare system with 12 hospitals
Current Challenges:
- Legacy electronic health record (EHR) system
- Data silos between departments
- Manual patient scheduling processes
- Limited real-time analytics capabilities

Project Goals:
- Modernize patient data infrastructure
- Implement integrated data analytics
- Reduce patient wait times by 30%
- Improve staff productivity by 20%

Our Differentiators:
- Healthcare-specific expertise (50+ similar projects)
- Certified implementation partners with major cloud providers
- Fixed-price delivery model with risk mitigation guarantees

Format:
1. Executive Summary (1 page max)
2. Understanding Your Challenges
3. Our Proposed Solution (phased approach)
4. Timeline and Milestones
5. Team and Expertise
6. Investment and ROI
7. Next Steps

Constraints:
- Use healthcare industry terminology appropriately
- Include specific, measurable outcomes
- Balance professionalism with compelling language
- Address regulatory considerations (HIPAA)
- Show understanding of healthcare-specific challenges
```

### Dos and Don'ts with AI in Proposal Writing

| ✅ Do | ❌ Don't |
|-------|---------|
| Personalize to client needs | Use generic, copy-paste content |
| Include specific metrics and timelines | Make vague promises |
| Showcase relevant experience | Exaggerate capabilities |
| Address client objections proactively | Ignore competitive landscape |
| Include clear call-to-action | Leave next steps unclear |

### Real World Risk Scenario

**Risk:** Overpromising on capabilities leads to failed delivery, damaged client relationships, and potential legal disputes over contract terms.

**Mitigation:**
- Verify all claims are achievable
- Include clear scope boundaries
- Document assumptions and dependencies
- Build in contingency plans

---

## 5. Education

### Problem Statement

An educator needs to create differentiated learning materials that accommodate various learning styles and student ability levels. The content must be engaging, accurate, and appropriate for the target age group.

### Dataset Link

- [Kaggle Education Datasets](https://www.kaggle.com/datasets)
- [OpenStax Textbooks](https://openstax.org/)

### Vague Prompt

```
Prompt: Create math worksheets for grade 5.
Result: "Here are some math problems for grade 5 students. Include addition, subtraction, multiplication and division."
```

**Issues with vague prompt:**
- No specific topics or standards alignment
- Doesn't consider student ability range
- Missing learning objectives
- No differentiation strategy
- No answer key

### Enhanced Prompt (Best Practices)

```
Role: You are an experienced Elementary Education Teacher with expertise in differentiated instruction and curriculum development.

Task: Create a comprehensive math worksheet set for Grade 5 students covering fractions.

Context:
- Topic: Adding and Subtracting Fractions (Common Core Standard 5.NF.A.1, 5.NF.A.2)
- Class Profile: 25 students with mixed abilities
  - 5 students need additional scaffolding
  - 15 are at grade level
  - 5 students need enrichment
- Previous Learning: Students understand basic fraction concepts (numerator, denominator, equivalent fractions)
- Time Available: 45-minute lesson

Format: Create THREE differentiated versions:

Level 1 (Scaffolded):
- Visual models included
- Step-by-step instructions
- Simpler denominators (same denominator first)
- Word problems with real-world contexts

Level 2 (Grade Level):
- Mixed denominators with visual aids
- Standard word problems
- Connection to real-world scenarios

Level 3 (Enrichment):
- Multi-step problems
- Fraction operations with improper fractions
- Extension to mixed numbers

For each level include:
- Learning objective
- 8-10 problems
- Answer key
- Teaching tips

Constraints:
- Use grade-appropriate language
- Include visual representations where helpful
- Align with Common Core standards
- Make problems engaging and contextual
```

### Dos and Don'ts with AI in Education

| ✅ Do | ❌ Don't |
|-------|---------|
| Align with educational standards | Create content with factual errors |
| Include differentiation strategies | Use one-size-fits-all approaches |
| Consider developmental appropriateness | Include content that's too mature |
| Provide answer keys | Ignore accessibility needs |
| Include multiple learning modalities | Over-rely on text-only content |

### Real World Risk Scenario

**Risk:** Incorrect educational content teaches students wrong concepts, leading to foundational learning gaps that are difficult to correct.

**Mitigation:**
- Verify all factual content
- Cross-reference with authoritative sources
- Have subject matter experts review
- Include clear error reporting mechanism

---

## 6. Learning & Development

### Problem Statement

An L&D team needs to create corporate training materials that effectively upskill employees. The content must be engaging, practical, and measurable against business outcomes.

### Dataset Link

- [Coursera Course Data](https://www.coursera.org/)
- [edX Dataset](https://www.edx.org/)

### Vague Prompt

```
Prompt: Create training on leadership skills.
Result: "This training will cover leadership. Be a good leader. Communicate with your team."
```

**Issues with vague prompt:**
- No specific leadership framework
- Doesn't define learning objectives
- Missing practical application
- No assessment criteria
- Not tailored to organizational context

### Enhanced Prompt (Best Practices)

```
Role: You are a Corporate Learning & Development Specialist with expertise in leadership development and instructional design.

Task: Create a comprehensive leadership training module on "Coaching for High Performance."

Context:
- Target Audience: First-time managers (0-2 years in role)
- Company: Technology company (500 employees)
- Delivery Format: 2-hour virtual workshop + pre-work
- Previous Training: "Foundations of Leadership" (completed)

Learning Objectives (Bloom's Taxonomy):
By end of session, participants will be able to:
1. Identify key differences between managing and coaching
2. Apply the GROW coaching model in common scenarios
3. Demonstrate active listening techniques
4. Create development plans for direct reports

Business Case:
- Improve manager-employee engagement scores by 15%
- Reduce voluntary turnover among high-performers by 10%

Format:
1. Pre-work Assignment (30 min)
   - Self-assessment: Current coaching habits
   - Video: Introduction to coaching mindset

2. Workshop Structure (2 hours)
   - Opening: Why Coaching Matters (15 min)
   - Concept: The Coaching Mindset (20 min)
   - Practice: GROW Model Application (45 min)
   - Demo: Active Listening Techniques (15 min)
   - Action: Development Plan Creation (20 min)
   - Closing: Commitment & Next Steps (5 min)

3. Post-Training
   - 30-day coaching challenge
   - Peer coaching partnership

Constraints:
- Include practical exercises and role-plays
- Provide Facilitator Guide with timing
- Include Participant Materials (handouts, worksheets)
- Add icebreakers and energizers
- Reference real workplace scenarios
- Include assessment/quiz questions
```

### Dos and Don'ts with AI in L&D

| ✅ Do | ❌ Don't |
|-------|---------|
| Align with business objectives | Create content without clear outcomes |
| Include interactive elements | Use lengthy passive content |
| Provide practical tools and templates | Focus only on theory |
| Include assessment and feedback loops | Ignore adult learning principles |
| Consider multiple learning styles | Create text-heavy content only |

### Real World Risk Scenario

**Risk:** Inadequate training leads to manager errors that cause employee turnover, productivity loss, or compliance issues.

**Mitigation:**
- Pilot training with representative group
- Gather feedback and iterate
- Measure business impact post-training
- Provide ongoing support resources

---

## 7. Marketing

### Problem Statement

A marketing team needs to create compelling content across multiple channels while maintaining brand consistency. The AI must adapt messaging to different platforms and audience segments while optimizing for engagement.

### Dataset Link

- [Marketing Database Kaggle](https://www.kaggle.com/datasets)
- [Ad Dataset](https://www.adscience.nl/)

### Vague Prompt

```
Prompt: Write promotional content for our new product.
Result: "Introducing our amazing new product! It's the best. Buy now!"
```

**Issues with vague prompt:**
- No product details provided
- Doesn't identify target audience
- Missing unique value proposition
- No platform specifications
- No call-to-action clarity

### Enhanced Prompt (Best Practices)

```
Role: You are a Senior Marketing Content Strategist with expertise in B2B SaaS and multi-channel campaigns.

Task: Create a comprehensive content package for launching a new project management software.

Context:
Product: "TaskFlow Pro" - AI-powered project management for remote teams
- Key Features:
  - Intelligent task allocation based on team capacity
  - Automated progress tracking with predictive analytics
  - Integrated video conferencing and collaboration tools
  - Time zone-aware scheduling

Target Audience:
- Primary: Remote team leads, Project managers (25-45 age group)
- Secondary: Startup founders, Operations managers

Campaign Goals:
- Generate 5,000 qualified leads
- Achieve 15% email open rate
- Drive 500 trial sign-ups

Platform Requirements:
1. Landing Page (hero section + value proposition)
2. Email Sequence (3 emails: teaser, launch, CTA)
3. LinkedIn Post (professional, thought leadership)
4. Twitter/X Thread (casual, engaging)
5. Facebook Ad Copy (attention-grabbing)

Brand Voice:
- Professional yet approachable
- Innovative but not jargon-heavy
- Empathetic to remote work challenges
- Confident but not arrogant

Format: Provide each piece with:
- Headline/Opening hook
- Body copy (platform-appropriate length)
- Call-to-action
- Suggested visuals (describe)

Constraints:
- Highlight AI/automation benefits without being technical
- Include social proof elements
- A/B test variations where applicable
- Comply with platform ad policies
```

### Dos and Don'ts with AI in Marketing

| ✅ Do | ❌ Don't |
|-------|---------|
| Maintain brand consistency | Generate generic, templated content |
| Target specific audience segments | Use one message for all audiences |
| Include clear CTAs | Leave conversion path unclear |
| Optimize for platform algorithms | Copy-paste without adaptation |
| Test and iterate based on data | Ignore performance metrics |

### Real World Risk Scenario

**Risk:** Misleading marketing claims lead to customer dissatisfaction, refunds, and potential regulatory action (FTC violations).

**Mitigation:**
- Legal review of all claims
- Ensure product capabilities match messaging
- Include appropriate disclaimers
- Document substantiation for claims

---

## 8. Legal

### Problem Statement

Legal teams need to draft various documents efficiently while ensuring accuracy and compliance. AI assistance can accelerate drafting but must maintain rigorous standards for legal validity.

### Dataset Link

- [CourtListener Dataset](https://www.courtlistener.com/)
- [Legal Information Institute](https://www.law.cornell.edu/)

### Vague Prompt

```
Prompt: Write a non-disclosure agreement.
Result: "This agreement is between two parties. They agree not to share confidential information. Both parties sign here."
```

**Issues with vague prompt:**
- No parties identified
- Missing critical legal terms
- No jurisdiction specified
- Doesn't define confidential information
- No enforcement mechanisms
- Missing essential contract elements

### Enhanced Prompt (Best Practices)

```
Role: You are a Corporate Attorney with 15 years of experience in commercial contracts and intellectual property law.

Task: Draft a comprehensive Mutual Non-Disclosure Agreement (MNDA) for a potential business partnership.

Context:
- Disclosing Party: TechStart Inc., a Delaware corporation (AI software company)
- Receiving Party: EnterpriseCo LLC, a California limited liability company (enterprise consulting firm)
- Purpose: Evaluate potential partnership for co-developing AI-powered consulting solutions
- Duration: 3 years (with confidentiality surviving for 5 years)
- Jurisdiction: State of Delaware

Required Elements:
1. Definition of Confidential Information
   - Include exclusions (publicly available, independently developed, etc.)
   
2. Obligations of Receiving Party
   - Protection standards
   - Permitted disclosures
   
3. Permitted Disclosures
   - Legal requirements
   - Need-to-know basis
   
4. Term and Termination
   - Survival clauses
   
5. Return/Destruction of Information
   
6. Intellectual Property Rights
   - No license implied
   
7. Remedies
   - Injunctive relief
   - No warranty disclaimer
   
8. General Provisions
   - Entire agreement
   - Amendment
   - Waiver
   - Severability
   - Assignment
   - Notices

Format: Provide:
- Proper legal structure and numbering
- Defined terms section
- Execution blocks for both parties

Constraints:
- Follow standard legal drafting conventions
- Include placeholder for dates
- Add bracketed sections requiring customization
- Include Jurat language for notarization (optional)
- Note: "This is a template and should be reviewed by legal counsel"
```

### Dos and Don'ts with AI in Legal

| ✅ Do | ❌ Don't |
|-------|---------|
| Include comprehensive disclaimers | Provide legal advice without qualification |
| Use precise legal terminology | Use layperson language in legal docs |
| Include jurisdiction-specific provisions | Ignore applicable laws |
| Provide template with customization notes | Generate "one-size-fits-all" documents |
| Recommend legal review | Rely solely on AI without expert review |

### Real World Risk Scenario

**Risk:** AI-generated legal document contains errors that void the agreement, leading to loss of IP protection, financial damages, or litigation.

**Mitigation:**
- Always require attorney review
- Maintain version control and audit trails
- Test critical provisions
- Keep human in the loop for execution

---

## 9. Sales

### Problem Statement

A sales team needs to personalize outreach at scale while maintaining authenticity. AI can help research prospects and craft messages, but must avoid generic templates that harm response rates.

### Dataset Link

- [Sales Dataset Kaggle](https://www.kaggle.com/datasets)
- [Apollo Sales Data](https://www.apollo.io/)

### Vague Prompt

```
Prompt: Write a cold email to a potential client.
Result: "Hi, I'd like to schedule a call to discuss how we can help your business. Let me know if you're interested."
```

**Issues with vague prompt:**
- No prospect information included
- Doesn't mention their company or role
- No specific value proposition
- Generic template feel
- No personalized hook

### Enhanced Prompt (Best Practices)

```
Role: You are an Enterprise SaaS Sales Development Representative with 7 years of experience in B2B technology sales.

Task: Write a personalized cold outreach email sequence for a prospective client.

Context:
Prospect Information:
- Name: Sarah Chen
- Title: VP of Operations
- Company: MedTech Solutions (200 employees, healthcare technology)
- Location: Boston, MA
- LinkedIn: Recently posted about expanding operations and数字化转型

My Product: AI-powered workflow automation platform
- Reduces manual processing time by 60%
- Integrates with Salesforce, HubSpot, ServiceNow
- Healthcare industry compliant (HIPAA-ready)
- Average ROI: 4.5x within first year

Trigger/Context: Saw their LinkedIn post about expanding operations and digital transformation initiatives

Email 1 - Initial Outreach (Goal: Book discovery call):
- Hook: Reference her specific challenge
- Value: One specific relevant case study
- CTA: 15-min discovery call

Email 2 - Follow-up (if no response after 4 days):
- Add new piece of social proof
- Address potential objection
- Lower the ask

Email 3 - Break-up (if no response after 7 more days):
- Offer value without asking
- Leave door open for future

Format for each email:
- Subject line (A/B test options)
- Opening hook (personalized)
- Body (3-4 sentences max)
- CTA
- Signature

Constraints:
- Keep emails under 150 words
- No attachments in first email
- Avoid spam triggers (no "free", "guarantee", excessive punctuation)
- Sound like a real person, not a robot
- Include personalization tokens
```

### Dos and Don'ts with AI in Sales

| ✅ Do | ❌ Don't |
|-------|---------|
| Research and personalize | Send generic, copy-paste messages |
| Include specific value proposition | Make vague benefit claims |
| Test and optimize subject lines | Ignore deliverability best practices |
| Follow up strategically | Bombard prospects with messages |
| Comply with CAN-SPAM/GDPR | Ignore cold outreach regulations |

### Real World Risk Scenario

**Risk:** Mass personalization leads to embarrassing errors (wrong company name, outdated role), damaging brand reputation and potentially violating regulations.

**Mitigation:**
- Implement verification step before sending
- Set up spam filter testing
- Review AI output for accuracy
- Track and respond to negative replies

---

## Summary: Key Takeaways

### Best Practices Across All Domains

1. **Provide Clear Context**: Always include relevant background information about the task, audience, and objectives.

2. **Use Role Prompting**: Assign a specific persona to get more targeted, expert-level outputs.

3. **Define Constraints Explicitly**: Specify format, length, tone, and any limitations upfront.

4. **Include Examples**: When possible, show the model what good output looks like.

5. **Iterate and Refine**: Test different prompt versions and refine based on outputs.

6. **Always Human Review**: AI output is a starting point, not final deliverable.

7. **Consider Risks**: Always think about what could go wrong and add appropriate disclaimers.

8. **Domain-Specific Caution**: Higher stakes domains (healthcare, legal, finance) require extra verification.
