# Student Placement Data Processor — Build Specification

Act as an expert Python developer, data engineer, Excel automation specialist, and UI/UX designer.

Build a **modular, fast, reliable, and team-shareable web application** for processing student placement/internship eligibility data.

The application must use:

* **Python**
* **Streamlit** for the web UI
* **Pandas** for data processing
* **OpenPyXL** for Excel reading/writing and formatting
* **JSON** for drive-specific configuration
* **Pytest** for testing

Do **not** build the core system as VBA. Excel is the input/output format; Python is the processing engine.

\---

# 1\. APPLICATION OBJECTIVE

The application must allow a TPC team member to:

1. Upload the required Excel workbooks.
2. Configure eligibility criteria for the current placement drive.
3. Validate the uploaded data.
4. Process all students automatically.
5. Generate a clean Excel workbook.
6. Download the final workbook.

The user must not need to modify Python code, Excel formulas, or VBA.

The normal workflow should be:

**Upload → Configure → Validate → Preview → Process → Download**

\---

# 2\. INPUT WORKBOOKS

Support up to three Excel workbooks:

### A. Responses Workbook

Raw Google Forms/Google Sheets response data.

Relevant fields include:

* Timestamp
* Email address
* Full Name
* Email ID
* Mobile No
* Gender
* College Name
* College Roll No.
* Branch
* BTech Major/Minor Subject
* Job Role
* Degree
* 10th Percentage
* 10th Year of Passing
* 12th/Diploma?
* 12th/Diploma Percentage
* 12th/Diploma Year of Passing
* BTech CGPA
* BTech Percentage
* BTech Year of Passing
* Live KT
* Dead KT
* Drop
* Gap
* Are you placed?
* Company 1 Name
* Company 2 Name
* Resume
* Statement of Acknowledgement

### B. Studentwise Placement Workbook

Use:

* College Roll No.
* 1st Offer
* 2nd Offer
* 3rd Offer
* 4th Offer

Also preserve relevant student-identification fields.

### C. Studentwise Internship Workbook

Use it to determine whether students already have internships.

The internship workbook is optional.

\---

# 3\. IMPORTANT INPUT RULE

Never depend on fixed column positions.

Identify columns by **header names**.

Implement a header-normalization/mapping layer that can recognize minor variations such as:

* `College Roll No.`
* `College Roll No`
* `Roll No`
* `Roll Number`

Likewise support reasonable variations for Email, Mobile, Name, Timestamp, etc.

If a required field cannot be identified, stop processing and clearly show the missing field to the user.

Do not silently guess.

\---

# 4\. PROJECT STRUCTURE

Use a modular architecture similar to:

```text
placement\_data\_processor/
│
├── app.py
│
├── config/
│   ├── settings.py
│   └── output\_schema.py
│
├── core/
│   ├── loader.py
│   ├── validator.py
│   ├── normalizer.py
│   ├── deduplicator.py
│   ├── matcher.py
│   ├── placement.py
│   ├── eligibility.py
│   ├── internship.py
│   ├── removal\_logger.py
│   └── processor.py
│
├── output/
│   ├── workbook.py
│   └── formatter.py
│
├── utils/
│   ├── headers.py
│   ├── names.py
│   ├── phones.py
│   └── logging.py
│
├── tests/
│   ├── test\_duplicates.py
│   ├── test\_matching.py
│   ├── test\_placement.py
│   └── test\_eligibility.py
│
├── requirements.txt
└── README.md
```

Keep the processing engine independent from Streamlit.

The UI must call the processing engine rather than containing business logic.

\---

# 5\. CANONICAL DATA MODEL

After loading the input files, convert data into a standardized internal student structure.

Use normalized fields such as:

```text
roll\_no
name
email
mobile
gender
branch
college
job\_role
tenth\_percentage
tenth\_year
twelfth\_percentage
twelfth\_year
degree
be\_cgpa
be\_percentage
live\_kt
dead\_kt
drop
gap
resume
offer\_count
internship
eligibility\_status
removal\_reason
```

