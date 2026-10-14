# Northwind Cloud Support and Refund Policy

Version 4.2. Owner: Customer Support Operations. Applies to all Northwind Cloud plans (Starter, Team, Business, Enterprise).

## Urgency levels and response SLAs

Every ticket is triaged into one of three urgency levels. Urgency is set by business impact and deadlines, never by how the customer sounds.

- **High**: production outage, many users blocked, a whole team or company unable to log in, suspected security breach or data loss, or a hard business deadline today. First response within 30 minutes, 24/7. Post an alert to the #support-urgent Slack channel immediately.
- **Medium**: one user or one feature impaired, a working workaround exists, or a billing problem with real money at stake. First response within 4 business hours.
- **Low**: how-to questions, feature requests, cosmetic issues, general feedback. First response within 2 business days.

## Refunds on monthly plans

Monthly subscriptions can be refunded in full within 14 days of the most recent charge. After 14 days we do not refund the current month, but the customer can cancel at any time and will not be charged again. Partial-month refunds are not offered.

## Refunds on annual plans

Annual subscriptions can be refunded in full within 30 days of the purchase or renewal date. Between day 31 and day 90 we offer a prorated refund for the unused full months, minus a 10 percent processing fee. After 90 days annual plans are non-refundable, but the customer may downgrade at renewal.

If a customer was moved to an annual plan by mistake (for example, they selected monthly but were charged annually), refund the difference in full regardless of the date, and switch them to monthly billing.

## Duplicate or incorrect charges

Duplicate charges caused by our billing system are always refunded in full, with no time limit. Support agents may issue duplicate-charge refunds up to 5,000 USD without approval. Larger amounts need approval from the Billing Lead. Refunds reach the customer's card in 5 to 10 business days.

## Service outages and credits

An outage is any period where the Northwind Cloud dashboard or API returns errors for more than 5 percent of requests in a region. During an outage, link the customer to status.northwindcloud.example and post in #support-urgent.

Service credits for outages are based on monthly uptime for the affected region:

- Below 99.9 percent: 10 percent credit on that month's invoice.
- Below 99.0 percent: 25 percent credit.
- Below 95.0 percent: 50 percent credit.

Credits must be requested within 30 days of the incident. Credits are applied to the next invoice and are not paid out as cash.

## Account lockout procedure

When users are locked out of their accounts, first confirm the identity of the requester through the account owner's registered email or a verified admin. Never unlock an account based only on the ticket text.

If a single user is locked out, send a password reset link and ask them to check spam folders. If a whole team, department or company is locked out (for example after an SSO certificate change, an expired SAML configuration, or a mass lockout from failed login attempts), treat it as High urgency. Page the on-call Identity engineer, post in #support-urgent, and offer a temporary emergency access link valid for 24 hours once the admin is verified. Lockouts that block payroll, month-end close or other time-critical business processes must be resolved before the customer's deadline.

## Security incidents

Suspected leaked API keys, unauthorized access, or access by former employees are always High urgency. Immediately advise the customer to rotate the affected keys from Settings, then API Keys. Escalate to the Security team in #sec-incidents within 15 minutes. Do not ask the customer to send secrets or keys over email or in the ticket.

## Data export and backups

Failed scheduled backups for more than 24 hours are High urgency, because customers may be relying on them for compliance or audits. A single failed manual export with a working alternative (for example CSV instead of XLSX) is Medium urgency.

## Billing and invoices

Customers can update company name, address and VAT or GST numbers on future invoices from Settings, then Billing. We can reissue past invoices with corrected details on request within 12 months. Invoice changes are Low urgency unless a payment is failing.

## Feature requests

Log every feature request in the product feedback board and thank the customer. Do not promise delivery dates. Enterprise customers may be offered a call with their account manager to discuss the roadmap.

## Escalation rules

- Escalate to the on-call engineer for any High urgency technical issue.
- Escalate to the Billing Lead for refunds over 5,000 USD or any refund outside policy.
- Escalate to the Account Manager when an Enterprise customer threatens to cancel.
- A customer's anger alone is never a reason to escalate. Respond calmly, fix the actual issue, and follow the SLA for the real urgency.

## Tone guidelines for replies

Replies should be warm, specific and short. Acknowledge the problem in the first sentence, say exactly what happens next and by when, and sign off as "Northwind Cloud Support". Never blame the customer and never share internal channel names in replies.
