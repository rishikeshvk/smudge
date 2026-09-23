# Kindred M1 curriculum research: beginner AWS (IAM, S3, EC2), 2-week slice

Research date: 2026-09-23. This is research only, not the final topic graph.
Primary sources are docs.aws.amazon.com and aws.amazon.com, fetched on the research date. Each fact carries its URL
inline. Facts I could not confirm from an official page are marked **(unverified)**.

---

## 0. Facts that changed recently (verified 2026-09-23)

The buddy's notes and the probe-suite answer keys need these current values. Older courses, blog posts and model
training data often have the old values, so each one also makes a good "shaky note" or a check that the buddy's facts
are current.

| Fact | Current value | Old value / common stale belief | Source |
|---|---|---|---|
| S3 max object size | **50 TB** since Dec 2025. The docs note the true ceiling is 53.7 TB (48.8 TiB): 10,000 parts x 5 GiB | 5 TB | https://aws.amazon.com/about-aws/whats-new/2025/12/amazon-s3-maximum-object-size-50-tb/ , https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingObjects.html |
| S3 single PUT max / console upload max | 5 GB / 160 GB; multipart for 5 MB to 50 TB | same | https://docs.aws.amazon.com/AmazonS3/latest/userguide/upload-objects.html |
| S3 Block Public Access + ACLs disabled on new buckets | On by default for all new buckets (any creation method) since the rollout began **April 5, 2023**; console had it since 2018/2021 | "buckets are public by default" / "use ACLs to share" | https://aws.amazon.com/about-aws/whats-new/2023/04/amazon-s3-security-best-practices-buckets-default/ |
| S3 default encryption | SSE-S3 automatically on all new uploads since **Jan 5, 2023**, at no cost | "S3 isn't encrypted unless you turn it on" | https://docs.aws.amazon.com/AmazonS3/latest/userguide/default-bucket-encryption.html |
| SSE-C | **Disabled by default** on all new general purpose buckets since **April 6, 2026**, also on existing buckets in accounts with no SSE-C data | SSE-C freely usable | https://aws.amazon.com/about-aws/whats-new/2026/04/s3-default-bucket-security-setting/ |
| S3 consistency | Strong read-after-write for PUT/DELETE of objects in all Regions (since Dec 2020). Bucket *configuration* changes are still eventually consistent | "eventual consistency for overwrites" | https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html#ConsistencyModel |
| S3 general purpose bucket quota | 10,000 per account by default | 100 | https://docs.aws.amazon.com/AmazonS3/latest/userguide/BucketRestrictions.html |
| S3 bucket namespace | Global per partition, **plus** an optional *account regional namespace* (Mar 2026): names end in `-<12-digit-account>-<region>-an` | "names are globally unique, full stop" | https://aws.amazon.com/about-aws/whats-new/2026/03/amazon-s3-account-regional-namespaces/ , https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html |
| S3 partitions | Four: `aws`, `aws-cn`, `aws-us-gov`, `aws-eusc` (European Sovereign Cloud) | three | https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingBucket.html |
| S3 bucket types | Four: general purpose, directory, table, vector | "just buckets" | https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html |
| Free Tier | Accounts created on/after **July 15, 2025**: USD 100 credits at sign-up + up to USD 100 more earned; choose a **Free plan** (no charges; ends after 6 months or when credits run out; then the account closes, with 90 days to upgrade) or a **Paid plan** | "12 months free, 750 hrs t2.micro" (that is legacy, pre-July-2025 accounts only) | https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html |
| EC2 Free-Tier-eligible types (new accounts) | `t3.micro`, `t3.small`, `t4g.micro`, `t4g.small`, `c7i-flex.large`, `m7i-flex.large` | `t2.micro` (legacy only) | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-free-tier-usage.html |
| Free plan + AWS Organizations | Creating/joining an Organization **auto-upgrades** a free plan account to paid, and free-tier credits expire immediately | n/a | https://docs.aws.amazon.com/singlesignon/latest/userguide/enable-identity-center.html , https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html |
| Root user MFA | **Required** for all account types (standalone, management, member). Must register within 35 days of first console sign-in attempt | "MFA is recommended" | https://docs.aws.amazon.com/IAM/latest/UserGuide/enable-mfa-for-root.html |
| Human access guidance | Use federation / **IAM Identity Center** with temporary credentials. IAM users only for cases federation can't cover | "create an IAM admin user" | https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html |
| IMDSv2 | Console Quick Start launches IMDSv2-only since Nov 2023; account-level default setting since Mar 2024; instance types released from mid-2024 are IMDSv2-only by default; AL2023 uses IMDSv2 by default | IMDSv1 default | https://aws.amazon.com/blogs/aws/amazon-ec2-instance-metadata-service-imdsv2-by-default/ , https://aws.amazon.com/about-aws/whats-new/2024/03/set-imdsv2-default-new-instance-launches/ |
| Amazon Linux 2 | **End of support 2026-06-30**. AL2023 supported to June 2029 | "AL2 is the default AMI" | https://aws.amazon.com/amazon-linux-2/faqs/ |
| Public IPv4 | USD 0.005/hour per public IPv4 address, in-use or idle (charge started Feb 2024; that date is **unverified** here) | "public IPs are free" | https://aws.amazon.com/vpc/pricing/ |
| Burstable (T) default mode | T8i, T4g, T3a, T3 launch as `unlimited` by default, so sustained high CPU can cost extra | "T instances just throttle" | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/burstable-performance-instances-unlimited-mode.html |
| AZ name mapping | Accounts created **from Nov 2025** get the same AZ-name to physical-AZ mapping. Older accounts in the oldest Regions have per-account mapping. AZ IDs (e.g. `use1-az1`) are always the same physical AZ | "us-east-1a is the same for everyone" or "always shuffled" | https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-availability-zones.html |
| Global infra size | 39 Regions, 124 AZs, 750+ CloudFront PoPs; Saudi Arabia and Chile announced (2 Regions, 7 AZs) | varies by source | https://aws.amazon.com/about-aws/global-infrastructure/ |
| IAM Identity Center | Formerly AWS SSO (renamed July 26, 2022). Aug 5, 2026: account-access management became optional for new organization instances | "AWS SSO" | https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html , https://aws.amazon.com/about-aws/whats-new/2026/08/aws-identity-center-accounts-optional/ |
| Cloud Practitioner exam | CLF-C02 is still the current exam guide. Domains: Cloud Concepts 24%, Security & Compliance 30%, Cloud Tech & Services 34%, Billing/Pricing/Support 12% | CLF-C01 | https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02.html |

**Discrepancies in AWS's own docs:**
- S3 Express One Zone request-cost saving is "80 percent lower" on the S3 Welcome page but "50 percent lower" on the storage-classes page. Avoid quoting either number in buddy notes.
- The "50 TB" max object size vs the 53.7 TB real ceiling (above).

---

## 1. Broad survey: what beginner material covers