All downstream processing should operate on this standardized structure.

\---

# 6\. DUPLICATE HANDLING

Process duplicates before eligibility checks.

### Primary duplicate check

Use:

**College Roll No.**

If multiple responses exist for the same student:

* Compare Timestamp.
* Keep the latest submission.
* Remove earlier submissions.

### Secondary checks

After roll-number deduplication, check:

1. Email
2. Mobile number
3. Name

Do not automatically treat identical names as the same student.

Name-only matches must be flagged for review unless other information establishes that they are duplicates.

\---

# 7\. PLACEMENT MATCHING

Use **College Roll No.** as the primary matching identifier.

Determine offer count using:

* 1st Offer
* 2nd Offer
* 3rd Offer
* 4th Offer

Classify students as:

* No offer
* Single-placed — 1 offer
* Double-placed — 2 offers
* More than 2 offers

If roll-number matching is unavailable, use secondary matching only where safe.

Do not make uncertain matches silently.

\---

# 8\. DRIVE CONFIGURATION

Before processing, require the user to configure the current drive.

The application must provide these controls.

## Placement Rule

Allow the user to select:

* No offers allowed
* Single-placed students allowed
* Custom maximum offer count

Never assume the placement threshold.

Example:

```text
Maximum offers allowed: 0
```

means students with any offer are removed.

```text
Maximum offers allowed: 1
```

means students with one offer remain eligible and students with two or more offers are removed.

\---

# 9\. ACADEMIC ELIGIBILITY

Allow the user to select:

### Open

No academic restrictions.

OR

### Threshold

Require:

```text
10th Percentage: \_\_\_\_\_\_
12th/Diploma Percentage: \_\_\_\_\_\_
BTech/BE CGPA: \_\_\_\_\_\_
```

Apply each threshold independently.

If the company says:

**70% throughout**

use:

* 10th ≥ 70%
* 12th/Diploma ≥ 70%
* BTech/BE CGPA ≥ 7.0

If:

**65% throughout**

use:

* 10th ≥ 65%
* 12th/Diploma ≥ 65%
* BTech/BE CGPA ≥ 6.5

Do not invent additional academic rules.

\---

# 10\. KT / BACKLOG RULE

Allow the user to select:

```text
Live KTs allowed?
Yes / No
```

If `No`:

* Students with Live KT are removed.

Do not create additional rules for:

* Dead KT
* Drop
* Gap

unless explicitly configured by the user.

\---

# 11\. INTERNSHIP RULE

If an internship workbook is provided:

* Match students against it.
* Identify students with existing internships.

Allow the user to select:

```text
Remove existing internship students?
Yes / No
```

Do not remove internship students unless the user selects `Yes`.

\---

# 12\. PROCESSING ORDER

Follow this pipeline:

```text
1. Load workbooks
2. Detect and validate headers
3. Normalize data
4. Remove duplicate responses
5. Match placement records
6. Calculate offer count
7. Apply placement rule
8. Apply academic rules
9. Apply KT rule
10. Check internship
11. Log every removal
12. Generate final eligible dataset
13. Format Excel workbook
14. Provide download
```

Do not skip business-rule stages.

\---

# 13\. REMOVAL LOG

Every removed student must be recorded.

Never silently discard a student.

Create a worksheet named:

**Remove**

Include at minimum:

```text
Sr No
Name
College Roll No.
Branch
Removal Category
Removal Reason
Offer Count
```

Use categories:

* Duplicate
* Single placed
* Double placed
* Placement
* 10th eligibility
* 12th eligibility
* CGPA eligibility
* Live KT / backlog
* Internship
* Other

Record the exact reason.

Example:

```text
10th eligibility
10th percentage 62% < required 70%
```

\---

# 14\. AUDIT SHEET

Also create an **Audit** worksheet.

Include:

```text
Name
College Roll No.
Initial Status
Duplicate Status
Offer Count
Placement Status
10th Status
12th Status
CGPA Status
KT Status
Internship Status
Final Status
Final Reason
```

