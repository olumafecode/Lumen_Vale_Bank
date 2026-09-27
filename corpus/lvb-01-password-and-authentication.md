# LVB-01: Password and Authentication Policy

Document ID: LVB-01
Version: 1.0
Status: Synthetic academic draft; not an operational bank policy
Effective date (fictional scenario): 2026-10-01
Review date: 2027-10-01
Owner: Chief Information Security Officer
Designated approval authority: Fictional Board of Directors; no actual approval implied
Classification: Public synthetic educational corpus
Provenance: Original AI-assisted fictional text created for this project; no private or third-party bank policies used

## 1. Credential standards and enrollment
### 1.1 Scope and ownership
This policy covers workforce authentication to LVB-managed applications, devices, privileged accounts, and remote access. Customer online-banking authentication is outside scope. Every workforce account must identify one person or an approved service. Shared human accounts are prohibited, including shared branch teller logins. Managers sponsor access; the Service Desk provisions it through AccessDesk after the required approval.

### 1.2 Password and multifactor requirements
Human-account passwords must contain at least 14 characters. Staff must use a unique password for each bank system where a separate password is needed and must not reuse a personal password. The system checks proposed passwords against a blocked list of common or compromised values. The bank does not impose a universal periodic password-change interval; a change is required when compromise is suspected or confirmed, a temporary password is issued, or the CISO directs a documented security reset.

Multifactor authentication (MFA) is required for bank email, remote access, privileged access, and systems containing Confidential or Restricted data. Use a bank-approved authenticator application or hardware security key. SMS is not an approved standard factor in this fictional policy. Privileged administrators must use a hardware security key and a separate administrative account; their everyday account must not hold standing administrator privileges.

### 1.3 Safe storage and enrollment
Use the bank-approved password manager. Do not place credentials in email, chat, spreadsheets, source code, browser notes, or support tickets. A manager, auditor, or Service Desk analyst must never ask for the password or a one-time MFA code. Staff must reject unexpected MFA prompts and report them as suspected compromise under section 2.3.

The Service Desk verifies identity through an existing personnel record and a callback to a registered contact before enrollment or recovery. A message from an unverified number or a manager's informal assurance is insufficient. Record verification completion, not secret answers or MFA codes, in AccessDesk.

<!-- PRINT PAGE BREAK -->

## 2. Lockout, recovery, and suspected compromise
### 2.1 Failed attempts and sessions
After five consecutive failed password attempts, an account is locked for 15 minutes. Repeated lockouts require Service Desk review. Staff must not bypass a lockout by borrowing another person's login. Supported workstations lock after five minutes of inactivity; staff must also lock them immediately when leaving a desk. An application that cannot meet the standard needs a time-limited exception under section 3.2, not an informal workaround.

### 2.2 Recovery procedure
Open an AccessDesk request or contact the Service Desk using the internal directory. The analyst verifies identity using section 1.3 and checks whether a security incident may be involved. If verified, the analyst revokes the lost factor or affected sessions, issues a temporary credential where necessary, and assists enrollment of a replacement factor. Temporary passwords expire after 24 hours and must be changed at first sign-in. Send them through an approved separate delivery channel, never in the same message as the account identifier.

If identity cannot be verified, access stays blocked and the analyst escalates to the Service Desk lead. Operational urgency, including an open branch queue, does not remove verification requirements. A lost hardware key must be reported immediately so the old factor can be revoked; replacing the device alone is insufficient.

### 2.3 Compromise response
Suspected exposure, an unexpected MFA approval request, or a password entered into a suspicious website must be reported to the on-call Security queue immediately and no later than 15 minutes after discovery, using a safe device. Do not wait for a manager or proof of misuse. If CaseTrack is unavailable, use the on-call directory; the recipient creates the record when the system returns.

Security directs containment, including session revocation and credential reset, and links the incident to AccessDesk. Preserve the suspicious message or URL through the approved evidence process; never forward passwords. The employee must not keep using a suspected compromised account merely because the password has been changed. Return to use requires Security clearance.

<!-- PRINT PAGE BREAK -->

## 3. Service accounts, exceptions, and assurance
### 3.1 Non-human credentials
A service account needs a named business owner, technical custodian, documented purpose, minimum access, and review date. Store secrets in the approved secrets vault, not the application repository. Prefer short-lived credentials where the system supports them. If a static service secret is necessary, rotate it at least every 90 calendar days and immediately after suspected exposure or loss of an authorized custodian's access where exposure cannot be ruled out.

Service accounts must not be used for interactive employee sign-in. Their owners review use and permissions quarterly. Disable an unused service account after the owner confirms it has no active dependency; test the change and record rollback arrangements. A human-account password's no-routine-expiry rule does not apply to static service secrets.

### 3.2 Exception control
The system owner requests an exception in CaseTrack before using a nonconforming system. State the affected requirement, business need, risk, compensating controls, accountable owner, and remediation date. Both the CISO and Head of Operations must approve it. An exception expires after no more than 30 calendar days and cannot authorize sharing a human account, revealing an MFA code, or skipping identity verification during recovery.

At expiry the system must comply or the affected access must stop. An extension requires a new documented risk review and both approvals; it is not automatic. Security keeps an exception register and checks expiry dates weekly. Emergency access follows LVB-08 section 2.2 and never permits a borrowed identity.

### 3.3 Evidence and examples
The Service Desk retains approved requests, verification completion records, recovery actions, and factor-revocation timestamps as access-management records under LVB-06 section 2.2. Security reviews lockout and unusual sign-in trends monthly without collecting passwords. Managers certify privileged access quarterly under LVB-08.

Example: a teller who forgot a password during a busy morning uses verified recovery and waits for their own account; a colleague does not lend a login. Example: a service secret found in a code repository requires immediate reporting, revocation or rotation, and an incident review even if the repository was intended to be private. These examples explain existing rules and do not create exceptions.
