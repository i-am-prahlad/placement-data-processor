# Changes to Be Implemented

Update the existing project according to the following requirements. Do not change any existing functionality unless explicitly specified below.

## 1. RAIT Sheet — Formatting

Apply the following changes to the final `RAIT` sheet:

1. The entire area of the RAIT sheet outside the populated data must remain **default Excel white** with the **default cell outlines**. Do not apply unnecessary fills or formatting to empty cells.

2. Set each column width based on the **longest value in that column** so that the complete value is visible.

3. **Do not wrap text.** No cell value should continue onto a second line.

4. Set row height to a maximum of **15 pixels**. Keep rows narrow; the default row height should be approximately **14.4**.

5. The header row must have:
   - **No fill**
   - **Bold**
   - **Black text**

6. All populated cells must have a **black border on all four sides**.

7. Empty cells outside the populated data area should retain normal/default Excel formatting.

8. The RAIT header row must **not contain filters**.

9. Values that represent numbers must be stored as actual **numeric Excel values**, not as text.

10. The **College Roll No.** column must be included in the RAIT sheet for searching, verification, and further processing.

11. The **College Roll No.** cells containing student roll numbers must have a **light red fill**.

12. The light red fill is intentional and must apply **only to the Roll No. data cells**, not the header or other columns.

13. The Roll No. column is an **internal-use column**. It must remain in the generated workbook so that TPC members can search for and perform further tasks using the student's roll number.

14. The Roll No. column is expected to be **removed manually before the RAIT data is sent/distributed further**. Do not delete it automatically during generation.

---

# 2. Removed Sheet

Update the `Remove` sheet as follows:

### 2.1 Final Schema

The removed-student entries must use the **same final schema as the RAIT sheet**, including the College Roll No. column, so that a removed student can be directly copied and inserted into the RAIT sheet if required.

Use this exact schema:

```text
Sr No, College Roll No., Name, Email Address, Mobile Number, Gender, Branch, College Name, Job Role (only if there are multiple job roles), 10th Percentage, 10th Year of Passing, 12th/Diploma?, 12th/Diploma Percentage, 12th Year of Passing, BE CGPA, BE Percentage, MTech CGPA (if given), MTech Percentage (if given), MTech Year of Passing (if given), Resume
```

Do not create a different student-data structure for removed students.

### 2.2 Roll Number

The **College Roll No.** must be retained in every relevant section of the `Remove` sheet.

The Roll No. column must also use the **light red fill** so that it is visually identifiable as an internal-use column.

The roll number must remain available for:

- Searching students.
- Verification.
- Matching.
- Manual processing.
- Copying a removed student back into the RAIT sheet if required.

Do not remove or hide the roll number.

### 2.3 Sections

The `Remove` sheet must:

- Have **no filters**.
- Be divided into separate sections.
- Keep the sections in exactly this order:

1. **Placed Student**
2. **Internship Students**
3. **Removed due to 10th Percentage**
4. **Removed due to 12th Percentage**
5. **Removed due to BE CGPA**
6. **Removed due to KT**

Each section should contain the same student-data schema described above.

### 2.4 Placement and Internship Information

For students removed because they are already placed or have an internship:

- First mention the **company/companies** they are placed at or interning at.
- Then provide the student's details using the expected final schema.

The information must be structured so that the student's row can be **directly copied and inserted into the RAIT sheet** if required.

Do not alter the student-data schema to accommodate the company information.

Instead, clearly identify the relevant company information before the student's corresponding details.

---

# 3. Final RAIT Schema

Use the following exact schema for the final `RAIT` sheet:

```text
Sr No, College Roll No., Name, Email Address, Mobile Number, Gender, Branch, College Name, Job Role (only if there are multiple job roles), 10th Percentage, 10th Year of Passing, 12th/Diploma?, 12th/Diploma Percentage, 12th Year of Passing, BE CGPA, BE Percentage, MTech CGPA (if given), MTech Percentage (if given), MTech Year of Passing (if given), Resume
```

The **College Roll No.** column is intentionally included for internal searching and processing.

The Roll No. column must be the **second column**, immediately after `Sr No`.

This is the same schema as before with the addition of **College Roll No.** and the existing spelling/capitalization changes.

Use this exact schema consistently throughout the output-generation process.

---

# 4. Streamlit App Changes

Remove all JSON-related functionality.

The application must **not require, generate, import, export, or use JSON configuration files** for this workflow.

All existing functionality should continue to work without the JSON functionality.

Do not replace the JSON functionality with another configuration-file system unless explicitly required.

---

# 5. Important Implementation Rules

- Do not modify the underlying eligibility logic unless explicitly instructed.
- Do not modify the existing processing order.
- Do not change the source data.
- Do not overwrite the uploaded/input workbooks.
- Preserve all existing functionality that is not specifically changed above.
- Apply the exact schema consistently.
- Keep College Roll No. in both `RAIT` and `Remove`.
- Apply a **light red fill only to populated Roll No. cells**.
- Do not apply the light red fill to the Roll No. header unless explicitly required.
- Keep Roll No. available for searching and verification.
- Do not automatically delete the Roll No. column.
- The Roll No. column is intended to be manually removed by the TPC team before the final data is distributed further.
- Ensure removed-student rows can be directly copied into the RAIT sheet without restructuring the student-data columns.
- Ensure the final Excel workbook is clean, copyable, and ready for TPC use.
- Prioritize correctness of the data over formatting.
- Do not invent missing information.