This sheet is for internal verification and troubleshooting.

\---

# 15\. PROCESSING SUMMARY

Create a **Run Info** worksheet containing:

```text
Processing Date
Input Response Count
Duplicate Count
Placement Removals
Academic Removals
KT Removals
Internship Removals
Final Eligible Count
```

Also show this summary in Streamlit before download.

Example:

```text
Total responses: 1,248
Duplicates removed: 51
Placement removals: 143
Academic removals: 72
KT removals: 18
Internship removals: 11

Final eligible: 953
```

\---

# 16\. PREVIEW BEFORE EXPORT

After processing, display a preview:

```text
PROCESSING PREVIEW

Total students:      XXXX
Duplicates:          XX
Placement removed:   XX
Academic removed:    XX
KT removed:          XX
Internship removed:  XX

Final eligible:      XXX
```

Provide:

**Generate Workbook**

Only after the user confirms should the final Excel workbook be generated.

\---

# 17\. FINAL RAIT SHEET

Create a worksheet named exactly:

**RAIT**

Use exactly these columns and this order:

```text
Sr no
Name
Email address
Mobile number
Gender
Branch
College name
Job role
10th percentage
10th yr of passing
12th/diploma?
12th/diploma percentage
12th year of passing
BE CGPA
BE percentage
MTech CGPA
MTech percentage
MTech Year of passing
Resume
```

Do not include College Roll No. in the final RAIT sheet.

If MTech data does not exist, leave those fields blank.

Only include Job Role when required by the configured output requirement.

\---

# 18\. FINAL DATA CLEANING

### Names

Convert names to Proper Case.

Example:

```text
PRAHLAD SINGH PANNU
```

becomes:

```text
Prahlad Singh Pannu
```

### Mobile numbers

Final mobile numbers must:

* Contain exactly 10 digits.
* Contain digits only.
* Have no leading zero.
* Have no country code.

Do not fabricate or guess invalid numbers.

If a number cannot be safely normalized, flag it rather than inventing digits.

### Sorting

Sort final RAIT records:

**Name A → Z**

### Resume

Convert valid resume URLs into functioning Excel hyperlinks.

Do not create fake URLs.

\---

# 19\. EXCEL FORMATTING

The final workbook must:

* Use Calibri, size 11.
* Have bold headers.
* Auto-fit columns.
* Apply borders to all populated cells.
* Center-align populated cells horizontally.
* Middle-align populated cells vertically.
* Remove inherited Google Sheets colours/tints.
* Use clean and consistent formatting.
* Preserve functioning hyperlinks.

Do not alter the raw input files.

\---

# 20\. PERFORMANCE REQUIREMENTS

Optimize for speed.

Use:

* Pandas vectorized operations.
* DataFrame merges.
* Dictionary/set lookups where appropriate.
* Indexed matching where useful.

Avoid nested row-by-row loops for large datasets.

Load each workbook once.

Do not repeatedly read the same Excel file.

The processing engine should remain fast even as the number of students increases.

\---

# 21\. VALIDATION

Before processing, validate:

* Required workbooks are present.
* Required headers exist.
* Roll numbers are usable.
* Timestamp exists for deduplication.
* Numeric fields are valid.
* Mobile numbers can be validated.
* Placement offer columns can be identified.
* Configuration values are valid.

Display clear errors.

Example:

```text
❌ Cannot process

Missing required column:
College Roll No.

Please upload a workbook containing this field.
```

Never silently continue when a critical field is missing.

\---

# 22\. ERROR HANDLING

The application must never crash because of one malformed student record.

Handle:

* Missing values
* Invalid percentages
* Invalid CGPA
* Invalid mobile numbers
* Missing resume URLs
* Duplicate records
* Unexpected column names
* Missing optional workbooks
* Empty cells
* Excel formatting issues

Where possible, flag the problematic records and continue safely.

Never fabricate missing data.

\---

# 23\. CONFIGURATION DESIGN

