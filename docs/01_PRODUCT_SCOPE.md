# IEMS Internal ERP  
## Project Requirements Summary

**Project Status:** Active planning phase  
**Company:** Inter Event Management Services (IEMS)  
**System Type:** Internal ERP  
**Technology Stack:** To be decided separately  

---

# 1. Project Overview

The IEMS Internal ERP will be a company-wide internal operations platform for employees, managers, admins, super admins, and directors.

The ERP will centralise daily work, attendance, task management, calendars, digital documents, offline archives, and physical file-room records.

The system should remain simple enough for employees to use daily while still giving management a complete operational view.

The previous inventory, invoice, logistics, truck-tracking, and WhatsApp-automation dashboard has been abandoned. Those features are not part of the initial ERP scope unless they are intentionally reconsidered later.

---

# 2. ERP Objectives

The ERP should help IEMS:

- Track employee attendance
- Manage leave requests
- Assign and monitor daily tasks
- Maintain shared calendars
- Organise client and event documents
- Preserve existing folder structures
- Support online and offline document access
- Maintain matching physical file-room archives
- Locate physical folders quickly
- Track physical file checkouts and returns
- Search across projects and records
- Control access using ABAC
- Provide management and director-level visibility
- Record important activity through audit logs

---

# 3. Core ERP Modules

The ERP should include the following modules:

1. Employee Dashboard
2. Attendance Management
3. Leave Management
4. Task Management
5. Shared Calendar
6. Client and Event Project Management
7. Digital Document Management
8. Offline Folder Archive
9. Physical Records-Room Management
10. QR-Code and Barcode Labelling
11. Search and Filtering
12. Approval Workflows
13. Audit Logs
14. ABAC Access Control
15. Admin Dashboard
16. Super Admin Dashboard
17. Super User Controls
18. Director Dashboard

---

# 4. User Types

The system should support the following access levels:

```text
Employee
Manager
Admin
Super Admin
Super User
Director
```

The Director account should be:

```text
director@iemsnewdelhi.com
```

The Director account should operate as a Super User account with a dedicated Director Dashboard.

---

# 5. Employee Dashboard

Each employee should have a simple home page focused on their own daily work.

## 5.1 Employee Home Page

The dashboard should show:

- Today's attendance status
- Check-in and check-out controls
- Tasks due today
- Overdue tasks
- Upcoming meetings
- Event deadlines
- Leave-request status
- Recent announcements
- Recently opened project folders
- Recently uploaded documents
- Quick links to commonly used folders

The interface should remain easy to use for employees who are not technically experienced.

---

# 6. Attendance Management

## 6.1 Employee Features

Employees should be able to:

- Check in
- Check out
- View attendance history
- View working hours
- View late arrivals
- View absences
- View leave days
- Request leave
- View leave-request status

## 6.2 Manager and Admin Features

Managers and admins should be able to:

- View team attendance
- Approve or reject leave
- Correct attendance entries
- Add remarks
- Export monthly attendance reports
- View department-wise attendance
- View employees currently checked in

## 6.3 Future Enhancements

Possible later additions:

- Office Wi-Fi verification
- GPS-based check-in
- QR-based office check-in
- Biometric attendance integration
- Payroll export

---

# 7. Task Management

Employees should be able to view and update daily tasks.

Each task should include:

```text
Title
Description
Assigned Employee
Assigned By
Client
Project
Priority
Due Date
Status
Comments
Attachments
Related Folder
```

Task statuses:

```text
To Do
In Progress
Blocked
Completed
```

Managers should be able to:

- Assign tasks
- Reassign tasks
- Track completion
- Filter by employee
- Filter by project
- View overdue work
- View blocked tasks

Example:

```text
Task: Upload signed venue permission
Project: IEMS-2026-0042
Folder: 04 Venue Documents
Assigned To: Priya
Due: Today, 5 PM
Priority: High
```

---

# 8. Shared Calendar

