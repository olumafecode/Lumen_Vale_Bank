# LVB-08: Internal Control, Approvals, and Assurance Policy

Document ID: LVB-08
Version: 1.0
Status: Synthetic academic draft; not an operational bank policy
Effective date (fictional scenario): 2026-10-01
Review date: 2027-10-01
Owner: Finance Controller
Designated approval authority: Fictional Board of Directors; no actual approval implied
Classification: Public synthetic educational corpus
Provenance: Original AI-assisted fictional text created for this project; no private or third-party bank policies used

## 1. Control ownership and segregation of duties
### 1.1 Responsibilities
Business managers own and operate controls in their processes. Finance, Compliance, Security, and the DPO provide specialist oversight within their responsibilities. Internal Audit independently tests the design and operation of controls and reports to the Board Audit Committee. Internal Audit must not prepare the reconciliation or approval evidence it later audits.

Each key control has a documented purpose, owner, frequency, evidence location, independent reviewer where required, and escalation route. The control register links to the relevant policy section and system record. A ticked checklist without supporting evidence is not proof that a control operated. Staff must not backdate a sign-off or use another person's identity.

### 1.2 Maker and checker
The person preparing a manual account adjustment cannot approve it. The person requesting their own expense cannot approve reimbursement. The person creating or changing a supplier's bank details cannot be the sole approver of the related payment. Access provisioning requires business-owner approval, and privileged access also requires CISO approval. The Service Desk implements the approved change; approval and implementation evidence must be distinguishable.

If a small team cannot separate duties locally, route the check to an authorized independent person in Operations or Finance before execution. Staff absence does not justify self-approval. Branch-specific cash controls are in LVB-04. Expense approval levels in LVB-11 govern expense claims and do not replace branch payout controls; equal monetary values in different processes do not imply equal approval authority.

### 1.3 Reconciliations and certification
Branches reconcile tills daily at close. Finance reviews the monthly general-ledger reconciliation within five business days after month-end, with an independent reviewer within the next two business days. Record unresolved items with amounts, age, owner, reason, and action date. Do not clear an item just to meet a deadline. Managers certify user access quarterly, including role fit, leavers, dormant accounts, and privileged permissions; privileged access review includes Security.

<!-- PRINT PAGE BREAK -->

## 2. Exceptions, urgent access, and escalation
### 2.1 Control failures
Record a missed control or suspected control failure in the Control Exceptions queue by the end of the day of discovery. Notify the control owner promptly. A high-risk failure involving possible fraud, unauthorized payment, or Restricted-data exposure must be escalated immediately to the relevant specialist owner; security-related failures also follow the 15-minute requirement in LVB-02.

The control owner assesses impact, interim safeguards, responsible staff, and an action deadline within two business days of the report. If exposure remains active, containment begins immediately rather than waiting for assessment completion. Finance tracks financial exceptions, while the relevant specialist tracks their own corrective actions. An exception is closed only after evidence shows the fix has been implemented and independently checked.

### 2.2 Emergency access
Emergency elevated access requires a named requester, documented incident or business-continuity reason, system scope, CISO or on-call Security delegate approval, and approval by an independent business owner. Record both approvals before activation. Use the employee's named emergency account with MFA and activity logging, never a shared login. If approvals cannot be obtained, do not grant access; escalate service continuity to Operations.

Access expires after at most four hours and must be removed sooner when the task is complete. Any extension is a new request requiring both approvals. Security reviews activity by the end of the next business day and records whether the access matched its purpose. Emergency access does not authorize self-approval of payments, disabling logging, or bypassing customer verification. Credential recovery still follows LVB-01 identity checks.

### 2.3 Unresolved and overdue items
Owners review open high-risk exceptions each business day. Any overdue high-risk action is escalated to the CEO and Board Audit Committee through the Finance Controller, with a risk explanation and revised plan. Other overdue actions are reviewed weekly by the relevant executive. A revised date does not erase the original deadline or evidence of delay. Retain the change history and approval rationale.

<!-- PRINT PAGE BREAK -->

## 3. Monitoring, change control, and assurance
### 3.1 Business-system changes
A change to a payment, customer, identity, or financial-reporting system requires a request describing purpose, risk, test results, approvals, rollback plan, and planned implementation window. The business owner approves the intended behavior; IT approves technical readiness; Security reviews security-impacting changes. The implementer must not be the sole tester or approver of a material change.

An emergency change uses the same minimum recorded purpose, risk, independent approval, and rollback plan before execution, with missing routine documentation completed by the end of the next business day. Emergency labeling cannot waive the named-account, logging, or transaction-separation controls. The owner verifies successful operation and records any rollback or incident.

### 3.2 Management review and audit
The Finance Controller provides a monthly control dashboard to senior management: overdue reconciliations, unresolved cash differences, emergency access, overdue remediation, and repeated exceptions. The dashboard uses aggregate data where possible and does not include unnecessary customer identifiers. A recurring low-value difference may indicate a wider issue and must not be ignored solely because it is below an amount threshold.

Internal Audit chooses its review samples independently, checks evidence against the control register, and reports findings with owners and dates. The Board Audit Committee reviews remediation progress quarterly. Managers supply complete records and must not coach staff to conceal failures. Retention follows LVB-06: financial reconciliation packs are seven years after financial year-end, access-review evidence is two years after completion, and control-exception cases are seven years after closure.

### 3.3 Worked control examples
A staff member creates a CU 200 manual account adjustment. An independent authorized checker is required even though the amount is below the branch cash-payout threshold; these are different controls. A manager submits an expense claim and routes approval upward rather than approving it themselves. A payment system fails and an engineer receives emergency access for two hours after the required approvals; access is removed when work finishes after 40 minutes, and Security reviews the activity by the next business-day end.

When a control is not described, staff ask the process owner for a written procedure. They must not interpret silence as permission to omit review. A new recurring control should be documented and approved through policy governance before being represented as an existing rule in the policy assistant.
