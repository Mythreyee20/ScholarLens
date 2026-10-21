# ScholarLens

> Fill this top section from your Examate project card on Day 1. Replace every line in angle brackets.

## Problem
Students often struggle to understand scholarship guidelines because eligibility rules and application requirements are spread across multiple documents. They may be unsure about income limits, minimum marks, eligible courses, category rules, required documents, and renewal conditions. As a result, students may apply for unsuitable schemes or submit incorrect documents, leading to application rejections. Scholarship nodal officers also spend considerable time answering the same questions repeatedly. ScholarLens aims to make scholarship information easier to understand and help students check their eligibility before applying.

## Who it is for
   --- Students who want to identify scholarships they may be eligible for and understand their application requirements.
   
   --- Scholarship nodal officers at government arts and science colleges, especially officers who verify large numbers of National Scholarship Portal (NSP) applications.

## Signature feature

ScholarLens aims to convert lengthy scholarship guideline documents into structured JSON records and generate a simple, one-page eligibility checklist for each scheme. Students can use the checklist to review income limits, minimum marks, eligible courses, category rules, required documents, and renewal conditions before applying.

## Hardest problem (my interview story)

The hardest problem is extracting accurate and consistent information from different scholarship guidelines, as each scheme may have different eligibility conditions and application requirements. ScholarLens will use a fixed JSON schema to organize important fields, followed by field-by-field validation against manually prepared reference records. Even one incorrect value, such as an income limit or a required document, could mislead a student. The target is to achieve at least 95% field-level extraction accuracy across 80 scholarship scheme guidelines.

## Dataset
  The planned dataset includes official NSP scholarship scheme guidelines, FAQs, user manuals, and scholarship statistics datasets from data.gov.in.

| Source | Link | Documents | Pages | Licence / terms |
|---|---|---|---|---|
| National Scholarship Portal (NSP) | https://scholarships.gov.in/ | Student Application FAQ, OTR FAQ, Standard Operating Procedures (SOP), Institute FAQs, Institute KYC Registration Process, DNO/SNO Registration FAQs, and FaceAuth Manual | 17-page SOP, 8-page Institute FAQ, 25-page Institute KYC guide; other document page counts not fully verified | Official NSP documents; check the terms and conditions of each document before reuse |
| Open Government Data Platform India | https://www.data.gov.in/ | Scholarship statistics datasets (to be selected and collected) | Not applicable | Follow the licence and reuse conditions specified for each dataset |


## Dataset target: 
        At least 900 pages covering 80 or more scholarship scheme guidelines.

## 10 real questions
See [docs/QUESTIONS.md](docs/QUESTIONS.md).

## Run it
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                                 # Windows: copy .env.example .env
uvicorn app.main:app --reload
curl localhost:8000/health
```

## Live link
<Added in Week 2>
