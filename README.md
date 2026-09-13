# Student Placement Data Processor

Web application for TPC teams to turn student form responses and placement/internship workbooks into a clean eligibility list.

Python is the processing engine. Excel is only the input and output format. Drive rules are configured directly in the web UI, not in source code.

Typical flow:

**Upload → Configure → Validate → Process → Preview → Download**

## Quick Start (1-Click Launch)

Simply **double-click** the `Start_App.bat` file in the project folder.

It will automatically:
- Launch the Streamlit application.
- Automatically open your default web browser to `http://localhost:8501`.
- Display a server window that can be minimized or closed when done.

---

## 1. First-Time Setup (One-Time Only)

Requirements: **Python 3.10** or later.

1. Open a terminal (PowerShell / Command Prompt on Windows, or Terminal on macOS/Linux).
2. Navigate into the project folder:
   ```bash
   cd placement_data_processor
   ```
3. Create a Python virtual environment:
   ```bash
   python -m venv .venv
   ```
4. Activate the virtual environment:
   - **Windows (PowerShell):**
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
     *(If script execution is restricted on Windows PowerShell, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` first)*
   - **Windows (Command Prompt):**
     ```cmd
     .venv\Scripts\activate.bat
     ```
   - **macOS / Linux:**
     ```bash
     source .venv/bin/activate
     ```
5. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
6. (Optional) Verify tests pass:
   ```bash
   pytest
   ```

---

## 2. Routine Execution

### Method A — 1-Click Batch File (Windows)
Double-click **`Start_App.bat`**.

### Method B — Terminal
1. Open terminal in the project directory:
   ```bash
   cd placement_data_processor
   ```
2. Activate your virtual environment:
   - **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
   - **Windows (Command Prompt):** `.venv\Scripts\activate.bat`
   - **macOS / Linux:** `source .venv/bin/activate`
3. Start the application:
   ```bash
   streamlit run app.py
   ```
4. Navigate to `http://localhost:8501` in your browser.

---

## 3. How to Stop the Application

1. In the terminal or batch window, press **`Ctrl + C`** or simply **close the window**.

## 4. How to use the application


1. **Upload files**
   - Responses workbook (Google Form / Sheets export)
   - Studentwise Placement workbook
   - Studentwise Internship workbook (optional)
2. **Drive rules** — set placement, academic, Live KT, and internship rules for this drive directly in the UI.
3. **Validate** — confirm detected columns, row counts, warnings, and errors.
4. **Process data**
5. **Preview** counts and a sample of eligible students.
6. **Generate workbook**, then **Download final workbook**.

The download contains four sheets:

| Sheet | Purpose |
| --- | --- |
| **RAIT** | Final eligible list with College Roll No. (internal-use column 2 with light red fill) |
| **Remove** | Every removed student organized into 6 sections with identical RAIT schema |
| **Audit** | Per-student status for troubleshooting |
| **Run Info** | Counts and processing date |

Files stay in the browser session. They are not saved on disk and are not sent to external APIs.

## 5. Project architecture

```text
placement_data_processor/
├── app.py                 Streamlit UI only
├── config/                DriveRules + RAIT column contract
├── core/                  Load → validate → normalize → dedupe → match → rules
├── output/                Workbook build + formatting
├── utils/                 Header mapping, names, phones, logging
├── tests/
├── requirements.txt
└── README.md
```

`app.py` never implements eligibility. It calls `core.processor.process` / `run_pipeline` and `output.workbook.build_workbook`.

Pipeline order:

1. Load workbooks (once)
2. Detect and validate headers by **name**, not column position
3. Normalize into a canonical student table
4. Remove duplicate responses (latest Timestamp wins on College Roll No., then email, then mobile)
5. Match placement records and compute offer count
6. Apply placement, academic, Live KT, then internship rules
7. Log every removal
8. Build RAIT + Remove + Audit + Run Info

Name-only collisions are flagged for review and are never auto-merged.

## 6. Adding or changing eligibility rules

Do **not** edit core matching logic for a one-off drive. Change the Step 2 controls in the UI.

If the team needs a new kind of rule (for example an optional Gap rule):

1. Add a field on `DriveRules` in `config/settings.py`
2. Expose it in `app.py`
3. Apply it in `core/processor.py` in the documented pipeline order
4. Give it a removal category and write tests

Keep the same application for every drive. Only the configuration changes.

## 7. Deploy for the TPC team

Team members should not install Python or edit Excel macros. Host one Streamlit app and share the URL.

**Streamlit Community Cloud**

1. Put this folder in a Git repository
2. Create an app at [share.streamlit.io](https://share.streamlit.io) with `app.py` as the entry point
3. Share the deployed URL with TPC

**Server / VM**

```bash
pip install -r requirements.txt
streamlit run app.py --server.port 8501 --server.headless true
```

Put it behind your college SSO or VPN if student data must stay on the intranet.

Treat uploads as sensitive: do not log personal fields, do not copy workbooks to shared drives from the app, and restart/clear the session after a drive is finished.