- **AWS Cloud Practitioner Essentials** (Skill Builder) has 13 modules: Intro to Cloud; Compute in the Cloud; Exploring
  Compute Services; Going Global; Networking; Storage; Databases; AI/ML & Analytics; Security; Monitoring/Compliance/
  Governance; Pricing & Support; Migrating; Well-Architected (https://aws.amazon.com/blogs/training-and-certification/new-aws-cloud-practitioner-essentials/, https://skillbuilder.aws/learn/94T2BEN85A/aws-cloud-practitioner-essentials/8D79F3AVR7).
- **CLF-C02 exam guide**, the parts relevant to our slice
  (https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain2.html,
  https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain3.html):
  - 2.1 Shared responsibility, and how it shifts by service (EC2 vs managed services).
  - 2.3 IAM, "Importance of protecting the AWS root user account", least privilege, IAM Identity Center; access keys,
    password policies, credential storage; MFA, cross-account roles; "Defining groups, users, custom policies, and
    managed policies"; tasks only the root user can do; federated identity.
  - 2.2 Encryption at rest / in transit.
  - 3.1 Console vs CLI/SDK/API vs IaC.
  - 3.2 Regions, AZs, edge locations; HA via multiple AZs; "Availability Zones do not share single points of failure".
  - 3.3 "appropriate use of various Amazon EC2 instance types (for example, compute optimized, storage optimized)"; auto
    scaling = elasticity; load balancers.
  - 3.5 VPC components (subnets, gateways); security groups vs network ACLs.
  - 3.6 object storage uses; "differences in Amazon S3 storage classes"; block storage (EBS, instance store); lifecycle
    policies.
  - 4 Billing (Budgets, Cost Explorer, Pricing Calculator, Free Tier, EC2 purchasing options).
- Out of scope for the target candidate: coding, architecture design, troubleshooting, implementation.

**Takeaway for a 2-week slice.** Cloud-practitioner depth plus light hands-on (create a bucket, launch a t3/t4g micro,
SSH in, attach a role). Cut: databases, containers, Lambda, CloudFront, Route 53, KMS internals, Organizations/SCPs,
VPC design beyond "default VPC + security group", Auto Scaling/ELB (mention at most). The cut topics are also useful as
**out-of-plan** probes: the buddy should say "not on our plan" rather than leak or invent.

---

## 2. Candidate concepts, learning order, prerequisites, size

IDs are working labels. "1h?" means whether the node fits roughly one hour of reading plus a small hands-on.

| # | ID | Concept | Prereqs | Fits ~1h? | Suggested day |
|---|---|---|---|---|---|
| 1 | F1 | What cloud computing / AWS is; ways to use AWS (console, CLI, SDK, API) | baseline | Yes (short) | D1 |
| 2 | F4 | Global infrastructure: Regions, AZs, edge; regional vs zonal vs global resources | F1 | Yes | D1 |
| 3 | F2 | AWS account and root user; sign-in; root MFA | F1 | Yes (short) | D2 |
| 4 | F3 | Billing basics and Free Tier (Free vs Paid plan, credits, Budgets, zero-spend budget, Cost Explorer, cleaning up) | F2 | Yes | D2 |
| 5 | F5 | Shared responsibility model | F1, F4 | Yes (short) | D3 |
| 6 | I1 | IAM overview: authentication vs authorization, principals, identities, IAM is global and free | F2 | Yes (short) | D3 |
| 7 | I2 | IAM users, user groups, credentials (password, access keys, MFA) | I1 | Yes | D4 |
| 8 | I3 | IAM policies: JSON anatomy, ARNs, managed vs inline, identity-based vs resource-based (concept only) | I2 | ~1h, dense | D4-D5 |
| 9 | I4 | Policy evaluation and least privilege: implicit deny, explicit deny wins, AWS managed policies, Access Analyzer | I3 | Yes | D5 |
| 10 | I5 | IAM roles and temporary credentials: trust policy, AssumeRole/STS, service roles | I3, I4 | ~1h, conceptually hard | D6 |
| 11 | I6 | Human access best practice: IAM Identity Center / federation (and why a solo learner may still use an IAM user) | I2, I5 | Yes (short) | D6 |
| 12 | S1 | S3 fundamentals: object storage, buckets, objects, keys, prefixes ("folders"), naming, Region, durability, consistency, size limits | F4, I1 | Yes | D7 |
| 13 | S2 | S3 access control and secure defaults: private by default, Block Public Access, Object Ownership/ACLs disabled, bucket policies, IAM+bucket policy together | S1, I3, I4 | ~1h, dense | D8 |
| 14 | S3e | S3 encryption: SSE-S3 default, SSE-KMS/DSSE-KMS, SSE-C disabled by default, TLS in transit | S1 | Yes (short) | D8 |
| 15 | S4 | S3 storage classes and Lifecycle rules | S1, F4 | Yes | D9 |
| 16 | S5 | S3 Versioning (delete markers, suspended vs enabled, cost), brief mention of MFA delete / Object Lock / replication | S1 | Yes | D9 |
| 17 | S6 | Sharing from S3: presigned URLs; static website hosting (overview) | S2, I5 | Yes | D10 |
| 18 | E1 | EC2 fundamentals: instance, AMI, instance types and naming, launching | F4, F3 | Yes | D10-D11 |
| 19 | E2 | EC2 networking minimum: default VPC/subnets, public vs private IP, security groups (stateful, allow-only), common ports, public IPv4 charge | E1 | Yes | D11 |
| 20 | E3 | Key pairs and connecting: SSH, EC2 Instance Connect, Session Manager | E1, E2 | Yes | D12 |
| 21 | E4 | EC2 storage: EBS volumes, snapshots, instance store, delete-on-termination | E1, F4 | Yes | D12 |
| 22 | E5 | Instance lifecycle and billing: states, stop/hibernate/terminate/reboot, per-second billing, purchasing options (On-Demand, Savings Plans, RIs, Spot, Dedicated) | E1, E4, F3 | Yes | D13 |
| 23 | E6 | User data and instance metadata (IMDSv2) | E1, E3 | Yes | D13 |
| 24 | E7 | IAM roles for EC2 / instance profiles; capstone "EC2 reads from S3 without keys" | I5, E6, S2 | Yes | D14 |

Prerequisite edges, for the graph builder:

```
F1 -> F4, F2, F5, I1(via F2)
F4 -> F5, S1, S4, E1, E4
F2 -> F3, I1
F3 -> E1, E5
I1 -> I2 -> I3 -> I4 -> I5 -> I6
I2 -> I6
I3,I4 -> S2
S1 -> S2, S3e, S4, S5
S2 + I5 -> S6
E1 -> E2 -> E3
E1 -> E4 -> E5
E1 + E3 -> E6
I5 + E6 + S2 -> E7
```

Sizing notes:
- **I3** and **S2** are the densest. They may need to be split into I3a "anatomy + ARNs" and I3b "managed vs inline;
  identity vs resource-based", and S2a "BPA + ownership" and S2b "bucket policies".
- **F1** and **F5** are short and could be merged if a day is light.
- Alternative order considered: EC2 before S3. Most beginner courses (Cloud Practitioner Essentials) teach compute
  first. S3 before EC2 fits better here: S3 is cheap and safe for a hands-on beginner, reuses IAM policies immediately,
  and puts the IAM→EC2 role capstone at the end. Trade-off: the buddy then can't use EC2 examples when explaining S3
  (e.g. "access S3 from an app on a server").

---

## 3. Per-concept details

Format per concept: **Key points** / **Docs** / **Shaky-note candidates** (common misconceptions or genuinely confusing
parts) / **Vocabulary** (terms, synonyms, abbreviations, CLI/API/console/ARN names).

### F1: What cloud computing / AWS is

**Key points**
- AWS (Amazon Web Services) rents computing resources on demand: servers, storage, databases and more, with
  pay-as-you-go pricing. You pay for what you use rather than buying hardware up front
  (https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html#PayingforStorage,
  https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html).
- Each capability is a separate **service** (EC2 = compute, S3 = storage, IAM = access control). Signing up gives
  access to all services; you are charged only for what you use.
- Four ways to use AWS: **AWS Management Console** (web UI), **AWS CLI** (command line), **AWS SDKs** (code libraries),
  and the raw **HTTP APIs**. CloudFormation / IaC is a fifth, declarative way. The console itself calls the same APIs
  (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html#access-ec2).
- Every request to AWS is signed with credentials (SigV4) unless it is anonymous. The SDK/CLI does the signing.
- Deployment models: cloud, hybrid, on-premises (CLF-C02 3.1).
- Elasticity: scale up/down on demand (EC2 intro page).

**Shaky candidates**
- "The cloud" is someone else's data centers, not something magical or "in the sky". Many beginners half-know this.
- Console vs CLI vs SDK are just different front-ends to the same API, not different products. Beginners often think
  the CLI is "more powerful".
- "AWS" vs "Amazon" naming: some services are "Amazon X" (Amazon S3, Amazon EC2) and some "AWS X" (AWS IAM, AWS
  Budgets). There is no functional meaning to the prefix **(unverified: AWS has never officially explained the
  convention)**.

**Vocabulary**: AWS, Amazon Web Services, cloud, cloud computing, cloud provider, service, pay-as-you-go, on-demand,
elasticity, scalability, AWS Management Console, console, AWS CLI, `aws` command, SDK, boto3 (Python SDK), API, REST,
IaC, infrastructure as code, CloudFormation, CloudShell, SigV4, Signature Version 4.

### F4: Global infrastructure (Regions, AZs, edge)

**Key points**
- A **Region** is a separate geographic area, designed to be isolated from other Regions. Most resources are
  **regional**: you pick a Region and only see that Region's resources. AWS does not replicate across Regions for you
  (https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-regions-availability-zones.html).
- Each Region has **at least three Availability Zones**. An AZ is "one or more discrete data centers, each with
  redundant power, networking, and connectivity, and housed in separate facilities". AZs are linked by low-latency
  metro fiber (https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-availability-zones.html).
- **Zonal** resources live in one AZ. Best practice is to spread across multiple AZs for high availability; AZs "do not
  share single points of failure" (CLF-C02 3.2).
- Region code e.g. `us-east-1`; AZ code = Region code + letter (`us-east-2a`); **AZ ID** e.g. `use2-az1` is the same
  physical AZ in every account. Accounts created from Nov 2025 get consistent name mapping; older accounts in the oldest
  Regions have per-account mapping (same source).
- Choose a Region by latency, cost, compliance/data residency, and service availability. Some Regions are opt-in
  (https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html#Regions).
- Scale (Sept 2026): 39 Regions, 124 AZs, 750+ edge PoPs; Saudi Arabia and Chile announced
  (https://aws.amazon.com/about-aws/global-infrastructure/).
- Other location types: Local Zones, Wavelength Zones (5G), edge locations (CloudFront). Mention only.
- Some services are **global**: IAM resources have no Region (the Region field of an IAM ARN is blank)
  (https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html).

**Shaky candidates**
- AZ ≠ data center. An AZ can be several data centers.
- `us-east-1a` in my account may not be `us-east-1a` in yours (older accounts). The new Nov-2025 change makes this
  doubly confusing.
- "My resources disappeared!" is usually just the wrong Region selected in the console.
- Edge locations are not Regions and you can't launch EC2 there.
- Which services are global vs regional (IAM global; S3 buckets regional even though the console lists all buckets
  together).

**Vocabulary**: Region, AWS Region, region code, `us-east-1` (N. Virginia), `eu-west-1` (Ireland), Availability Zone,
AZ, AZ ID, zone, zonal, regional, global service, data center, edge location, point of presence, PoP, Local Zone,
Wavelength Zone, partition, `aws`, `aws-cn`, `aws-us-gov`, `aws-eusc`, opt-in Region, high availability, HA, fault
tolerance, latency, data residency, `aws ec2 describe-availability-zones`, `describe-regions`, Global View.

### F2: AWS account and root user

**Key points**
- A new account starts with one identity, the **root user**: the sign-up email + password, with "complete access to
  all AWS services and resources in the account"
  (https://docs.aws.amazon.com/IAM/latest/UserGuide/id_root-user.html).
- Don't use root for everyday tasks. Use it only for root-only tasks: changing the account email/root password/root
  keys, closing a standalone account, restoring IAM permissions if the only admin locked themselves out, activating
  IAM access to billing, some billing/tax tasks, enabling S3 MFA delete, and removing a bucket policy that denies
  everyone (same page).
- **MFA is required** for root in all account types. It must be registered within 35 days of first console sign-in
  attempt. Supported: passkeys/security keys (FIDO, recommended), virtual authenticator apps (TOTP), hardware TOTP
  tokens (https://docs.aws.amazon.com/IAM/latest/UserGuide/enable-mfa-for-root.html).
- Don't create root access keys (https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html).
- The account is identified by a 12-digit **account ID**. The root user's ARN form is `arn:aws:iam::123456789012:root`
  (https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html).
- Identity-based policies can't be attached to root and root can't have a permissions boundary. Root *is* affected by
  SCPs/RCPs in an Organization (https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html#access_policies-root).
- Organizations can centrally remove member-account root credentials. Advanced; mention only.

**Shaky candidates**
- "Root user" vs "root" on Linux (`sudo`, EC2). The name collision is a genuine source of confusion.
- `arn:aws:iam::ACCOUNT:root` in a policy means "the whole account", not "only the root user". This is a notorious
  confusion **(the policy meaning is from general IAM knowledge; the principal-element doc was not fetched)**.
- Beginners think they can't restrict root at all. Standalone: effectively true. In Organizations, SCPs apply.
- MFA used to be optional; older tutorials say "recommended".

**Vocabulary**: AWS account, account ID, 12-digit account number, account alias, root user, root account, account
owner, root credentials, root email, MFA, multi-factor authentication, 2FA, passkey, security key, FIDO, YubiKey,
virtual MFA, authenticator app, TOTP, hardware token, sign-in URL, `arn:aws:iam::123456789012:root`, close account.

### F3: Billing basics and Free Tier

**Key points**
- New accounts (on/after July 15, 2025): USD 100 credit at sign-up plus up to USD 100 more for completing activities
  (e.g. with EC2, Bedrock, Budgets); over 30 always-free services
  (https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html,
  https://aws.amazon.com/about-aws/whats-new/2025/07/aws-free-tier-credits-month-free-plan/).
- **Free plan**: no charges. Ends after 6 months or when credits are used up, whichever is first. Then the account
  closes; AWS keeps content 90 days, and you can upgrade to Paid within that window. The free plan excludes things
  that could burn credits (e.g. Savings Plans, Reserved Instances, some Marketplace). It auto-upgrades to Paid if you
  join AWS Organizations, set up Control Tower, etc.
- **Paid plan**: all services. Pay-as-you-go beyond credits; includes short-term trials.
- Legacy accounts (before July 15, 2025) keep the old 12-month / always-free / trials model
  (https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/billing-free-tier.html).
- **AWS Budgets**: cost/usage budgets with alerts on actual and forecasted spend, via email/SNS. Data updates up to 3
  times a day, so alerts lag real spend
  (https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html). Beginners commonly set up
  a **zero-spend budget** template **(template name from memory; unverified in this pass)**.
- **Cost Explorer**: view up to the last 13 months and forecast 12 months
  (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html#ec2-pricing-additional). **Pricing Calculator**:
  estimates before you build (https://calculator.aws/).
- Things that cost money while "idle": EBS volumes, Elastic IPs, public IPv4 addresses (USD 0.005/hr)
  (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-lifecycle.html, https://aws.amazon.com/vpc/pricing/).
- S3 pricing dimensions: storage, requests & retrievals, data transfer (data **in** from the internet is free),
  management features, replication (https://aws.amazon.com/s3/pricing/).

**Shaky candidates**
- "Free tier = t2.micro for 12 months" is outdated for new accounts.
- A budget alert is not a spending cap: it notifies (and can trigger actions) but doesn't stop spend by itself. Alerts
  are also delayed.
- On the Free plan you "can't be charged", but the account **closes** at 6 months unless upgraded. Few people expect
  that.
- Stopped instance = free? Only the compute is free; EBS storage (and public IPv4 / EIPs) still bill.
- Resources in *other* Regions you forgot about.

**Vocabulary**: Free Tier, AWS Free Tier, Free plan, free account plan, Paid plan, credits, promotional credits,
always free, short-term trial, 12-month free tier (legacy), pay-as-you-go, on-demand pricing, Billing and Cost
Management console, AWS Budgets, budget, cost budget, usage budget, zero-spend budget, budget alert, forecasted,
Cost Explorer, AWS Pricing Calculator, bill, invoice, cost allocation tags, `aws-portal:ViewBilling`, data transfer
out, egress.

### F5: Shared responsibility model

**Key points**
- AWS: security **of** the cloud (hardware, facilities, network, virtualization). Customer: security **in** the cloud
  (data, IAM, OS configuration, apps, firewall configuration)
  (https://aws.amazon.com/compliance/shared-responsibility-model/).
- The split shifts by service type. With EC2 (IaaS) the customer manages the guest OS including patches, applications
  and "the AWS-provided firewall" (security groups). With abstracted services (e.g. S3) the customer manages data,
  encryption options, classification and IAM permissions (same source).
- Control types: **inherited** (e.g. physical security), **shared** (patch management, configuration management,
  awareness & training; each party does its own layer), **customer-specific** (same source).
- CLF-C02 2.1 expects you to describe how it shifts for RDS, Lambda and EC2.

**Shaky candidates**
- "AWS handles security" is wrong. Misconfiguration (e.g. a public bucket) is the customer's responsibility.
- Patching: AWS patches the host; the customer patches the guest OS on EC2. People mix these up.
- Encryption: AWS provides the options; choosing and managing keys is on the customer.

**Vocabulary**: shared responsibility model, security of the cloud, security in the cloud, inherited controls,
shared controls, customer-specific controls, IaaS, PaaS, SaaS, managed service, guest OS, host, hypervisor, patching,
compliance, AWS Artifact.

**Leak warning**: the official page's examples name EC2, security groups, S3 and DynamoDB. See §5.

### I1: IAM overview

**Key points**
- IAM (AWS Identity and Access Management) controls "who is authenticated (signed in) and authorized (has
  permissions) to use resources" (https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html).
- **Authentication** = proving who you are. **Authorization** = what you may do. A **principal** is an entity that can
  make requests: root user, IAM user, role (session), federated user, or AWS service
  (https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html#id_roles_additional-resources).
- IAM identities: users, user groups, roles. IAM *entities* (things that authenticate) are users and roles; groups are
  not principals (https://docs.aws.amazon.com/IAM/latest/UserGuide/id.html).
- IAM, IAM Identity Center and STS cost nothing extra (introduction page).
- IAM is **eventually consistent**: changes take time to propagate, so keep IAM changes out of critical code paths
  (introduction page).
- IAM is global. ARNs have an empty Region field: `arn:aws:iam::123456789012:user/John`
  (https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html).
- Access by default: new identities have **no permissions** until granted.

**Shaky candidates**
- AuthN vs AuthZ are easy to swap.
- "IAM" as a word vs "I am" (see collisions).
- Eventual consistency: "I just added the permission and it still says AccessDenied".
- IAM Identity Center is part of the "IAM" family but a different service.

**Vocabulary**: IAM, AWS Identity and Access Management, identity, principal, entity, authentication, authN,
authorization, authZ, permission, access, credentials, request context, least privilege, IAM console, AWS STS,
Security Token Service, eventual consistency, `iam.amazonaws.com`, `aws sts get-caller-identity`, `GetCallerIdentity`.

### I2: IAM users, groups and credentials

**Key points**
- An **IAM user** is an identity in your account for one person or application, with long-term credentials: a console
  password and/or access keys (https://docs.aws.amazon.com/IAM/latest/UserGuide/id.html).
- **Access keys** = access key ID (e.g. `AKIAIOSFODNN7EXAMPLE`) + secret access key. The secret is shown only at
  creation. Max **2** per user. Don't create them for root. Don't put them in code; the shared credentials file stores
  them in plaintext (https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html).
- Unique-ID prefixes: `AIDA` user, `AGPA` group, `AROA` role, `ANPA` managed policy, `AIPA` instance profile, `AKIA`
  long-term access key, `ASIA` temporary (STS) key
  (https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html#identifiers-prefixes).
- **User groups**: collections of users. Attach policies once and every member gets them. A user can be in many groups
  (max 10). Groups **can't be nested**. There is **no default "all users" group**. A group **can't be a Principal** in a
  policy (https://docs.aws.amazon.com/IAM/latest/UserGuide/id_groups.html,
  https://docs.aws.amazon.com/general/latest/gr/iam-service.html).
- Quotas: 5,000 users/account; 300 groups/account (adjustable); 10 managed policies per user (adjustable to 20); 8 MFA
  devices per user (https://docs.aws.amazon.com/general/latest/gr/iam-service.html).
- Names are case-insensitive for uniqueness (you can't have `ADMINS` and `admins`) but case-sensitive in ARNs/policies
  (https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_iam-quotas.html,
  https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html).
- MFA can be enabled per IAM user. Phishing-resistant passkeys/security keys are preferred
  (https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#enable-mfa-for-privileged-users).
- AWS now recommends IAM users **only** where federation can't be used: workloads that can't use roles, third-party
  clients, CodeCommit, Keyspaces, emergency access
  (https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html#id_which-to-choose).

**Shaky candidates**
- Older tutorials say "create an IAM admin user for daily use". Current guidance is Identity Center. Many learners on
  a single personal account still create one IAM admin user. A genuine grey area and a good "I'm not sure which is
  right for us" note.
- Groups vs roles: both "bundle permissions". Groups are for *users*; roles are *assumed*.
- Deleting a user and re-creating one with the same name gets a new unique ID. Policies that name the user by ARN
  apply to the new user; policies that use the unique ID do not.
- Access key ID is not secret; the secret access key is.

**Vocabulary**: IAM user, user, user group, IAM group, group, member, console password, login profile, password
policy, access key, access key ID, secret access key, secret key, long-term credentials, programmatic access,
`~/.aws/credentials`, `aws configure`, profile (CLI profile), MFA device, virtual MFA, `AKIA…`, `AIDA…`, `AGPA…`,
Access Advisor, last accessed, credential report, `aws iam create-user`, `create-group`, `add-user-to-group`,
`create-access-key`, `CreateUser`, `CreateAccessKey`, `arn:aws:iam::123456789012:user/Bob`,
`arn:aws:iam::123456789012:group/Developers`, path (`/division_abc/`).

### I3: IAM policies (anatomy)

**Key points**
- A policy is a (mostly JSON) document that, attached to an identity or resource, defines permissions. AWS evaluates
  policies on every request, whichever way the request is made: console, CLI or API
  (https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html).
- Elements: `Version` (use `2012-10-17`), `Statement` (one or more), `Sid` (optional), `Effect` (`Allow`/`Deny`),
  `Action`, `Resource`, `Condition` (optional), `Principal` (only in resource-based policies; forbidden in identity
  policies because the principal is implied) (same page).
- Action format `service:Action`, wildcards allowed (`s3:Get*`, `iam:*AccessKey*`). Resource is an **ARN**:
  `arn:partition:service:region:account:resource`. IAM ARNs leave the Region blank
  (https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html).
- **Identity-based** policies attach to users/groups/roles and come as:
  - **AWS managed** (created by AWS, shared by all customers)
  - **customer managed** (yours, reusable, versioned; max 5 versions)
  - **inline** (embedded 1:1 in one identity, deleted with it)
  (https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html#policies_id-based).
- **Resource-based** policies attach to a resource (examples: S3 bucket policy, role trust policy) and must name a
  Principal. They are always inline (same page). *(Leak hazard: see §5.)*
- There are nine policy types in total (identity, resource, VPC endpoint, permissions boundary, SCP, RCP, ACL, RAM
  share, session). A beginner needs only the first two plus awareness that the others "limit but don't grant"
  (same page).
- Size limits: managed policy 6,144 chars; inline per user 2,048, per role 10,240, per group 5,120 (whitespace not
  counted) (https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_iam-quotas.html).
- Multiple statements and multiple policies are OR-ed for allows. The console has a visual editor, so JSON isn't
  required (access_policies page).

**Shaky candidates**
- `"Version": "2012-10-17"` is the policy-language version, not "the date I wrote it". A classic beginner mistake is
  to put today's date.
- Why `Principal` is absent in identity policies.
- Incomplete ARNs get wildcard-completed (`arn:aws:sqs` ≡ `arn:aws:sqs:*:*:*`) (identifiers page).
- `Resource: "*"` with an action like `iam:ChangePassword` still only affects yourself.
- Inline vs customer managed: when to use which.

**Vocabulary**: policy, IAM policy, permissions policy, policy document, JSON, statement, `Version`, `2012-10-17`,
`Statement`, `Sid`, `Effect`, `Allow`, `Deny`, `Action`, `NotAction`, `Resource`, `NotResource`, `Condition`,
`Principal`, condition key, `aws:MultiFactorAuthPresent`, `aws:SourceIp`, ARN, Amazon Resource Name, wildcard `*`,
identity-based policy, resource-based policy, managed policy, AWS managed policy, customer managed policy, inline
policy, policy version, visual editor, JSON editor, `aws iam create-policy`, `attach-user-policy`,
`attach-group-policy`, `put-user-policy`, `arn:aws:iam::123456789012:policy/Name`, `arn:aws:iam::aws:policy/...`.

### I4: Policy evaluation and least privilege

**Key points**
- Order: authenticate, then build the request context, then evaluate all applicable policies
  (https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html).
- Default is **implicit deny**. Any **explicit Deny** overrides every Allow. Within one account, identity-based and
  resource-based allows form a **union**: either can allow (same page).
- Permissions boundaries, SCPs/RCPs and session policies only **limit**; the effective permission is the intersection
  (same page). Advanced; awareness only.
- **Least privilege**: grant only what a task needs. Start with AWS managed policies, then tighten with customer
  managed policies, using Access Analyzer policy generation (from CloudTrail activity) and last-accessed info
  (https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html).
- Access levels in policy summaries: List, Read, Write, Permissions management, Tagging
  (https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html#grant-least-priv).
- IAM Access Analyzer: 100+ policy validation checks, and findings for public/cross-account access. External-access
  analysis is free; unused-access analysis and custom policy checks cost extra
  (https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html).
- Common AWS managed policies: `AdministratorAccess`, `PowerUserAccess`, `ReadOnlyAccess`, `AmazonS3ReadOnlyAccess`,
  `AmazonS3FullAccess`, `AmazonEC2FullAccess`, `IAMUserChangePassword` **(names from general knowledge; they are
  standard AWS managed policy names but individual pages were not fetched)**.

**Shaky candidates**
- "Deny wins" vs "more specific wins". IAM has no specificity rule.
- Implicit deny (nothing allows it) vs explicit deny (a statement says Deny). The error message looks the same.
- Cross-account needs **both** sides to allow; same-account needs **either**. Genuinely confusing.
- AWS managed policies can change when AWS updates them, and they're broader than you need.

**Vocabulary**: policy evaluation logic, implicit deny, default deny, explicit deny, explicit allow, AccessDenied,
"not authorized to perform", least privilege, principle of least privilege, AdministratorAccess, ReadOnlyAccess,
PowerUserAccess, job-function policies, IAM Access Analyzer, policy validation, policy generation, findings, last
accessed information, Access Advisor, permissions boundary, SCP, service control policy, RCP, session policy, IAM
policy simulator.

### I5: IAM roles and temporary credentials

**Key points**
- A **role** is an identity with permissions but **no long-term credentials**. Whoever assumes it gets **temporary
  credentials** for a role session (https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html).
- Who can assume a role: IAM users (same or other account), other roles, AWS service principals (e.g. EC2, Lambda, S3
  replication), and external identities via SAML 2.0/OIDC federation (same page).
- Two policies per role: the **trust policy** (a resource-based policy: *who* may assume) and the **permissions
  policy** (*what* the role can do). A trust policy can't use `*` inside a principal ARN (same page).
- Assuming a role is `sts:AssumeRole`. The default session is 1 hour; `DurationSeconds` 900s up to the role's max
  (1–12h). **Role chaining** caps sessions at 1h
  (https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_iam-quotas.html, id_roles page).
- When you assume a role you temporarily give up your own permissions (id_roles, "Delegation").
- **Service role** = a role a service assumes on your behalf, editable by you. **Service-linked role** = owned by the
  service; you can view but not edit its permissions (id_roles page).
- Temporary keys start `ASIA` and need a session token too (identifiers page).
- Best practice: workloads use roles/temporary credentials rather than IAM-user keys
  (https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#bp-workloads-use-roles).
- Quotas: 1,000 roles/account; 20 managed policies per role; trust policy 2,048 chars (adjustable to 8,192)
  (quotas page).

**Shaky candidates**
- "A role is like a group." No: groups hold users; roles are assumed and hand out temporary credentials.
- Trust policy vs permissions policy. Which one says who, and which says what?
- Cross-account needs the trust policy **and** an identity policy on the caller allowing `sts:AssumeRole`.
- Where do temporary credentials "come from"? STS.
- The confused deputy problem / external ID (advanced; mention only).

**Vocabulary**: IAM role, role, assume role, `sts:AssumeRole`, `AssumeRole`, `AssumeRoleWithSAML`,
`AssumeRoleWithWebIdentity`, role session, session name, session duration, `DurationSeconds`, maximum session duration,
temporary credentials, temporary security credentials, session token, `ASIA…`, `AROA…`, trust policy, trust
relationship, permissions policy, service role, service-linked role, `AWSServiceRoleFor…`, service principal (e.g.
`ec2.amazonaws.com`), federation, federated user, identity provider, IdP, SAML 2.0, OIDC, OpenID Connect, role
chaining, switch role, delegation, cross-account access, external ID, confused deputy, IAM Roles Anywhere,
`arn:aws:iam::123456789012:role/S3Access`, `arn:aws:sts::123456789012:assumed-role/RoleName/SessionName`.

### I6: IAM Identity Center and federation (human access)

**Key points**
- Best practice #1: human users should use **federation** and temporary credentials. AWS recommends **IAM Identity
  Center** for centralized access (https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#bp-users-federation-idp).
- Identity Center was formerly **AWS Single Sign-On** (renamed July 26, 2022). The `sso` CLI namespace remains, e.g.
  `aws configure sso` (https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html).
- Users sign in through the **AWS access portal**. **Permission sets** create the roles in accounts.
  **Organization instances** (recommended; live in the Organizations management account; the only kind that manages
  AWS account access) vs **account instances** (single account, apps only; no permission sets, no AWS account access)
  (same page; https://docs.aws.amazon.com/singlesignon/latest/userguide/enable-identity-center.html).
- Enabling an organization instance from a standalone account **creates an AWS Organization**. On a free-tier plan,
  creating an organization auto-upgrades the account to Paid and credits expire immediately (enable-identity-center
  page).
- Identity sources: the Identity Center directory, AD, or an external IdP (Okta, Entra ID, etc.) via SAML/SCIM
  (what-is page).
- Aug 2026: new organization instances can skip account-access management (apps only)
  (https://aws.amazon.com/about-aws/whats-new/2026/08/aws-identity-center-accounts-optional/).

**Shaky candidates**
- **Genuinely confusing for a solo learner on a Free plan**: AWS says "use Identity Center", but doing it the
  recommended way creates an Organization and auto-upgrades the plan. Excellent material for a buddy note like "I
  wasn't sure whether to bother with Identity Center for just us…".
- "SSO" vs "IAM Identity Center" naming.
- Account instance vs organization instance.
- The "IAM users are deprecated" myth. They aren't deprecated; they're just not recommended for humans.

**Vocabulary**: IAM Identity Center, AWS SSO, AWS Single Sign-On, SSO, single sign-on, federation, identity
provider, IdP, access portal, AWS access portal, permission set, organization instance, account instance, identity
source, Identity Center directory, SCIM, SAML, `aws configure sso`, `aws sso login`, workforce identity, AWS
Organizations, management account, member account, account access manager.

### S1: S3 fundamentals

**Key points**
- Amazon S3 (Simple Storage Service) is **object storage**. Data is stored as **objects** in **buckets**. An object is
  the data plus metadata; a **key** is its unique name in the bucket; bucket + key (+ version ID) identifies an object
  (https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html).
- Buckets are created in a Region you choose, and their name and Region **can't be changed** later. Objects never
  leave the Region unless you copy/replicate them (Welcome; UsingBucket pages).
- General purpose bucket names are unique **across all accounts in a partition** (global namespace), unless you use
  the new **account regional namespace** (`name-<acct>-<region>-an`). Names: 3–63 chars; lowercase letters, digits,
  `.` and `-`; start/end alphanumeric; not IP-shaped; reserved prefixes/suffixes (`xn--`, `sthree-`, `amzn-s3-demo-`,
  `-s3alias`, `--ol-s3`, `.mrap`, `--x-s3`, `--table-s3`; `-an` only in the account regional namespace). Avoid dots
  (breaks HTTPS virtual-host addressing) (https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html).
- After deletion, a global-namespace name may be re-created by **someone else**, who could then receive requests
  meant for you. Recommendation: empty the bucket and keep it rather than delete (naming rules page).
- **Flat namespace**: "folders" are just shared key **prefixes** such as `photos/`. The console fakes folders, and
  "Create folder" makes a 0-byte object with a trailing `/`
  (https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-folders.html).
- Object size 0 B to 50 TB. Single PUT ≤ 5 GB; console upload ≤ 160 GB; multipart for larger. Object keys ≤ 1,024
  bytes (upload-objects and using-folders pages).
- **Strong read-after-write consistency** for object PUT/DELETE/LIST in all Regions. Concurrent writers: last writer
  wins; no object locking for concurrent writers. Bucket **config** is eventually consistent (wait ~15 min after first
  enabling versioning) (Welcome, consistency model).
- Durability: designed for 99.999999999% (11 nines) in all classes except RRS
  (https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html#sc-compare).
- No limit on objects per bucket or bucket size. 10,000 buckets per account by default. No buckets inside buckets
  (https://docs.aws.amazon.com/AmazonS3/latest/userguide/BucketRestrictions.html).
- Object URL: `https://bucket.s3.us-west-2.amazonaws.com/photos/puppy.jpg` (virtual-hosted style) (Welcome).
- CLI: high-level `aws s3` (`mb`, `cp`, `ls`, `sync`, `rm`) and low-level `aws s3api` (`create-bucket`,
  `put-object`, ...). Creating outside us-east-1 needs `LocationConstraint` (naming rules page example).
- Four bucket types exist (general purpose, directory, table, vector). A beginner needs only general purpose (Welcome).

**Shaky candidates**
- S3 is not a file system: there are no real folders, rename = copy + delete, and you can't append to an object.
- "Globally unique names" is now nuanced (account regional namespace, Mar 2026).
- The console lists buckets from all Regions together, yet each bucket lives in one Region.
- Consistency: many older sources still say "eventually consistent".
- 5 TB vs 50 TB max object size (Dec 2025 change).
- Durability ≠ availability (11 nines durable, 99.99% available for Standard).

**Vocabulary**: Amazon S3, S3, Simple Storage Service, object storage, bucket, general purpose bucket, directory
bucket, table bucket, vector bucket, object, key, object key, key name, prefix, folder, delimiter, `/`, metadata,
system metadata, user-defined metadata (`x-amz-meta-`), `Content-Type`, ETag, object URL, virtual-hosted-style,
path-style, endpoint, `s3.amazonaws.com`, global namespace, account regional namespace, partition, bucket naming
rules, durability, 11 nines, availability, strong consistency, read-after-write, multipart upload, `PutObject`,
`GetObject`, `ListObjectsV2`, `CreateBucket`, `DeleteObject`, `HeadObject`, `CopyObject`, `aws s3 mb`, `aws s3 cp`,
`aws s3 ls`, `aws s3 sync`, `aws s3 rm`, `aws s3 rb`, `aws s3api create-bucket`, `LocationConstraint`,
`arn:aws:s3:::bucket-name`, `arn:aws:s3:::bucket-name/key`, S3 console, "General purpose buckets", Objects tab,
Properties tab, Permissions tab, Management tab.

### S2: S3 access control and secure defaults

**Key points**
- Buckets and objects are **private by default**. Access is granted through IAM (identity) policies, **bucket
  policies**, ACLs (legacy) and access points (https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html).
- **Block Public Access** (BPA) has 4 independent settings: `BlockPublicAcls`, `IgnorePublicAcls`, `BlockPublicPolicy`,
  `RestrictPublicBuckets`. They apply at organization, account, bucket and access-point levels; S3 enforces the most
  restrictive combination. **All four are on by default for new buckets.** They are not per-object. They override
  policies/ACLs but don't modify them, so turning BPA off re-exposes any existing public policy
  (https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html).
- What counts as "public": an ACL granting `AllUsers`/`AuthenticatedUsers`, or a bucket policy that isn't restricted to
  fixed principals/accounts/IPs/VPCs etc. (e.g. `"Principal": "*"` with no limiting condition) (same page).
- **Object Ownership**: **Bucket owner enforced** (default, ACLs disabled), Bucket owner preferred, or Object writer.
  With ACLs disabled, uploads that set ACLs other than bucket-owner-full-control fail with `AccessControlListNotSupported`
  (https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html).
- **Bucket policy**: a resource-based policy in IAM policy language, attached to the bucket. Only the bucket owner can
  set one. Max 20 KB. Needs a `Principal`. Can grant cross-account access. Wildcards on ARNs let you target prefixes
  or extensions (https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-policies.html, Welcome).
- Bucket ARN `arn:aws:s3:::bucket` vs object ARN `arn:aws:s3:::bucket/*`: `s3:ListBucket` targets the bucket;
  `s3:GetObject` targets objects (example in https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html).
- The account that owns a bucket owns its objects (under the default setting), not the IAM user who uploaded them
  (UsingBucket page).
- A bucket policy that denies everyone can lock out even admins. Root (or central root access in Organizations) can
  delete it (https://docs.aws.amazon.com/IAM/latest/UserGuide/id_root-user.html).
- A bucket policy can't stop S3 Lifecycle deletions/transitions (bucket-policies page).
- IAM Access Analyzer for S3 flags public/shared buckets (BPA page).

**Shaky candidates**
- Bucket policy vs IAM policy: which to use and how they combine. Same account: either allows (union). Explicit deny
  anywhere wins.
- The `bucket` vs `bucket/*` ARN mistake (very common; causes AccessDenied on list or get).
- "I turned off Block Public Access, so it's public now". No: you still need a policy granting public read. BPA only
  blocks.
- ACLs: older tutorials still teach "make public" via ACL. That now fails by default.
- `RestrictPublicBuckets` also blocks named cross-account grants once the policy contains any public statement.
  Advanced and surprising.

**Vocabulary**: private by default, public access, Block Public Access, BPA, `BlockPublicAcls`, `IgnorePublicAcls`,
`BlockPublicPolicy`, `RestrictPublicBuckets`, `PutPublicAccessBlock`, `s3:PutBucketPublicAccessBlock`, account-level
BPA, bucket policy, resource-based policy, `Principal`, `"Principal": "*"`, `aws:SourceIp`, `aws:SourceVpce`, ACL,
access control list, canned ACL, `bucket-owner-full-control`, `AllUsers`, `AuthenticatedUsers`, Object Ownership,
Bucket owner enforced, Bucket owner preferred, Object writer, `AccessControlListNotSupported`, `s3:GetObject`,
`s3:PutObject`, `s3:ListBucket`, `s3:DeleteObject`, `s3:ListAllMyBuckets`, `PutBucketPolicy`,
`aws s3api put-bucket-policy`, `get-bucket-policy-status`, access point, access point policy, IAM Access Analyzer for
S3, AccessDenied, 403 Forbidden.

### S3e: S3 encryption

**Key points**
- All new object uploads are encrypted with **SSE-S3** (Amazon S3 managed keys, AES-256) automatically since Jan 5,
  2023, at no cost (https://docs.aws.amazon.com/AmazonS3/latest/userguide/default-bucket-encryption.html).
- Options: **SSE-S3**; **SSE-KMS** (AWS KMS keys: the AWS managed `aws/s3` key or a customer managed key; KMS
  charges and request quotas apply; **S3 Bucket Keys** reduce KMS cost); **DSSE-KMS** (dual-layer); **SSE-C**
  (customer-provided keys) (same page).
- SSE-C isn't allowed as bucket default encryption, and since **April 6, 2026 it is disabled by default** on new
  buckets. Requests using it get 403 unless re-enabled via PutBucketEncryption. AWS's rationale: KMS customer managed
  keys give the same control (https://aws.amazon.com/about-aws/whats-new/2026/04/s3-default-bucket-security-setting/,
  https://docs.aws.amazon.com/AmazonS3/latest/userguide/default-s3-c-encryption-setting-faq.html).
- Enabling/changing default encryption doesn't re-encrypt existing objects (default-bucket-encryption page).
- SSE-KMS buckets can't serve anonymous static-website requests; you need CloudFront with OAC
  (https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteHosting.html).
- In transit: HTTPS/TLS endpoints. Client-side encryption is also possible **(general; not fetched)**.

**Shaky candidates**
- "Encryption at rest means my data is private." No: anyone with `s3:GetObject` gets plaintext with SSE-S3.
  Encryption ≠ access control. SSE-KMS adds a second permission (on the key).
- SSE-S3 vs SSE-KMS vs SSE-C naming soup.
- Enabling default encryption doesn't retro-encrypt old objects (moot for post-2023 objects).
- SSE-C being disabled by default is brand new (Apr 2026). Older material says it's a normal option.

**Vocabulary**: encryption at rest, encryption in transit, server-side encryption, SSE, SSE-S3, Amazon S3 managed
keys, AES256, SSE-KMS, AWS KMS, Key Management Service, KMS key, CMK (legacy term), customer managed key, AWS
managed key, `aws/s3`, DSSE-KMS, SSE-C, customer-provided keys, S3 Bucket Key, default encryption,
`PutBucketEncryption`, `aws s3api put-bucket-encryption`, `x-amz-server-side-encryption`, client-side encryption,
TLS, HTTPS.

### S4: S3 storage classes and Lifecycle

**Key points** (https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html)
- Default class is **S3 Standard** (`STANDARD`). Each object has its own class.
- The main classes:

  | Class | API name | Availability | AZs | Min duration | Min billable size | Retrieval fee |
  |---|---|---|---|---|---|---|
  | Standard | `STANDARD` | 99.99% | ≥3 | none | none | none |
  | Intelligent-Tiering | `INTELLIGENT_TIERING` | 99.9% | ≥3 | none | none | none, but a per-object monitoring fee |
  | Standard-IA | `STANDARD_IA` | 99.9% | ≥3 | 30 days | 128 KB | yes |
  | One Zone-IA | `ONEZONE_IA` | 99.5% | 1 | 30 days | 128 KB | yes |
  | Glacier Instant Retrieval | `GLACIER_IR` | — | ≥3 | 90 days | 128 KB | yes; millisecond access |
  | Glacier Flexible Retrieval | `GLACIER` | — | ≥3 | 90 days | — | yes; must **restore** first; minutes–hours |
  | Glacier Deep Archive | `DEEP_ARCHIVE` | — | ≥3 | 180 days | — | yes; hours |
  | Express One Zone | `EXPRESS_ONEZONE` | — | 1 | — | — | — |

  Express One Zone lives in directory buckets and gives single-digit ms latency. Reduced Redundancy
  (`REDUCED_REDUNDANCY`) is **not recommended**.
- All classes are designed for 11-nines durability except RRS (99.99%).
- Intelligent-Tiering tiers: Frequent; Infrequent after 30 days without access; Archive Instant after 90 days; optional
  Archive Access (90+ days) and Deep Archive Access (180+ days). Objects < 128 KB aren't monitored.
- "Glacier" storage classes are S3 classes. You don't use the separate Amazon Glacier (vault) service to reach them.
- **Lifecycle** rules: **transition** actions (move to cheaper class after N days) and **expiration** actions (delete).
  They apply to existing and new objects; transitions carry per-request costs; billing changes as soon as an object is
  eligible. Noncurrent-version actions are for versioned buckets. Bucket policies can't block lifecycle actions
  (https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html).

**Shaky candidates**
- The minimum storage duration charge: deleting a Standard-IA object on day 5 still bills 30 days.
- The 128 KB minimum billable size makes IA bad for tiny files.
- One Zone-IA has the same *durability* as Standard-IA but less *availability* and isn't resilient to losing an AZ.
  People conflate durability and availability.
- Glacier Instant vs Flexible vs Deep Archive naming. Instant Retrieval doesn't need a restore; the other two do.
- Intelligent-Tiering "has no retrieval fees" but charges monitoring.

**Vocabulary**: storage class, S3 Standard, Standard-IA, S3 Standard-Infrequent Access, One Zone-IA, S3 One
Zone-Infrequent Access, Z-IA, Intelligent-Tiering, INT, S3 Glacier Instant Retrieval, Glacier IR, S3 Glacier Flexible
Retrieval, S3 Glacier Deep Archive, Express One Zone, RRS, Reduced Redundancy Storage, `STANDARD`, `STANDARD_IA`,
`ONEZONE_IA`, `INTELLIGENT_TIERING`, `GLACIER_IR`, `GLACIER`, `DEEP_ARCHIVE`, `EXPRESS_ONEZONE`, access tier, archive
tier, restore, `RestoreObject`, retrieval fee, minimum storage duration, minimum billable object size, Storage Class
Analysis, lifecycle, S3 Lifecycle, lifecycle rule, lifecycle configuration, transition, expiration, noncurrent version
expiration, abort incomplete multipart upload, `PutBucketLifecycleConfiguration`,
`aws s3api put-bucket-lifecycle-configuration`.

### S5: S3 Versioning

**Key points** (https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html)
- Three bucket states: **Unversioned** (default), **Versioning-enabled**, **Versioning-suspended**. Once enabled, a
  bucket can never return to unversioned; it can only be suspended.
- Each new write gets a unique **version ID**. Objects that existed before enabling have version ID `null`.
- DELETE without a version ID inserts a **delete marker**, which becomes the current version. Recover by deleting the
  marker or by restoring an older version. Overwrite = new version.
- Every version is a full copy and is **billed as a full object**. Pair versioning with lifecycle
  noncurrent-version expiration.
- Wait ~15 min after first enabling versioning before writes (propagation)
  (https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html#ConsistencyModel).
- **MFA delete** can only be configured by the root user
  (https://docs.aws.amazon.com/IAM/latest/UserGuide/id_root-user.html).
- Related, awareness only: Object Lock (WORM, requires versioning **(unverified detail)**) and replication (CRR/SRR)
  (Welcome).

**Shaky candidates**
- "Delete" in a versioned bucket doesn't free storage. The data stays until versions are permanently deleted.
- Suspending ≠ disabling. Existing versions stay.
- The `null` version ID.
- The console's "Show versions" toggle hides this complexity.

**Vocabulary**: versioning, S3 Versioning, bucket versioning, version ID, `null` version, current version, noncurrent
version, delete marker, versioning-enabled, versioning-suspended, unversioned, MFA delete, Object Lock, WORM,
retention, legal hold, replication, CRR, Cross-Region Replication, SRR, `PutBucketVersioning`,
`aws s3api put-bucket-versioning`, `ListObjectVersions`, "Show versions".

### S6: Sharing from S3 (presigned URLs, static website hosting)

**Key points**
- A **presigned URL** grants time-limited access to one object (GET, PUT, HEAD...) without changing bucket policy. It
  uses the *creator's* credentials and permissions. Anyone holding it can use it until expiry (bearer token)
  (https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html).
- Expiry: console 1 min–12 h; CLI/SDK up to **7 days** with IAM user credentials (SigV4). With temporary credentials
  (role/STS/EC2 instance role, ~6 h) the URL dies when the credentials expire, even if a longer time was set (same page).
- Expiry is checked at request start, so a download that started before expiry finishes (same page).
- Common errors: 403 (creator lacks permission), `SignatureDoesNotMatch` (clock skew, proxies), `ExpiredToken` (same
  page).
- **Static website hosting**: website endpoint, HTTP only, needs public read (BPA off + bucket policy). AWS now
  recommends Amplify Hosting or CloudFront + OAC for HTTPS and to keep BPA on
  (https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteHosting.html,
  https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingBucket.html).
- Bucket names with dots are fine only for website hosting (naming rules page).

**Shaky candidates**
- "Presigned URL = public object." No: the object stays private; the URL carries a signature.
- Why a URL made from an EC2 role or SSO session expires early (surprises everyone).
- A presigned PUT overwrites any object with the same key.
- Static website endpoint vs REST endpoint; HTTP-only.

**Vocabulary**: presigned URL, pre-signed URL, signed URL (CloudFront term; don't conflate), expiration, `X-Amz-Expires`,
`X-Amz-Signature`, `aws s3 presign`, `generate_presigned_url` (boto3), bearer token, `s3:signatureAge`, static website
hosting, website endpoint, index document, error document, `index.html`, CloudFront, OAC, origin access control,
Amplify Hosting, CORS.

### E1: EC2 fundamentals (instances, AMIs, instance types)

**Key points**
- Amazon EC2 (Elastic Compute Cloud) provides on-demand virtual servers called **instances**
  (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html).
- An **AMI** (Amazon Machine Image) is the template (OS + software + block device mapping) you must specify at
  launch. AMIs are Region-specific (copy to use elsewhere) and also specific to OS, CPU architecture, root volume type
  and virtualization type. Sources: AWS, public/community, shared, Marketplace (paid), your own
  (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AMIs.html).
- The **instance type** fixes CPU/memory/network/storage. Name = series + generation + options + `.` + size, e.g.
  `c7gn.xlarge` = compute-optimized, gen 7, Graviton, network-optimized, xlarge
  (https://docs.aws.amazon.com/ec2/latest/instancetypes/instance-type-names.html).
  - Series letters: M general purpose, C compute, R memory, T burstable, I/D storage, G/P GPU, X/U/Z memory-heavy,
    Inf/Trn AI chips, Mac.
  - Option letters: a AMD, g Graviton (Arm), i Intel, d local NVMe instance store, n network, e extra, z high
    frequency, b block storage, flex.
- Worked examples:
  - `t3.micro` = burstable, gen 3, micro.
  - `t4g.small` = burstable, gen 4, Graviton.
  - `c7i-flex.large` = compute, gen 7, Intel, Flex.
  - `m7i-flex.large` = general purpose, gen 7, Intel, Flex.
- **Burstable T** instances earn CPU credits. T3/T3a/T4g/T8i launch as `unlimited` by default, so sustained high CPU
  can cost extra (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/burstable-performance-instances-unlimited-mode.html).
- Free-Tier-eligible types (new accounts): `t3.micro`, `t3.small`, `t4g.micro`, `t4g.small`, `c7i-flex.large`,
  `m7i-flex.large`. Filter with `aws ec2 describe-instance-types --filters Name=free-tier-eligible,Values=true`
  (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-free-tier-usage.html).
- Launching: the console "Launch instance" wizard asks for name/tags, AMI, instance type, key pair, network settings /
  security group, storage, and Advanced details (IAM instance profile, user data, metadata options). CLI:
  `aws ec2 run-instances`. *(The wizard touches nearly every later EC2 node; see §5.)*
- Default AMI choice today: **Amazon Linux 2023**. AL2 reached end of support 2026-06-30
  (https://aws.amazon.com/amazon-linux-2/faqs/).
- Related compute services (mention only): Lightsail, ECS/EKS, Lambda, Auto Scaling, ELB (EC2 intro page).

**Shaky candidates**
- Graviton (Arm, `g`) AMIs are not interchangeable with x86 AMIs. Launch fails or the wrong AMI appears. Very common.
- "micro/small/large" sizes are relative within a family, not absolute.
- T-instance CPU credits / unlimited mode surprises.
- An AMI ID differs per Region for the "same" image.
- `t2.micro` Free Tier advice in old tutorials.

**Vocabulary**: Amazon EC2, EC2, Elastic Compute Cloud, instance, EC2 instance, virtual machine, VM, virtual server,
server, AMI, Amazon Machine Image, image, `ami-0abc…`, Amazon Linux 2023, AL2023, Amazon Linux 2, AL2, Ubuntu, Windows
Server, AWS Marketplace, community AMI, instance type, instance family, series, generation, size, `nano`, `micro`,
`small`, `medium`, `large`, `xlarge`, `2xlarge`, `metal`, vCPU, general purpose, compute optimized, memory optimized,
storage optimized, accelerated computing, burstable, T instances, CPU credits, unlimited mode, standard mode,
Graviton, Arm64, x86_64, Nitro, Flex, `t3.micro`, `t4g.micro`, `c7i-flex.large`, launch, launch instance wizard,
launch template, instance ID `i-0123…`, `aws ec2 run-instances`, `describe-instances`, `ec2:RunInstances`, EC2 console,
EC2 Dashboard, `arn:aws:ec2:region:account:instance/i-…`.

### E2: EC2 networking minimum (default VPC, IPs, security groups)

**Key points**
- Every Region has a **default VPC** with a public subnet per AZ, an internet gateway and DNS enabled, so you can
  launch immediately (https://docs.aws.amazon.com/vpc/latest/userguide/default-vpc.html).
- An instance lives in one subnet, which is in one AZ. A public IPv4 is auto-assigned in default subnets **(detail
  from default-subnet docs, not fetched this pass)**. **Public IPv4 addresses cost USD 0.005/hr**
  (https://aws.amazon.com/vpc/pricing/).
- A **security group** is a virtual firewall attached to the instance's network interface
  (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html,
  https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html):
  - Rules are **allow only**; there are no deny rules.
  - A **new** SG has no inbound rules and one allow-all outbound rule.
  - SGs are **stateful**: return traffic is automatically allowed.
  - Multiple SGs per instance aggregate their rules. Changes apply immediately.
  - If you don't pick one, the VPC's default SG is used.
  - A rule = protocol + port range + source/destination (CIDR, prefix list, or another SG ID).
  - SGs are free.
- Common ports: 22 SSH, 80 HTTP, 443 HTTPS, 3389 RDP. `0.0.0.0/0` = anywhere; `/32` = single IP.
- Network ACLs are subnet-level and **stateless** (CLF-C02 3.5). Awareness only.
- Stop/start changes the public IPv4 (unless it's an Elastic IP); private IP is kept
  (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-lifecycle.html).

**Shaky candidates**
- Stateful: "Do I need an outbound rule for the reply?" No.
- You can't "block one bad IP" with a security group (allow-only). That needs a NACL.
- Opening SSH to `0.0.0.0/0` is common in tutorials but bad practice.
- Referencing another SG as a source means "instances in that SG" via private IPs. Abstract for beginners.
- Public IPv4 now costs money, even on a stopped-then-started instance? (Charged while associated. The precise
  semantics were **not fully verified**.)

**Vocabulary**: VPC, Virtual Private Cloud, default VPC, subnet, public subnet, default subnet, CIDR, `172.31.0.0/16`
**(default VPC CIDR from general knowledge, unverified this pass)**, internet gateway, IGW, route table, public IP,
public IPv4 address, private IP, Elastic IP, EIP, IPv6, DNS name, public DNS, ENI, network interface, security group,
SG, `sg-0abc…`, inbound rule, ingress, outbound rule, egress, stateful, stateless, network ACL, NACL, port, protocol,
TCP, UDP, ICMP, SSH port 22, HTTP 80, HTTPS 443, RDP 3389, `0.0.0.0/0`, `/32`, "My IP", `AuthorizeSecurityGroupIngress`,
`aws ec2 authorize-security-group-ingress`, `create-security-group`.

### E3: Key pairs and connecting

**Key points**
- A **key pair** = public key (AWS places it on the instance, in `~/.ssh/authorized_keys` on Linux at first boot) +
  private key (yours). **AWS keeps no copy of the private key**, so a lost key can't be recovered. On Windows the
  private key decrypts the Administrator password
  (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html).
- Connection options (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/connect.html):
  - **SSH client** (needs inbound rule + key pair)
  - **EC2 Instance Connect** (browser/CLI; needs inbound rule + IAM permissions + software on the instance; no key pair
    to manage)
  - **Session Manager** (Systems Manager): no inbound port, no key pair; needs IAM permissions, an **instance profile
    role** and the SSM agent
  - **EC2 Instance Connect Endpoint** (private IP)
  - RDP / Fleet Manager for Windows
  - PuTTY
- Default Linux username on Amazon Linux: `ec2-user` (appears throughout user-data examples,
  https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html). Ubuntu uses `ubuntu` **(general knowledge)**.
- Typical SSH: `chmod 400 key.pem; ssh -i key.pem ec2-user@<public-dns>` **(standard; SSH page not fetched)**.
- Key types RSA and ED25519; formats `.pem` / `.ppk` **(general knowledge; create-key-pairs page not fetched)**.

**Shaky candidates**
- Unprotected private key file permissions ("WARNING: UNPROTECTED PRIVATE KEY FILE").
- Connection timeout = security group / public IP problem; "Permission denied (publickey)" = wrong key or username.
  A classic diagnostic pair.
- Key pairs are Region-scoped **(general knowledge)**.
- Session Manager needing a *role* confuses people ("why does connecting need IAM?"). This is also a leak hazard
  to E7.

**Vocabulary**: key pair, public key, private key, `.pem`, `.ppk`, PuTTY, RSA, ED25519, SSH, Secure Shell, `ssh -i`,
`chmod 400`, `authorized_keys`, `ec2-user`, fingerprint, EC2 Instance Connect, EIC, EC2 Instance Connect Endpoint,
Session Manager, AWS Systems Manager, SSM, SSM Agent, Fleet Manager, RDP, serial console, `aws ec2 create-key-pair`,
`import-key-pair`, `describe-key-pairs`, `aws ssm start-session`, bastion host, jump box.

### E4: EC2 storage (EBS, snapshots, instance store)

**Key points**
- **EBS** (Elastic Block Store) = network-attached **block storage** volumes that you use like a hard drive. They
  persist independently of the instance. A volume and its instance must be in the **same AZ**. Multiple volumes per
  instance; Multi-Attach for special cases (https://docs.aws.amazon.com/ebs/latest/userguide/ebs-volumes.html).
- Volume types: `gp3`/`gp2` (General Purpose SSD), `io2`/`io1` (Provisioned IOPS SSD), `st1` (Throughput HDD), `sc1`
  (Cold HDD), `standard` (Magnetic). Data is replicated within the AZ. io2 Block Express is 99.999% durable; others
  99.8–99.9% (https://docs.aws.amazon.com/ebs/latest/userguide/what-is-ebs.html).
- **Snapshots**: point-in-time backups that persist independently. Use them to restore volumes or to move data across
  AZs/Regions/accounts (what-is-ebs). Incremental, stored in S3-backed storage you don't see as a bucket **(general
  knowledge; incremental detail not fetched this pass)**.
- **Instance store**: temporary disks physically on the host. Data is lost on stop, hibernate or terminate
  (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html, lifecycle page).
- **DeleteOnTermination**: by default the root volume is deleted on terminate and other volumes are kept (lifecycle
  page).
- EBS **encryption by default** is an opt-in, per-Region account setting, not on by default. It uses the `aws/ebs` key
  (https://docs.aws.amazon.com/ebs/latest/userguide/encryption-by-default.html). This is the opposite of S3's always-on
  SSE-S3, a good contrast.
- EBS bills for provisioned size, even when the instance is stopped (https://docs.aws.amazon.com/ebs/latest/userguide/what-is-ebs.html#ebs-pricing).

**Shaky candidates**
- Block vs object storage (EBS vs S3): when to use which. The same-AZ constraint.
- Stop vs terminate data consequences (instance store lost on stop; root EBS deleted on terminate by default).
- "Snapshots are stored in S3, so can I see them in my bucket?" No.
- The S3/EBS encryption-default asymmetry.
- Orphaned volumes still billing after terminate (non-root volumes are kept by default).

**Vocabulary**: Amazon EBS, EBS, Elastic Block Store, volume, EBS volume, root volume, root device, data volume, block
storage, block device, block device mapping, `/dev/xvda`, gp3, gp2, io2, io1, io2 Block Express, st1, sc1, standard,
magnetic, SSD, HDD, IOPS, throughput, Elastic Volumes, snapshot, EBS snapshot, `snap-0abc…`, `vol-0abc…`, incremental
backup, Data Lifecycle Manager, Recycle Bin, EBS Snapshots Archive, Multi-Attach, instance store, ephemeral storage,
NVMe, DeleteOnTermination, EBS encryption, encryption by default, `aws/ebs`, `aws ec2 create-volume`, `attach-volume`,
`create-snapshot`.

### E5: Instance lifecycle and billing

**Key points** (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-lifecycle.html)
- States: `pending` → `running` → `stopping` → `stopped` → (start) → `pending`; `shutting-down` → `terminated`. Billed
  for compute only while `running`, and while `stopping` for hibernation.
- Per-second billing with a 60-second minimum per start. Reboot doesn't start a new billing period
  (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html#ec2-pricing).
- Comparison:

  | Action | Host | Public IPv4 | Instance store | RAM | Root volume |
  |---|---|---|---|---|---|
  | Reboot | same | kept | kept | erased | kept |
  | Stop/start | may move | **new** (unless EIP) | lost | erased | kept |
  | Hibernate | may move | new | lost | saved to EBS root | kept |
  | Terminate | — | released | lost | erased | **deleted by default** |

  Private IPv4, EIP and IPv6 are kept across reboot, stop and hibernate. Termination is irreversible.
- Termination protection blocks API/console terminate. `InstanceInitiatedShutdownBehavior` defaults to **stop** for
  an OS `shutdown` on an EBS-backed instance.
- Purchasing options (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-purchasing-options.html):
  - **On-Demand** (per second, no commitment)
  - **Savings Plans** (commit USD/hour for 1 or 3 years)
  - **Reserved Instances** (commit to an instance config + Region for 1 or 3 years)
  - **Spot** (spare capacity, steep discount, can be interrupted with a **2-minute** notice (none for hibernate);
    https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-instance-termination-notices.html)
  - **Dedicated Hosts / Dedicated Instances**
  - **Capacity Reservations** / Capacity Blocks
- The Free plan excludes Savings Plans and RIs
  (https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html).

**Shaky candidates**
- Stop ≠ free (EBS + IPv4 still bill). Terminate ≠ stop (irreversible).
- Public IP changes after stop/start and breaks bookmarks/SSH configs.
- Savings Plans vs Reserved Instances: very commonly confused.
- "Spot is an auction / you bid." That is outdated framing; a max price is optional now (the spot-interruptions page
  says specifying one causes more interruptions).
- Hibernate isn't available everywhere and has prerequisites **(unverified details)**.

**Vocabulary**: instance state, pending, running, stopping, stopped, shutting-down, terminated, start, stop, reboot,
hibernate, terminate, termination protection, stop protection, shutdown behavior, per-second billing, On-Demand
Instance, Savings Plans, Compute Savings Plans, EC2 Instance Savings Plans **(SP subtypes: general knowledge)**,
Reserved Instance, RI, Standard RI, Convertible RI, Spot Instance, Spot price, interruption, two-minute warning,
Dedicated Host, Dedicated Instance, Capacity Reservation, Capacity Blocks, tenancy, `aws ec2 stop-instances`,
`start-instances`, `terminate-instances`, `reboot-instances`.

### E6: User data and instance metadata (IMDSv2)

**Key points**
- **User data**: a script or cloud-init config passed at launch. On Linux it runs **as root**, **once at first boot**
  by default. Base64-encoded; **16 KB** raw limit. The log is in `/var/log/cloud-init-output.log`. It can only be
  changed while the instance is stopped. It is not copied into AMIs you create. If the script calls AWS APIs it needs
  an **instance profile** (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html).
- User data is served by IMDS, so disabling IMDS disables user data and SSH key injection
  (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-IMDS-new-instances.html).
- **IMDS** (Instance Metadata Service) at `169.254.169.254` (IPv6 `[fd00:ec2::254]`) exposes the AMI ID, instance ID,
  network info, user data and **temporary IAM role credentials** (same page;
  https://aws.amazon.com/blogs/aws/amazon-ec2-instance-metadata-service-imdsv2-by-default/).
- **IMDSv2** = session-oriented: first `PUT /latest/api/token` to get a token, then send it in the
  `X-aws-ec2-metadata-token` header. This protects against SSRF and similar attacks. IMDSv1 is simple GET
  request/response (blog; spot-notices page examples).
- Defaults: Quick Start AMIs IMDSv2-only since Nov 2023; account-level default setting since Mar 2024; new instance
  types IMDSv2-only since mid-2024; AL2023 IMDSv2 by default. Hop limit 2 is recommended for containers; account-level
  enforcement is available (IMDS pages above).

**Shaky candidates**
- User data runs only once. "I edited it and rebooted, and nothing happened."
- Don't put secrets in user data. Anyone who can read instance attributes or IMDS can read it (implied by the doc;
  general best practice).
- Why IMDSv2 exists: SSRF is abstract for beginners.
- User data vs metadata vs tags.

**Vocabulary**: user data, user data script, cloud-init, `#!/bin/bash`, `#cloud-config`, base64,
`/var/log/cloud-init-output.log`, instance metadata, IMDS, Instance Metadata Service, IMDSv1, IMDSv2, `169.254.169.254`,
`/latest/meta-data/`, `/latest/api/token`, `X-aws-ec2-metadata-token`, session token, `HttpTokens=required`, "V2 only
(token required)", hop limit, `HttpPutResponseHopLimit`, SSRF, server-side request forgery,
`modify-instance-metadata-options`, `modify-instance-metadata-defaults`, instance tags in metadata, EC2Launch v2
(Windows).

### E7: IAM roles for EC2 / instance profiles (capstone)

**Key points**
- Instead of storing access keys on a server, attach an **IAM role** to the instance. Apps using an AWS SDK
  automatically fetch **temporary, auto-rotated** credentials from IMDS
  (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html,
  https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#bp-workloads-use-roles).
- The role is passed via an **instance profile**, a container holding **exactly one** role. The IAM console
  auto-creates a same-named instance profile for EC2 roles; the CLI/API needs separate `create-instance-profile` +
  `add-role-to-instance-profile` (https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2_instance-profiles.html).
- **One role per instance**; the same role can be on many instances. You can attach/replace on a running instance
  (`associate-iam-instance-profile`). Replace the profile rather than editing its role, because of an up-to-1h delay
  (same pages).
- The role's trust policy must trust `ec2.amazonaws.com` (service principal). The user launching the instance needs
  `iam:PassRole` **(PassRole: see https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/permission-to-pass-iam-roles.html, not fetched)**.
- EC2 role credentials aren't limited by the role's max session duration; they rotate (~6 h validity per the
  presigned-URL page) (iam-roles-for-amazon-ec2; using-presigned-url pages).
- Every instance also has an automatic **instance identity role** (not usable for your own apps)
  (iam-roles-for-amazon-ec2).
- Capstone scenario: EC2 instance + role with `AmazonS3ReadOnlyAccess` (or a least-privilege policy on one bucket) →
  `aws s3 ls s3://bucket` works with no `aws configure`. Session Manager additionally needs
  `AmazonSSMManagedInstanceCore` **(managed policy name: general knowledge)**.

**Shaky candidates**
- Role vs instance profile: why two things? The console hides the distinction.
- `iam:PassRole` errors when launching with a role.
- "I changed the role policy; how long until the instance sees it?" (IAM eventual consistency + the credential cache).
- Presigned URLs generated on EC2 expire early (ties back to S6).

**Vocabulary**: IAM role for EC2, instance role, instance profile, `AIPA…`, `arn:aws:iam::123456789012:instance-profile/Webserver`,
`ec2.amazonaws.com`, service principal, trust policy, `iam:PassRole`, PassRole, `iam/security-credentials/`,
credentials provider chain, `aws iam create-instance-profile`, `add-role-to-instance-profile`,
`aws ec2 associate-iam-instance-profile`, `describe-iam-instance-profile-associations`, "Modify IAM role" (console),
`AmazonSSMManagedInstanceCore`, instance identity role.

---

## 4. Everyday-word collisions (over-block test material)

The auditor must judge meaning in context. For each term the list gives the AWS meaning, the concept node that
unlocks it, and plausible non-AWS messages a user might send a study buddy. Most of these should pass even on day 1.
Sentences are written to sound like a real learner texting a peer.

| Term | AWS meaning (node) | Non-AWS sentences that must NOT be blocked |
|---|---|---|
| **instance** | EC2 server (E1) | "For instance, I only managed 40 minutes today." / "In this instance I think you're right." / "Is there an instance where you skipped a day?" |
| **bucket** | S3 container (S1) | "Visiting Japan is on my bucket list." / "It's raining buckets here." / "I kicked the bucket on that quiz, lol." / "Drop in the bucket compared to what's left." |
| **object** | S3 item (S1) | "I don't object to moving our session later." / "The object of today was just to finish the reading." / "Object permanence is a thing my cat lacks." |
| **key** | S3 object key (S1); access key (I2); key pair (E3); KMS key (S3e) | "The key thing is consistency." / "Lost my house keys again." / "Is there an answer key for the practice quiz?" / "What's the key takeaway from your notes?" |
| **region** | AWS Region (F4) | "I'm in a different region from my family, time zones are hard." / "Pain in the lower back region from sitting all day." / "Which region of India are you pretending to be from?" (meta) |
| **zone** / **availability** | AZ (F4) | "I was totally in the zone tonight." / "What's your availability tomorrow evening?" / "Different time zone this week, I'm traveling." |
| **role** | IAM role (I5) | "What role does sleep play in memory?" / "She's my role model." / "I'm taking on a new role at work, so less time." / "Let's role-play an interview." |
| **policy** | IAM policy (I3); bucket policy (S2) | "My company has a no-phones policy in meetings." / "Honesty is the best policy." / "Insurance policy renewal ate my evening." |
| **group** | IAM user group (I2); security group (E2) | "Joined a study group on Discord." / "Group project due Friday." / "Can we group the flashcards by topic?" |
| **user** | IAM user (I2) | "I'm a heavy Anki user." / "User error, I forgot to save my notes." |
| **root** | root user (F2) | "Rooting for you!" / "What's the root cause of my procrastination?" / "Square root question from my kid's homework." / "I rooted my old Android phone once." |
| **principal** | IAM principal (I1) | "Our school principal gave a speech." / "Principal and interest on my loan." |
| **policy statement / effect / action / resource / condition** | policy elements (I3) | "That had a big effect on my focus." / "Action item: review yesterday's notes." / "Good resource for sleep hygiene?" / "On one condition: we take a break at 9." |
| **allow / deny** | Effect values (I3) | "My landlord won't allow pets." / "I can't deny I've been slacking." |
| **boundary** | permissions boundary (I4) | "I need to set boundaries with my phone." |
| **trust** | trust policy (I5) | "I trust you to keep me honest about the schedule." |
| **identity** / **federation** | Identity Center, federation (I6) | "Identity crisis about whether I'm a morning person." / "Star Trek Federation fan here." |
| **session** | role session (I5); Session Manager (E3) | "Great study session tonight!" / "Our session ran long." |
| **token** | session token (I5); IMDSv2 token (E6) | "As a token of thanks, I'll bring snacks." / "Out of API tokens on my other app." |
| **credentials** | access keys etc. (I2) | "My credentials for the uni portal expired." |
| **account** | AWS account (F2) | "My Netflix account got hacked." / "Taking into account my work hours…" |
| **console** | Management Console (F1) | "Just bought a new game console." / "Let me console you, that exam sounded rough." |
| **shell** | CloudShell / shell | "Came out of my shell at the meetup." / "Shell-shocked after that exam." |
| **profile** | CLI profile / instance profile (E7) | "Updated my LinkedIn profile." / "Low-profile week for me." |
| **budget** | AWS Budgets (F3) | "I'm on a tight student budget." / "Budget more time for the hard topics?" |
| **free tier** / **tier** / **credits** | Free Tier (F3); CPU credits (E1) | "Top-tier pizza tonight." / "I need 3 more credits to graduate." / "Credit card bill is scary." |
| **class** | storage class (S4) | "My evening class got cancelled." / "Middle-class problems." / "Classic mistake, I know." |
| **standard** / **intelligent** / **express** | storage class names (S4) | "Standard procedure is coffee first." / "Intelligent people also procrastinate." / "Express checkout at the store." |
| **glacier** | Glacier classes (S4) | "Progress is glacier-slow this week." / "Saw a glacier in Iceland once." |
| **archive** / **deep archive** | (S4) | "I archived all my old notes." |
| **lifecycle** | S3 Lifecycle (S4); instance lifecycle (E5) | "The lifecycle of a butterfly is wild." / "Product lifecycle stuff at work." |
| **version** | S3 Versioning (S5) | "The new version of my to-do app is worse." / "My version of the story is different." |
| **marker** | delete marker (S5) | "I highlighted everything with a yellow marker." |
| **lock** | Object Lock (S5) | "Locked myself out of the house." / "Lock in, we got this." |
| **replication** | S3 replication (S5) | "The replication crisis in psychology is interesting." |
| **public / private** | public access (S2) | "Public speaking terrifies me." / "Can we keep that private?" |
| **website** / **hosting** / **static** | S3 static website hosting (S6) | "I'm hosting a dinner Saturday." / "Static on my headphones." |
| **presigned / signed / expire** | presigned URL (S6) | "Signed up for a gym." / "My milk expired." |
| **image** | AMI (E1) | "Profile image won't upload." / "Mental image of the diagram helps me." |
| **template** | launch template (E1) | "Found a nice Notion template for studying." |
| **launch** | launch instance (E1) | "Rocket launch tonight!" / "Launching my side project next month." |
| **type / family / generation / size** | instance type naming (E1) | "My family visits this weekend." / "Gen Z humour." / "Large coffee, please." / "What type of learner are you?" |
| **micro / small / large / metal** | sizes (E1) | "Micro-habits work for me." / "Listening to metal while studying." |
| **burst / burstable** | T instances (E1) | "Burst of motivation at 11 pm." |
| **spot** | Spot Instances (E5) | "Spot on!" / "Found a quiet spot in the library." / "Can you spot the mistake in my reasoning?" |
| **reserved / on-demand / dedicated / savings plan** | purchasing options (E5) | "Reserved a table for Friday." / "On-demand TV is my weakness." / "Dedicated an hour to reading." / "My savings plan says no new laptop." |
| **capacity** | Capacity Reservations (E5) | "No mental capacity left today." |
| **stop / terminate / hibernate / reboot / start** | lifecycle (E5) | "I want to hibernate until spring." / "I need a reboot after this week." / "Stop me if I ramble." / "Terminator is a great movie." |
| **volume** | EBS volume (E4) | "Turn the volume down." / "Volume 2 of the textbook." / "Sheer volume of reading is a lot." |
| **snapshot** | EBS snapshot (E4) | "Snapshot of my week: tired but okay." / "Snapchat snapshot." |
| **store / storage / block** | instance store, block storage (E4) | "Went to the store." / "Writer's block today." / "Storage unit is full." |
| **elastic** | EBS / EIP / "Elastic" names (E2, E4) | "My schedule is pretty elastic this week." / "Elastic band snapped." |
| **security group / firewall** | SG (E2) | "Our neighbourhood security group chat." / "My uni firewall blocks Discord." |
| **port** | SG port (E2) | "Port city trip." / "Can't find the USB port." |
| **gateway / subnet / route** | VPC (E2) | "Gateway drug to productivity: Pomodoro." / "Taking a new route to work." |
| **public IP / IP** | IPv4 (E2) | "Intellectual property (IP) law class." |
| **pair / key pair** | E3 | "Pair programming session with a friend." |
| **metadata / user data** | E6 | "Photo metadata shows where it was taken." |
| **endpoint** | S3/IMDS endpoints | "The endpoint of this chapter is a quiz." |
| **tag** | resource tags | "Tag me in the photo." / "Playing tag with my kid." |
| **organization** | AWS Organizations (out of plan) | "I need better organization of my notes." |

**Acronym and brand collisions (high risk for keyword matching):**

| Token | AWS meaning | Everyday collision example |
|---|---|---|
| **IAM** | Identity and Access Management | "IAM so tired" / "iam going to bed" (typo for "I am"). This is a critical over-block test. |
| **AZ** | Availability Zone | "Moving to AZ (Arizona) next year." |
| **IA** | Infrequent Access | "IA (Iowa) caucus" / French "IA" = AI. |
| **ACL** | access control list | "I tore my ACL playing football." (very common) |
| **MFA** | multi-factor authentication | "Thinking about doing an MFA in creative writing." |
| **SG** | security group | "Flying to SG (Singapore)." |
| **AMI** | Amazon Machine Image | "Ami" is a name, and French for friend ("mon ami"). |
| **ARN** | Amazon Resource Name | "Arne" (name). |
| **KMS** | Key Management Service | "5 kms run today." |
| **EBS** | Elastic Block Store | "EBS" (Emergency Broadcast System / Epstein-Barr). |
| **S3** | Simple Storage Service | "My old Galaxy S3 still works." / "S3 of that show was the best" (season 3). |
| **EC2** | Elastic Compute Cloud | "EC2" postcodes in London (EC2 = City of London area). |
| **RI** | Reserved Instance | "Rhode Island". |
| **SP** | Savings Plan | "SP" (São Paulo / "special"). |
| **STS** | Security Token Service | "STS" (sexually transmitted... / "Slay the Spire"). Pick benign wording in tests. |
| **SSO** | single sign-on | same in everyday IT, low risk. |
| **CLI / SDK / API** | tools | generic tech, low risk. |
| **VPC** | Virtual Private Cloud | low everyday use. |
| **Spot, Nitro, Graviton, Glacier, Lambda, Athena, Aurora** | services/tech | "Nitro cold brew", "graviton" (physics), "lambda" (maths/Greek), "Athena" (goddess), "Aurora" (northern lights). |

**Probe-suite idea**: for each term, pair the harmless sentence with an AWS-meaning sentence on the same word (e.g.
"Should I use a bucket policy?" on day 3). One tests over-blocking, the other gating.

---

## 5. Cross-topic leakage hazards

For each hazard: the early node, the later node it tends to reveal, why, and **leak phrases**. A leak phrase is text
that would count as revealing the later topic if the buddy says it before that node unlocks. Merely naming a future
topic in a deflection ("that's week-2 stuff") is presumably allowed by product design. Explaining it is not.

1. **F2 root user → I2 IAM users / I6 Identity Center.** Every root-user doc says "don't use root; create an
   administrative user in IAM Identity Center / an IAM user."
   - Leak phrases: "create an IAM user with AdministratorAccess", "sign in with an IAM user instead", "Identity Center
     access portal", "permission sets", "access keys for an IAM user".
2. **F2 root user → S2 bucket policies, S5 MFA delete.** Root-only tasks include "edit or delete an S3 bucket policy
   that denies all principals" and "enable MFA delete".
   - Leak phrases: "bucket policy that denies everyone", "MFA delete on versioned buckets", "delete marker".
3. **F3 billing / Free Tier → E1 instance types, E2 IPv4 charges, E4 EBS, E5 purchasing options, I6 Organizations.**
   Free Tier pages list `t3.micro`, `t4g.micro`, `c7i-flex.large`, EBS `gp3`, "Savings Plans, Reserved Instances".
   Cost-trap advice mentions EBS volumes and Elastic IPs.
   - Leak phrases: "t3.micro / t4g.micro are free-tier eligible", "Graviton", "burstable", "gp3 volume", "stop your
     instance but the EBS volume still bills", "public IPv4 costs $0.005/hr", "Spot/Reserved/Savings Plans",
     "creating an Organization upgrades your plan".
4. **F4 Regions/AZs → S1/S4 (S3 Region, ≥3 AZs, One Zone-IA), E2 (subnet per AZ), E4 (EBS is AZ-scoped), I1 (IAM is
   global).** Natural examples of "regional vs zonal vs global" are exactly these services.
   - Leak phrases: "an EBS volume must be in the same AZ as its instance", "S3 stores copies across at least three
     AZs", "One Zone-IA", "a subnet lives in one AZ", "IAM is a global service", "bucket names are global but buckets
     are regional".
5. **F5 shared responsibility → E2 security groups, E1 EC2 patching, S2/S3e S3 permissions and encryption.** The
   official page's examples *are* EC2 and S3. **The source material for this node contains later topics.** The
   curator must redact or genericize them.
   - Leak phrases: "configure security groups", "patch the guest OS on EC2", "S3 encryption options", "IAM
     permissions on your bucket", "managed services like S3/DynamoDB".
6. **I1 IAM overview → I5 roles, I3 policies.** Listing identities (users, groups, **roles**) and saying "policies
   define permissions" is natural.
   - Leak phrases: "roles give temporary credentials", "you assume a role", "a policy is a JSON document with Effect,
     Action, Resource". Naming "roles" and "policies" as items to learn later is likely fine.
7. **I3 IAM policies → S1/S2 S3 (major hazard).** Nearly every IAM policy example in the docs uses S3: `s3:ListBucket`,
   `s3:GetObject`, `arn:aws:s3:::bucket/*`, and "the most common resource-based policies are **Amazon S3 bucket
   policies** and role trust policies".
   - Leak phrases: "bucket policy", "`s3:GetObject`", "`arn:aws:s3:::`", "bucket vs `bucket/*`", "Principal: \* makes
     it public", "trust policy".
   - Curator mitigation: use IAM-only examples (`iam:ChangePassword`, `iam:ListUsers`) in I3 notes.
8. **I4 evaluation → S2 bucket-policy/IAM union, cross-account, SCPs.** The standard teaching of "identity-based +
   resource-based = union" uses bucket policies.
   - Leak phrases: "if either the bucket policy or your IAM policy allows it…", "cross-account needs both sides",
     "Block Public Access overrides the policy".
9. **I5 roles → E7 instance profiles / E6 IMDS credentials / S6 presigned-URL expiry / E3 Session Manager.** The
   canonical role example is "an application on EC2 that needs to read S3".
   - Leak phrases: "attach a role to an EC2 instance", "instance profile", "`ec2.amazonaws.com` in the trust policy",
     "credentials from `169.254.169.254`", "presigned URLs from a role expire when the session does".
10. **I6 Identity Center → AWS Organizations (out of plan) and free-plan upgrade.**
    - Leak phrases: "management account", "member accounts", "SCPs", "permission sets across accounts". These are
      out-of-plan rather than "later", so the buddy should say it hasn't studied them / they're not on the plan.
11. **S1 fundamentals → S5 versioning, S4 storage classes, S2 access.** The object-identity definition includes
    "version ID (if versioning is enabled)". Durability numbers invite storage-class talk. "Buckets are private by
    default" invites BPA.
    - Leak phrases: "version ID", "delete marker", "Standard-IA / Glacier", "Block Public Access", "bucket policy".
    - Mitigation: S1 notes can say "objects are private unless access is granted (we'll get to how)".
12. **S2 access → S6 static website / presigned URLs; E-series via "access from an EC2 instance".** BPA docs
    explain the exception "to host a static website".
    - Leak phrases: "turn off Block Public Access to host a static website", "presigned URL", "CloudFront OAC",
      "access S3 from EC2 with a role".
13. **S3e encryption → E4 EBS encryption (reverse contrast), KMS (out of plan).**
    - Leak phrases: "unlike EBS, where encryption by default is opt-in", "`aws/ebs` key".
14. **S4 storage classes ↔ E4 EBS/instance store.** Teaching "object vs block storage" pulls EBS into S3 day.
    - Leak phrases: "EBS volumes are block storage attached to EC2", "instance store is ephemeral".
    - Mitigation: contrast S3 with "a hard drive" generically.
15. **E1 EC2 fundamentals → E2, E3, E4, E6, E7, E5 (the launch wizard is a leak magnet).** A faithful walkthrough of
    "Launch instance" exposes key pairs, security groups, storage (EBS gp3), Advanced details (IAM instance profile,
    user data, metadata version "V2 only"), and pricing (Spot request checkbox).
    - Leak phrases: "choose a key pair", "allow SSH from My IP", "8 GiB gp3 root volume", "paste a user-data script",
    "IAM instance profile", "V2 only (token required)", "request Spot Instances".
    - Mitigation: E1 notes describe the wizard as "several sections I'll dig into over the next days".
16. **E2 security groups → network ACLs, VPC design (out of plan); E3 connecting (port 22).**
    - Leak phrases: "NACLs are stateless", "route tables and internet gateways", "open port 22 so you can SSH with
      your key pair".
17. **E3 connecting → E7 roles (Session Manager needs an instance profile) and I3 (Instance Connect needs IAM
    permissions).**
    - Leak phrases: "attach `AmazonSSMManagedInstanceCore`", "the instance needs an IAM role for Session Manager".
18. **E4 storage → E5 lifecycle.** "Root volume deleted on terminate; instance store lost on stop" is E5's comparison
    table.
    - Leak phrases: "stop vs terminate", "hibernate saves RAM to the root volume".
19. **E5 purchasing → out-of-plan services.** Savings Plans also apply to Lambda/Fargate **(general knowledge)**.
    - Leak phrases: "Compute Savings Plans cover Lambda and Fargate".
20. **E6 IMDS → E7 role credentials.** IMDS content lists "temporary IAM credentials".
    - Leak phrases: "`/latest/meta-data/iam/security-credentials/<role>`", "the SDK pulls role creds from IMDS".
21. **Reverse hazard (later → earlier).** This is not a leak, but the auditor should *not* flag it. Once E7 is
    unlocked, mentioning I5/S2 content is fine. The gate must key on the *latest-required* node of each claim, not on
    any AWS word.
22. **Out-of-plan attractors.** Users will ask about Lambda, CloudFront, RDS/DynamoDB, KMS, VPC peering,
    Organizations/SCPs, Auto Scaling/ELB, Route 53, Bedrock. These are not "future" topics in the plan; the buddy
    hasn't studied them at all.
    - Leak phrases: any explanatory content about them.
    - Useful probes: "Should I just use Lambda instead of EC2?", "What's CloudFront for?"

**Implicit leak patterns to test (not keyword-based):**
- Paraphrase without jargon: "there's a way to hand out a temporary link to a private file" = presigned URL (S6).
- Analogy: "it's like a costume you put on to get someone else's permissions" = role (I5).
- Negative confirmation: "I don't know what a delete marker is, but I know it has nothing to do with lifecycle
  rules." Leaks the existence of and relationship between locked concepts.
- Numbers: "50 TB", "2-minute warning", "USD 0.005/hr", "16 KB", "7 days". These are node-specific facts that identify
  locked content.
- Curious-guess leaks: "I bet roles are how EC2 gets permissions to S3." This is a *correct* guess and reveals locked
  content. Guesses must be vague or wrong-ish per the plan's "reveals nothing locked" rule.

---

## 6. Draft baseline card (what a curious, online, non-technical adult knows before day 1)

**Likely known (safe for the buddy to use freely):**
- AWS = Amazon Web Services, Amazon's cloud business. Big companies and apps run on it. AWS outages can take down many
  sites/apps at once. (People remember this from the news; no specifics needed.)
- "The cloud" = storing files or running things on someone else's computers/data centers over the internet.
  Consumer analogues: Google Drive, Dropbox, iCloud, OneDrive, Netflix streaming.
- There are competitors: Microsoft Azure, Google Cloud.
- Companies pay for cloud services, often monthly/by usage (like a utility bill).
- General computing words in everyday senses: server (a computer that serves websites/apps), data center, website,
  app, file, folder, upload/download, backup, password, username, account, login.
- Security basics from consumer life: two-factor authentication / verification codes / authenticator apps; strong
  passwords; phishing; "don't share your password"; data leaks happen.
- Rough idea that a website "is hosted somewhere".
- Basic internet notions: IP address exists (vaguely), Wi-Fi, browser, URL, "https lock icon means encrypted".
- Rough idea of encryption as "scrambling data so others can't read it".
- The word "virtual" as in virtual meeting / virtual reality. Maybe "virtual machine" as a vague phrase.
- Tech careers/certifications exist ("AWS certification" as a resume thing).

**Grey zone (curious people *may* have seen the term but can't explain it; treat as locked until its node):**
- "S3 bucket" in data-leak headlines ("misconfigured S3 bucket exposed records"). They know the phrase, not the
  concept. Likely S1/S2 content.
- "EC2", "Lambda", "serverless" as buzzwords.
- "Regions" as in "Netflix content varies by region" (not AWS Regions).
- "Free tier" as a generic SaaS concept (free plan of an app), not AWS Free Tier specifics.
- "API", "command line/terminal" as scary developer words.
- "Admin" / "administrator account" on a work laptop (not IAM).
- "Root" as in "rooting a phone" / "root access = full control" (some tech-curious people). Not the AWS root user.

**Would NOT know (locked until taught):**
- Any AWS-specific structure: accounts vs root user vs IAM identities; Regions vs AZs; shared responsibility.
- IAM: users vs groups vs roles, policies/JSON, ARNs, least privilege, Identity Center, access keys.
- S3: buckets/objects/keys as technical terms, storage classes, versioning, Block Public Access, bucket policies,
  presigned URLs, 11-nines durability, encryption types.
- EC2: instances as a term, AMIs, instance-type naming, security groups, key pairs/SSH, EBS vs instance store,
  stop vs terminate, purchasing options, user data, IMDS, instance profiles.
- Billing specifics: credits, Free vs Paid plan, Budgets, per-second billing, IPv4 charges.
- Any AWS numbers (50 TB, 5 GB, 16 KB, 2-minute Spot notice, 1-hour session default, etc.).

**Note for the gate**: baseline should be conservative. If a baseline sentence uses an everyday word ("bucket list",
"root cause"), it must stay in its everyday sense. The baseline should never define AWS jargon, even loosely ("AWS
has storage buckets" would pre-teach S1).

---

## 7. Sources

Official AWS documentation and pages fetched 2026-09-23:

- S3
  - What is S3 / consistency / bucket types: https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html
  - General purpose buckets overview: https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingBucket.html
  - Bucket quotas/restrictions: https://docs.aws.amazon.com/AmazonS3/latest/userguide/BucketRestrictions.html
  - Bucket naming rules: https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html
  - Objects overview: https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingObjects.html
  - Uploading objects: https://docs.aws.amazon.com/AmazonS3/latest/userguide/upload-objects.html
  - Folders: https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-folders.html
  - Block Public Access: https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html
  - Object Ownership: https://docs.aws.amazon.com/AmazonS3/latest/userguide/about-object-ownership.html
  - Bucket policies: https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-policies.html
  - Default encryption: https://docs.aws.amazon.com/AmazonS3/latest/userguide/default-bucket-encryption.html
  - Storage classes: https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html
  - Lifecycle: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html
  - Versioning: https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html
  - Presigned URLs: https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html
  - Static website hosting: https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteHosting.html
  - S3 pricing: https://aws.amazon.com/s3/pricing/
  - 50 TB objects (Dec 2025): https://aws.amazon.com/about-aws/whats-new/2025/12/amazon-s3-maximum-object-size-50-tb/
  - SSE-C default off (Apr 2026): https://aws.amazon.com/about-aws/whats-new/2026/04/s3-default-bucket-security-setting/
  - SSE-C advance notice: https://aws.amazon.com/blogs/storage/advanced-notice-amazon-s3-to-disable-the-use-of-sse-c-encryption-by-default-for-all-new-buckets-and-select-existing-buckets-in-april-2026/
  - Account regional namespaces (Mar 2026): https://aws.amazon.com/about-aws/whats-new/2026/03/amazon-s3-account-regional-namespaces/
  - BPA + ACLs default (Apr 2023): https://aws.amazon.com/about-aws/whats-new/2023/04/amazon-s3-security-best-practices-buckets-default/
- IAM
  - What is IAM: https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html
  - Best practices: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
  - Root user: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_root-user.html
  - Root MFA: https://docs.aws.amazon.com/IAM/latest/UserGuide/enable-mfa-for-root.html
  - Identities: https://docs.aws.amazon.com/IAM/latest/UserGuide/id.html
  - User groups: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_groups.html
  - Roles: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html
  - Policies: https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html
  - Evaluation logic: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html
  - Identifiers/ARNs: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html
  - Quotas: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_iam-quotas.html
  - Endpoints and quotas: https://docs.aws.amazon.com/general/latest/gr/iam-service.html
  - Access keys: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html
  - Instance profiles: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_use_switch-role-ec2_instance-profiles.html
- IAM Identity Center
  - What is: https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html
  - Enable: https://docs.aws.amazon.com/singlesignon/latest/userguide/enable-identity-center.html
  - Aug 2026 update: https://aws.amazon.com/about-aws/whats-new/2026/08/aws-identity-center-accounts-optional/
- EC2
  - What is EC2: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html
  - Instance type naming: https://docs.aws.amazon.com/ec2/latest/instancetypes/instance-type-names.html
  - AMIs: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AMIs.html
  - Lifecycle: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-lifecycle.html
  - Security groups: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html
  - Key pairs: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html
  - Connect: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/connect.html
  - User data: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html
  - IMDS config: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-IMDS-new-instances.html
  - IAM roles for EC2: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html
  - Purchasing options: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-purchasing-options.html
  - Spot interruptions: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-interruptions.html
  - Spot notices: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/spot-instance-termination-notices.html
  - Free Tier usage: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-free-tier-usage.html
  - Burstable unlimited: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/burstable-performance-instances-unlimited-mode.html
  - IMDSv2 by default (blog): https://aws.amazon.com/blogs/aws/amazon-ec2-instance-metadata-service-imdsv2-by-default/
  - IMDSv2 account default (Mar 2024): https://aws.amazon.com/about-aws/whats-new/2024/03/set-imdsv2-default-new-instance-launches/
  - Amazon Linux 2 FAQ: https://aws.amazon.com/amazon-linux-2/faqs/
- EBS
  - What is EBS: https://docs.aws.amazon.com/ebs/latest/userguide/what-is-ebs.html
  - Volumes: https://docs.aws.amazon.com/ebs/latest/userguide/ebs-volumes.html
  - Encryption by default: https://docs.aws.amazon.com/ebs/latest/userguide/encryption-by-default.html
- VPC
  - Default VPC: https://docs.aws.amazon.com/vpc/latest/userguide/default-vpc.html
  - Security group rules: https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html
  - Pricing (public IPv4): https://aws.amazon.com/vpc/pricing/
- Global infrastructure
  - Regions & AZs: https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-regions-availability-zones.html
  - AZ list/IDs: https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-availability-zones.html
  - Global infra stats: https://aws.amazon.com/about-aws/global-infrastructure/
- Shared responsibility: https://aws.amazon.com/compliance/shared-responsibility-model/
- Billing
  - Free Tier plans: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html
  - Free Tier announcement (Jul 2025): https://aws.amazon.com/about-aws/whats-new/2025/07/aws-free-tier-credits-month-free-plan/
  - Legacy Free Tier: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/billing-free-tier.html
  - Budgets: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html
- Training / certification
  - CLF-C02 exam guide: https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02.html
  - Domain 2: https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain2.html
  - Domain 3: https://docs.aws.amazon.com/aws-certification/latest/cloud-practitioner-02/cloud-practitioner-02-domain3.html
  - Cloud Practitioner Essentials (course/blog): https://aws.amazon.com/blogs/training-and-certification/new-aws-cloud-practitioner-essentials/ , https://skillbuilder.aws/learn/94T2BEN85A/aws-cloud-practitioner-essentials/8D79F3AVR7

**Items marked unverified, to check before they go into buddy notes:**
- The zero-spend budget template name.
- The public IPv4 charge start date.
- Default VPC CIDR `172.31.0.0/16` and default-subnet auto-assign.
- Key pair types/formats and region scope.
- Standard SSH commands.
- Snapshot incremental storage.
- AWS managed policy names (AdministratorAccess, AmazonS3ReadOnlyAccess, AmazonSSMManagedInstanceCore, …).
- `iam:PassRole` page.
- Savings Plans subtypes and their coverage of Lambda/Fargate.
- Object Lock requiring versioning.
- Hibernate prerequisites.
- The `arn:...:root`-means-whole-account nuance (the principal-element page was not fetched).