Do not hard-code drive-specific eligibility rules into the processing modules.

Represent rules separately, for example:

```python
rules = {
    "placement": {
        "max\_offers": 0
    },
    "academic": {
        "mode": "threshold",
        "tenth": 70,
        "twelfth": 70,
        "cgpa": 7.0
    },
    "live\_kt": {
        "allowed": False
    },
    "internship": {
        "remove": True
    }
}
```

The same application must work for different placement drives by changing configuration rather than changing source code.

\---

# 24\. STREAMLIT UI

Create a clean interface with these sections:

## Step 1 — Upload Files

```text
Responses Workbook
\[Upload]

Studentwise Placement Workbook
\[Upload]

Studentwise Internship Workbook
\[Upload - Optional]
```

## Step 2 — Drive Rules

Configure:

* Placement rule
* Academic rule
* Live KT rule
* Internship rule

## Step 3 — Validate

Show:

* Detected columns
* Record counts
* Warnings
* Errors

## Step 4 — Process

Button:

**Process Data**

## Step 5 — Preview

Show processing statistics and a small preview of eligible students.

## Step 6 — Export

Button:

**Download Final Workbook**

\---

# 25\. TEAM-SHARING REQUIREMENT

The application must be designed so that team members do not need to install Python or understand the code.

Prefer deploying the Streamlit application centrally.

The application should have:

* One shared codebase.
* One processing engine.
* One consistent version.
* No local Excel macros.
* No manual formulas.
* No manual code modification for individual drives.

All teammates should use the same application.

\---

# 26\. SECURITY / DATA HANDLING

Student information is sensitive.

Therefore:

* Do not log student personal information unnecessarily.
* Do not expose uploaded workbooks publicly.
* Do not store uploaded files permanently unless explicitly required.
* Process files in memory or temporary storage where practical.
* Delete temporary files after processing.
* Do not send student data to external APIs.
* Do not use external AI services for student matching or eligibility decisions.
* Keep raw input files unchanged.

\---

# 27\. TESTING

Create automated tests for at least:

### Deduplication

* Same roll number → latest timestamp survives.
* Earlier submission is removed.

### Placement

* 0 offers.
* 1 offer.
* 2 offers.
* More than 2 offers.

### Academic

* Exactly at threshold.
* Below threshold.
* Open eligibility.
* Missing values.

### KT

* Live KT with rule enabled.
* Live KT with rule disabled.

### Internship

* Internship removal enabled.
* Internship removal disabled.

### Matching

* Exact roll-number match.
* Email fallback.
* Mobile fallback.
* Ambiguous name match.

### Output

* Exact RAIT column order.
* Correct sorting.
* Correct formatting.
* Correct hyperlink generation.

\---

# 28\. NON-NEGOTIABLE DATA RULES

Never:

* Invent student information.
* Invent eligibility criteria.
* Assume placement thresholds.
* Assume internship-removal rules.
* Assume missing values.
* Overwrite raw input files.
* Match students solely by name when ambiguity exists.
* Silently remove students.
* Silently ignore validation errors.
* Depend on fixed Excel column positions.

Always:

* Prefer College Roll No. for matching.
* Keep the latest duplicate response based on Timestamp.
* Record every removal and its reason.
* Preserve missing information as blank when it cannot be safely determined.
* Keep business rules configurable.
* Keep processing and UI modules separate.

\---

# 29\. DELIVERABLES

Build the complete working project with:

```text
app.py
config/
core/
output/
utils/
tests/
requirements.txt
README.md
```

The README must explain:

1. Installation.
2. How to run locally.
3. How to use the application.
4. Project architecture.
5. Configuration.
6. How to add/change eligibility rules.
7. How to deploy for the TPC team.

The final application must be production-oriented, modular, maintainable, and suitable for repeated use across different placement drives.

Do not create a monolithic script.

Do not put all logic into `app.py`.

The final user experience should be:

**Upload files → Configure rules → Validate → Process → Review → Download Excel.**