The calendar should show:

- Event dates
- Meetings
- Site visits
- Vendor deadlines
- Task deadlines
- Payment follow-ups
- Employee leave
- Archive-verification dates
- Physical-file return deadlines

Calendar entries should link to the related project, task, employee, or document where applicable.

---

# 9. Client and Event Project Management

Each client event should be treated as a structured project.

Example:

```text
Project ID: IEMS-2026-0042
Client: Company A
Event: Annual Conference 2026
Event Date: 18 August 2026
Venue: Pragati Maidan
Project Manager: Rahul Sharma
Assigned Team: Rahul, Amit, Priya
Status: Active
Priority: Normal
```

Possible project statuses:

```text
Planning
Active
On Hold
Completed
Archived
Cancelled
```

Each project should connect:

```text
Client Project
      ↓
Digital Folder
      ↓
Offline Download
      ↓
Physical Records-Room File
      ↓
Tasks
      ↓
Calendar
      ↓
Approvals
      ↓
Audit Logs
```

---

# 10. Digital Document Management

The document system is the core of the ERP.

## 10.1 Existing Folder Structure

The ERP should preserve the office's existing folder hierarchy instead of forcing employees to reorganise files.

Example:

```text
IEMS-2026-0042 - Company A - Annual Conference 2026/
├── 01 Client Brief/
├── 02 Quotations/
├── 03 Work Orders/
├── 04 Venue Documents/
├── 05 Vendor Documents/
├── 06 Event Plans/
├── 07 Bills and Invoices/
├── 08 Photos and Deliverables/
└── 09 Final Archive/
```

The system should preserve:

- Folder names
- Subfolder names
- File hierarchy
- Existing imported folders
- Downloaded offline copies
- Physical file references

## 10.2 Project Metadata Label

Each folder should have a visible metadata label.

Example:

```text
Project ID: IEMS-2026-0042
Client: Company A
Event: Annual Conference 2026
Event Date: 18 August 2026
Venue: Pragati Maidan
Project Manager: Rahul Sharma
Status: Active
Priority: Normal
Assigned Team: Rahul, Amit, Priya
Physical File Status: Available
Offline Archive Status: Downloaded
```

The metadata should be stored separately from the folder name so it can be searched, filtered, and updated easily.

## 10.3 File Features

Employees should be able to:

- Upload files
- Download files
- Preview files
- Rename files
- Move files
- Create folders
- Upload existing folders
- Download complete project folders
- View file versions
- Mark files as approved
- Search files
- View file activity

Supported previews should include:

- PDF
- Images
- Word documents
- Excel sheets
- PowerPoint files
- Text files

---

# 11. Offline Archive Downloads

Each project should support a full offline download while preserving the hierarchy.

Example:

```text
IEMS-2026-0042 - Company A - Annual Conference 2026.zip
```

The download should include:

- Original folder hierarchy
- All selected files
- Project metadata
- Archive manifest
- Printable folder label
- Printable cover sheet
- Document index sheet
- QR code or barcode
- Download date
- Downloaded-by employee

For the initial version, offline access can remain read-only.

---

# 12. Physical Records-Room Management

The ERP should support a matching physical archive for paper files.

Each physical folder should be linked to the same project ID used in the digital system.

Example:

```text
Project ID: IEMS-2026-0042
Client: Company A
Event: Annual Conference 2026
Physical Location:
Records Room A
→ Rack R02
→ Shelf S03
→ Box B05
→ File F014
```

## 12.1 Storage Location Fields

The system should track:

```text
Room
Rack
Shelf
Cabinet
Box
File Number
Archived On
Archived By
Last Verified On
Physical File Status
```

Possible statuses:

```text
Available
Checked Out
Missing
Under Verification
Archived
```

---

# 13. Physical Folder Label

The ERP should generate printable labels.

Example:

