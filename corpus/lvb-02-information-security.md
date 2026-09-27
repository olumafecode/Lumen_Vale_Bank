# LVB-02: Information Security and Incident Response Policy

Document ID: LVB-02
Version: 1.0
Status: Synthetic academic draft; not an operational bank policy
Effective date (fictional scenario): 2026-10-01
Review date: 2027-10-01
Owner: Chief Information Security Officer
Designated approval authority: Fictional Board of Directors; no actual approval implied
Classification: Public synthetic educational corpus
Provenance: Original AI-assisted fictional text created for this project; no private or third-party bank policies used

## 1. Information classification and everyday safeguards
### 1.1 Scope and classification
This policy applies to bank information in electronic, paper, verbal, and photographed form, whether used in a branch, at head office, or remotely. Information owners assign one of four labels. Public information has an approved external release. Internal information is ordinary staff-only material. Confidential information includes internal financial reports and nonpublic business plans. Restricted information includes customer identification documents, account data, employee medical records, authentication secrets, and investigation identities.

If information is unlabelled, treat it as Confidential until its owner classifies it. If a file mixes classes, apply the highest class to the whole file unless the owner separates it safely. Public availability of one field does not make a combined customer record Public. LVB-06 provides privacy-specific handling and retention rules.

### 1.2 Approved systems and least privilege
Use only bank-managed devices and approved applications for Confidential or Restricted data. Access must match a recorded business need and approval in AccessDesk. Do not install unapproved software, disable endpoint protection, use personal cloud storage, or upload bank data to a public AI service. Synthetic training examples approved by the information owner may be used in an approved AI tool; real bank records must not be substituted for them.

The IT team applies critical security patches within 72 hours of its classification of a patch as critical, and high-priority patches within 14 calendar days. The system owner records testing and deployment evidence. If the deadline cannot be met, the CISO must approve documented temporary safeguards and a remediation date before expiry; the exception process in section 3.2 applies.

### 1.3 Physical handling
Keep Restricted paper in locked storage when unattended. Use secure-print release and collect pages immediately. Escort visitors in staff-only areas and do not allow tailgating. Dispose of records only through approved destruction bins or approved electronic deletion, after retention and hold checks. Lock screens when stepping away, even for a brief conversation.

<!-- PRINT PAGE BREAK -->

## 2. Incident reporting and response
### 2.1 What to report and when
Report suspected phishing, malware, unauthorized access, lost devices, mistaken data disclosure, missing sensitive papers, and suspicious MFA prompts immediately and no later than 15 minutes after discovery. Use the on-call Security queue in CaseTrack from a safe device. If it is unavailable, call the internal on-call contact; that recipient records the incident once service returns. A manager's permission is not required. Reporting promptly is required even if the employee caused the mistake.

Include what happened, when it was discovered, affected system or location, data type, and a safe callback route. Do not include passwords, MFA codes, complete customer documents, or speculative accusations. Preserve original messages and timestamps through Security's evidence instructions. Do not erase logs, investigate another employee's account, or contact a suspected attacker.

### 2.2 Immediate containment and triage
For suspected device compromise, disconnect the device from networks if safe, stop using it, and contact Security from another device. Do not factory-reset, wipe, or power off solely to remove evidence unless Security instructs it or physical safety requires it. For a misdirected email, report it; attempted recall does not replace reporting. Security assigns an incident lead and records severity, containment decisions, and evidence custody.

Active compromise of a payment service or exposure of Restricted data is Priority 1. Security acknowledges Priority 1 reports within 15 minutes of receipt and begins containment immediately. Other reports are acknowledged within one business day. Acknowledgment targets do not relax the employee's 15-minute reporting requirement.

### 2.3 Privacy and communication coordination
When personal data may be affected, the incident lead notifies the DPO within one hour of Security's receipt of the report. The DPO and Compliance Officer determine any external notification obligations for the scenario; this corpus supplies no statutory deadline. Only authorized communication owners may notify customers or media. Staff must not speculate in group chats or contact affected customers independently.

<!-- PRINT PAGE BREAK -->

## 3. Recovery, third parties, and review
### 3.1 Recovery and learning
The incident lead confirms containment and removal of the cause before restoration. The system owner verifies service integrity using an approved test; Security approves return to service and records any continuing monitoring. Restoring a backup does not by itself prove that unauthorized access has ended. Backups containing personal data remain subject to LVB-06 retention and hold rules.

For Priority 1 incidents, the incident lead completes a lessons-learned review within five business days after service restoration. Record the timeline, impact, evidence, root cause where established, corrective action, owner, and due date. Label an unconfirmed cause as unconfirmed. The CISO tracks overdue actions weekly and escalates unresolved high-risk actions to the Board Risk Committee through the CEO.

### 3.2 Third parties and exceptions
Before a supplier receives Confidential or Restricted data, the business sponsor obtains Security, DPO, and Procurement review of access, storage, incident contacts, deletion, and exit arrangements. Supplier access must have an expiry date and named sponsor. The sponsor reports a supplier incident through the same internal Security channel; a supplier's own report does not replace the bank's incident record.

A temporary exception to a technical safeguard requires CISO and relevant business-owner approval in CaseTrack, compensating controls, a responsible person, and an expiry no later than 30 calendar days. The exception cannot waive incident reporting, authorize personal cloud storage, or waive a privacy hold. Credential-specific exceptions follow the additional restrictions in LVB-01 section 3.2. The CISO checks the register weekly.

### 3.3 Training, records, and examples
All staff complete security induction before access to customer systems and refresher training annually. Managers track overdue completion and restrict untrained staff from sensitive tasks until training is complete. Security maintains incident records for seven years after closure; ordinary security logs follow the one-year schedule in LVB-06 unless placed on hold.

Example: a laptop lost on a train is reported within 15 minutes of discovery even if encrypted. Security determines whether remote containment is necessary and the DPO assesses personal-data impact. Example: a customer file emailed to the wrong recipient triggers both security response and privacy assessment; it is not resolved merely by receiving a deletion promise.