```text
IEMS PROJECT FILE

Project ID: IEMS-2026-0042
Client: Company A
Event: Annual Conference 2026
Event Date: 18 Aug 2026
Venue: Pragati Maidan
Project Manager: Rahul Sharma

Physical Location:
Records Room A
Rack: R02
Shelf: S03
Box: B05
File: F014

[ QR CODE ]
```

---

# 14. QR-Code and Barcode Support

Each physical folder should have a QR code or barcode.

Scanning it should open the matching project record.

QR codes can also be generated for:

- Storage rooms
- Racks
- Shelves
- Cabinets
- Boxes
- Individual files

Scanning a box or rack should show the records stored inside it.

---

# 15. Physical File Checkout Register

Employees should be able to scan a folder and check it out.

Example:

```text
Physical File Status: Checked Out
Taken By: Priya
Taken On: 4 June 2026, 11:30 AM
Purpose: Client payment reconciliation
Expected Return: 5 June 2026
```

When returned:

```text
Returned On: 5 June 2026, 3:10 PM
Status: Available
```

The ERP should track:

- Employee
- Checkout date
- Purpose
- Expected return date
- Actual return date
- Overdue status
- Remarks

The ERP should alert users about overdue physical files.

---

# 16. Folder Templates

When a new project is created, the ERP should automatically create a standard folder hierarchy.

Templates can differ by project type:

```text
Conference
Exhibition
Corporate Event
Government Event
Product Launch
Vendor File
HR File
Legal File
```

Admins should be able to update templates later.

---

# 17. Search

Employees should be able to search using:

- Project ID
- Client name
- Event name
- Event date
- Venue
- File name
- Folder name
- Project manager
- Assigned employee
- Tags
- Physical location
- Room
- Rack number
- Shelf number
- Box number
- File number

Example search:

```text
Pragati Maidan conference 2025
```

Possible result:

```text
IEMS-2025-0081
Company A — Annual Conference

Digital Folder: Available
Physical File: Room A → Rack R03 → Shelf S02 → File F021
```

---

# 18. Version History

Important files should support version history.

Example:

```text
Quotation.pdf
├── Version 1 — Uploaded 2 June
├── Version 2 — Revised 5 June
└── Version 3 — Approved 7 June
```

The latest approved version should be clearly marked.

---

# 19. Approval Workflows

Some files should require approval.

Possible statuses:

```text
Draft
Under Review
Approved
Rejected
Superseded
Archived
```

Useful approval categories:

- Quotations
- Artwork
- Stage layouts
- Vendor proposals
- Final bills
- Work orders
- Archive closure

Approval actions should include:

```text
Preview
Approve
Reject
Add Comment
Request Revision
```

---

# 20. Missing Document Checklist

Each project should show whether required documents are available.

Example:

| Document Type | Status |
|---|---|
| Client brief | Uploaded |
| Signed quotation | Uploaded |
| Work order | Missing |
| Venue approval | Uploaded |
| Vendor bills | Partially uploaded |
| Final invoice | Pending |

The ERP can calculate:

```text
Archive Readiness: 78%
```

Before archiving a project, the system should flag missing required files.

---

# 21. Existing Folder Import

The ERP should allow employees to import existing folders while preserving their structure.

Workflow:

```text
Upload Existing Folder
→ Preserve Structure
→ Add Client
→ Add Event Name
→ Add Project ID
→ Add Year
→ Add Tags
→ Add Physical Storage Location
```

This allows older company records to be digitised gradually.

---

# 22. Duplicate Detection

The system should warn users when a similar file already exists.

Example:

```text
A similar file already exists:
Vendor Quote - Sound System.pdf
Uploaded on 2 June 2026
```

---

# 23. Mobile Document Scanning

A later mobile-friendly feature can allow employees to scan paper documents.

Workflow:

```text
Scan Document
→ Select Project
→ Select Folder
→ Rename File
→ Upload
```

Example:

```text
Project: IEMS-2026-0042
Folder: 05 Vendor Documents
File: Signed Sound Vendor Quote.pdf
```

---

# 24. Archive Verification

Physical files should be verified periodically.

The employee should scan the QR code and confirm:

- Physical file exists
- Label is readable
- Storage location is correct
- Digital archive exists
- Folder contents are complete

Example:

```text
Last Verified: 3 June 2026
Next Verification: 3 December 2026
```

---

# 25. Access Control

The ERP should use a hybrid **RBAC + ABAC** model.

## 25.1 RBAC Layer

RBAC should be used for broad platform roles:

```text
Employee
Manager
Admin
Super Admin
Super User
Director
```

## 25.2 ABAC Layer

ABAC should control detailed access using attributes.

Possible user attributes:

```text
Department
Designation
Employee ID
Assigned Projects
Archive Permissions
Finance Access
HR Access
Confidentiality Level
```

Possible resource attributes:

```text
Project ID
Client
Document Type
Department
Project Status
Confidentiality Level
Archive Status
Physical Location
```

Example rule:

```text
ALLOW view_document
IF user.employee_id IN project.assigned_team
AND document.project_id = project.project_id
```

Example finance rule:

```text
ALLOW view_document
IF user.department = "accounts"
AND document.document_type = "invoice"
```

Default policy:

```text
DENY unless explicitly allowed
```

---

# 26. Super User

The ERP should include a Super User role.

The Super User should be able to:

- View every project folder
- Access HR, finance, legal, and management documents
- Override access restrictions
- Edit or disable policies
- Restore deleted files
- Manage admins and super admins
- Export complete archives
- View complete audit logs
- Access physical archive records
- Override checkout restrictions
- Manage system-wide settings

Only one or two Super User accounts should exist.

Every Super User action must still be logged.

Sensitive actions should require:

```text
Reason for override
```

---

# 27. Director Dashboard

A dedicated Director Dashboard should be created for:

```text
director@iemsnewdelhi.com
```

The Director account should operate as a Super User account.

## 27.1 Director Dashboard Purpose

The Director Dashboard should provide a company-wide operational overview without requiring the director to open every module manually.

## 27.2 Executive Metrics

The dashboard should show:

| Metric | Example |
|---|---:|
| Active projects | 18 |
| Upcoming events this week | 6 |
| Overdue tasks | 9 |
| Pending approvals | 5 |
| Employees present today | 11 |
| Employees absent today | 2 |
| Physical files checked out | 4 |
| Overdue physical-file returns | 1 |
| Projects missing key documents | 6 |
| Archives pending verification | 12 |

Each metric should be clickable.

## 27.3 Project Overview

The Director should be able to view all projects.

Example:

| Project | Client | Event Date | Manager | Status | Archive Readiness |
|---|---|---:|---|---|---:|
| Annual Conference | Company A | 18 Aug 2026 | Rahul | Active | 78% |
| Product Launch | Company B | 25 Aug 2026 | Priya | Planning | 52% |
| Exhibition Setup | Company C | 4 Sep 2026 | Amit | Urgent | 66% |

Filters:

```text
Client
Project Manager
Status
Event Date
Venue
Priority
Archive Readiness
Department
```

## 27.4 Attendance Summary

The Director Dashboard should show:

- Employees present today
- Employees absent today
- Employees on leave
- Late arrivals
- Employees currently checked in
- Monthly trends
- Department-wise attendance

## 27.5 Tasks and Workload

The Director Dashboard should show:

- Overdue tasks
- Tasks due today
- Blocked tasks
- High-priority tasks
- Tasks grouped by employee
- Tasks grouped by project
- Employee workload distribution

## 27.6 Calendar

The Director calendar should show:

- Event dates
- Meetings
- Site visits
- Vendor deadlines
- Project deadlines
- Payment follow-ups
- Employee leave
- Archive-verification dates
- Physical-file return deadlines

## 27.7 Document and Archive Monitoring

The Director should be able to see:

- Recently uploaded documents
- Recently downloaded archives
- Projects missing required files
- Files awaiting approval
- Physical files currently checked out
- Archives without storage locations
- Projects pending verification
- Deleted or restored files

## 27.8 Physical Storage-Room View

Example:

```text
Records Room A
├── Rack R01
│   ├── Shelf S01 — 14 folders
│   └── Shelf S02 — 11 folders
├── Rack R02
│   ├── Shelf S01 — 9 folders
│   └── Shelf S03 — 16 folders
```

The Director should be able to search by:

```text
Room
Rack
Shelf
Box
File Number
Client
Project ID
```

## 27.9 Alerts

Examples:

```text
3 projects have missing work orders
1 physical file is overdue for return
5 approvals are pending
2 employees have overdue tasks
4 archives need verification this month
```

Possible severity levels:

```text
Critical
High
Normal
Informational
```

## 27.10 Audit Activity

The Director Dashboard should show important recent activity.

Example:

```text
4 June 2026, 11:20 AM
Rahul uploaded Work Order.pdf

4 June 2026, 11:35 AM
Priya downloaded project archive IEMS-2026-0042

4 June 2026, 12:05 PM
Amit moved physical file:
Room A → Rack R02 → Shelf S03 → File F014
```

---

# 28. Audit Logs

The ERP should record important activity.

Log:

- Uploads
- Downloads
- Edits
- Deletions
- Restores
- Archive downloads
- Permission changes
- Approval actions
- Physical location changes
- Physical file checkouts
- Physical file returns
- Super User overrides
- Attendance corrections
- Leave approvals
- Task updates

Example:

```text
4 June 2026, 11:20 AM
Rahul uploaded Work Order.pdf

4 June 2026, 11:35 AM
Priya downloaded the project archive

4 June 2026, 12:05 PM
Amit assigned physical location:
Room A → Rack R02 → Shelf S03 → File F014
```

---

# 29. Management Dashboard

Management should see:

| Metric | Example |
|---|---:|
| Active projects | 18 |
| Projects with missing documents | 6 |
| Physical files checked out | 4 |
| Overdue file returns | 2 |
| Pending approvals | 5 |
| Archives awaiting verification | 12 |
| Overdue tasks | 9 |
| Employees absent today | 3 |

---

# 30. MVP Scope

Build the first version with:

1. Login
2. Employee accounts
3. Roles
4. ABAC checks
5. Super User account
6. Director account
7. Employee Dashboard
8. Director Dashboard
9. Attendance
10. Leave requests
11. Daily tasks
12. Shared calendar
13. Client and event projects
14. Project metadata labels
15. Existing folder import
16. File upload
17. File preview
18. File download
19. Search
20. Download complete project archive as ZIP
21. Printable folder labels
22. QR-code generation
23. Physical archive location tracking
24. Physical-file checkout and return
25. Pending approvals
26. Basic audit logs

---

# 31. Add Later

After the MVP is working:

- Advanced version history
- Approval-workflow automation
- Archive-readiness scoring
- Mobile document scanning
- Duplicate detection
- Periodic archive verification
- Notifications
- Retention rules
- Full-text document search
- Advanced offline sync
- Management analytics
- Google Calendar integration
- Automated reminders
- Bulk archive import
- Biometric attendance
- Payroll export

---

# 32. Final ERP Concept

The IEMS Internal ERP should connect:

```text
Employees
      ↓
Attendance
      ↓
Tasks
      ↓
Calendar
      ↓
Projects
      ↓
Digital Documents
      ↓
Offline Archives
      ↓
Physical Records-Room Files
      ↓
Approvals
      ↓
Audit Logs
      ↓
Director Dashboard
```

The goal is to create one internal system where IEMS employees can work daily, managers can supervise operations, and directors can monitor the company from a single dashboard.

---

# 33. Technology Stack

The technology stack will be decided separately after the functional requirements are finalised.
