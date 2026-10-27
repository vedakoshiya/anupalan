# Source Registry: Core 40 Regulatory Instruments

**Anupalan Phase 0 Baseline Catalog for Indian MSME Compliance Pilot (Surat & Gujarat Focus)**

This registry defines the initial 40 official statutory instruments (notifications, circulars, acts, and state schemes) ingested into the Anupalan knowledge base. Each instrument is cataloged with its issuing authority, jurisdiction, subject classification, and legal relationship links.

---

## Summary of Scope by Domain

| Domain | Authority | Focus Areas | Count |
| :--- | :--- | :--- | :--- |
| **GST: Job Work & Textiles** | CBIC / GST Council | Job work rates, movement rules, ITC-04, textile sector exemptions | 8 |
| **GST: Composition Scheme & Thresholds** | CBIC / GST Council | Composition eligibility, turnover thresholds (₹1.5 Cr / ₹50 L / ₹40 L) | 6 |
| **GST: Input Tax Credit & E-Invoicing** | CBIC | Section 16/17, GSTR-2B matching, ITC mismatches, e-invoicing limits | 9 |
| **GST: Reverse Charge & E-Way Bill** | CBIC | RCM services, GTA transport, Rule 138 e-way bill compliance | 4 |
| **MSME & Udyam Protections** | Ministry of MSME / MoF | Udyam criteria, MSMED Sec 15/16 delayed payments, Sec 43B(h) | 6 |
| **Gujarat State Circulars & Subsidies** | Govt of Gujarat / SGST | MSME capital/interest subsidies, textile policy, return scrutiny | 7 |
| **Total** | | | **40** |

---

## 1. GST: Job Work & Textiles (Central Jurisdiction)

1. **`INST-GST-JW-001`**: Notification No. 11/2017-Central Tax (Rate)
   - *Authority:* CBIC | *Date:* 2017-06-28 | *Effective From:* 2017-07-01
   - *Title:* Rate of GST on intra-State supply of services, specifically Entry 26 (Job work).
   - *Subjects:* `["job_work", "gst_rates", "services"]`

2. **`INST-GST-JW-002`**: Notification No. 20/2017-Central Tax (Rate)
   - *Authority:* CBIC | *Date:* 2017-08-22 | *Effective From:* 2017-08-22
   - *Title:* Amending Notification 11/2017 to reduce GST rate on textile job work to 5%.
   - *Relation:* `amends` `INST-GST-JW-001`
   - *Subjects:* `["job_work", "textiles", "reduced_rate"]`

3. **`INST-GST-JW-003`**: Notification No. 31/2017-Central Tax (Rate)
   - *Authority:* CBIC | *Date:* 2017-10-13 | *Effective From:* 2017-10-13
   - *Title:* Reduced GST rate (5%) on job work in relation to handicrafts and imitation jewellery.
   - *Relation:* `amends` `INST-GST-JW-001`
   - *Subjects:* `["job_work", "handicrafts", "jewellery"]`

4. **`INST-GST-JW-004`**: Notification No. 14/2019-Central Tax (Rate)
   - *Authority:* CBIC | *Date:* 2019-09-30 | *Effective From:* 2019-10-01
   - *Title:* Revision of GST rate on job work from 18% to 12% for registered principal goods.
   - *Relation:* `amends` `INST-GST-JW-001`
   - *Subjects:* `["job_work", "registered_principal", "rate_revision"]`

5. **`INST-GST-JW-005`**: Circular No. 38/12/2018-GST
   - *Authority:* CBIC | *Date:* 2018-03-26 | *Effective From:* 2018-03-26
   - *Title:* Clarification on issues related to job work under Section 143 of CGST Act.
   - *Subjects:* `["job_work", "section_143", "challan", "movement"]`

6. **`INST-GST-JW-006`**: Circular No. 88/07/2019-GST
   - *Authority:* CBIC | *Date:* 2019-02-01 | *Effective From:* 2019-02-01
   - *Title:* Clarification on movement of goods under job work between states and piecemeal return.
   - *Subjects:* `["job_work", "interstate", "partial_return"]`

7. **`INST-GST-JW-007`**: Circular No. 126/45/2019-GST
   - *Authority:* CBIC | *Date:* 2019-11-22 | *Effective From:* 2019-11-22
   - *Title:* Clarification on scope of the notification relating to job work services (registered vs unregistered).
   - *Subjects:* `["job_work", "unregistered_persons", "rate_differential"]`

8. **`INST-GST-JW-008`**: Notification No. 38/2023-Central Tax
   - *Authority:* CBIC | *Date:* 2023-08-04 | *Effective From:* 2023-08-04
   - *Title:* Relaxations and frequency adjustments in filing Form GST ITC-04 for job work.
   - *Subjects:* `["job_work", "itc_04", "compliance_frequency"]`

---

## 2. GST: Composition Scheme & Thresholds (Central Jurisdiction)

9. **`INST-GST-COMP-001`**: Central Goods and Services Tax Act, 2017 - Section 10
   - *Authority:* Central Legislature | *Date:* 2017-04-12 | *Effective From:* 2017-07-01
   - *Title:* Section 10: Statutory provisions governing Composition Levy.
   - *Subjects:* `["composition_scheme", "eligibility", "statutory_provisions"]`

10. **`INST-GST-COMP-002`**: Notification No. 08/2017-Central Tax
    - *Authority:* CBIC | *Date:* 2017-06-27 | *Effective From:* 2017-07-01
    - *Title:* Prescribing turnover limit for composition levy (₹75 Lakhs initially).
    - *Subjects:* `["composition_scheme", "turnover_limit"]`

11. **`INST-GST-COMP-003`**: Notification No. 14/2019-Central Tax
    - *Authority:* CBIC | *Date:* 2019-03-07 | *Effective From:* 2019-04-01
    - *Title:* Enhanced turnover limit of ₹1.5 Crore for manufacturers and traders opting for composition.
    - *Relation:* `supersedes` `INST-GST-COMP-002`
    - *Subjects:* `["composition_scheme", "enhanced_limit", "one_point_five_crore"]`

12. **`INST-GST-COMP-004`**: Notification No. 02/2019-Central Tax (Rate)
    - *Authority:* CBIC | *Date:* 2019-03-07 | *Effective From:* 2019-04-01
    - *Title:* Special composition scheme for service providers with turnover up to ₹50 Lakhs (6% total rate).
    - *Subjects:* `["composition_scheme", "service_providers", "fifty_lakh_limit"]`

13. **`INST-GST-COMP-005`**: Notification No. 10/2019-Central Tax
    - *Authority:* CBIC | *Date:* 2019-03-07 | *Effective From:* 2019-04-01
    - *Title:* Exemption from mandatory registration for persons exclusively supplying goods up to ₹40 Lakhs.
    - *Subjects:* `["registration_threshold", "exclusive_goods", "forty_lakhs"]`

14. **`INST-GST-COMP-006`**: Circular No. 77/51/2018-GST
    - *Authority:* CBIC | *Date:* 2018-12-31 | *Effective From:* 2018-12-31
    - *Title:* Clarification on denial of composition option and recovery of tax in case of wrongful availing.
    - *Subjects:* `["composition_scheme", "violations", "penalties"]`

---

## 3. GST: Input Tax Credit (ITC) & E-Invoicing (Central Jurisdiction)

15. **`INST-GST-ITC-001`**: Central Goods and Services Tax Act, 2017 - Section 16
    - *Authority:* Central Legislature | *Date:* 2017-04-12 | *Effective From:* 2017-07-01
    - *Title:* Section 16: Eligibility and conditions for taking Input Tax Credit.
    - *Subjects:* `["itc", "eligibility", "payment_within_180_days"]`

16. **`INST-GST-ITC-002`**: Central Goods and Services Tax Act, 2017 - Section 17
    - *Authority:* Central Legislature | *Date:* 2017-04-12 | *Effective From:* 2017-07-01
    - *Title:* Section 17: Apportionment of credit and blocked/ineligible credits (Section 17(5)).
    - *Subjects:* `["itc", "blocked_credit", "motor_vehicles", "food_beverages"]`

17. **`INST-GST-ITC-003`**: Central Goods and Services Tax Rules, 2017 - Rule 36(4)
    - *Authority:* CBIC | *Date:* 2019-10-09 | *Effective From:* 2019-10-09
    - *Title:* Rule 36(4): Restriction on availment of ITC in respect of invoices not uploaded in GSTR-1.
    - *Subjects:* `["itc", "rule_36_4", "gstr_2b"]`

18. **`INST-GST-ITC-004`**: Circular No. 123/42/2019-GST
    - *Authority:* CBIC | *Date:* 2019-11-11 | *Effective From:* 2019-11-11
    - *Title:* Clarification on restriction on availment of ITC under rule 36(4).
    - *Subjects:* `["itc", "rule_36_4", "reconciliation"]`

19. **`INST-GST-ITC-005`**: Circular No. 170/02/2022-GST
    - *Authority:* CBIC | *Date:* 2022-07-06 | *Effective From:* 2022-07-06
    - *Title:* Mandatory reporting of correct ITC availment, reversal, and ineligible ITC in GSTR-3B.
    - *Subjects:* `["itc", "gstr_3b", "table_4", "reversal"]`

20. **`INST-GST-ITC-006`**: Circular No. 183/15/2022-GST
    - *Authority:* CBIC | *Date:* 2022-12-27 | *Effective From:* 2022-12-27
    - *Title:* Clarification on ITC mismatch between GSTR-3B and GSTR-2A for FY 2017-18 and 2018-19.
    - *Subjects:* `["itc_mismatch", "ca_certificate", "supplier_declaration"]`

21. **`INST-GST-ITC-007`**: Circular No. 193/05/2023-GST
    - *Authority:* CBIC | *Date:* 2023-07-17 | *Effective From:* 2023-07-17
    - *Title:* Clarification on dealing with verification of ITC mismatch for FY 2019-20 and 2020-21.
    - *Subjects:* `["itc_mismatch", "interim_period", "rule_36_4"]`

22. **`INST-GST-ITC-008`**: Notification No. 13/2020-Central Tax
    - *Authority:* CBIC | *Date:* 2020-03-21 | *Effective From:* 2020-10-01
    - *Title:* Implementation of E-Invoicing and prescribing turnover thresholds.
    - *Subjects:* `["e_invoicing", "threshold", "qr_code"]`

23. **`INST-GST-ITC-009`**: Notification No. 10/2023-Central Tax
    - *Authority:* CBIC | *Date:* 2023-05-10 | *Effective From:* 2023-08-01
    - *Title:* Reduction of E-Invoicing aggregate turnover threshold to ₹5 Crore for MSMEs.
    - *Relation:* `amends` `INST-GST-ITC-008`
    - *Subjects:* `["e_invoicing", "five_crore", "msme_threshold"]`

---

## 4. GST: Reverse Charge & E-Way Bill (Central Jurisdiction)

24. **`INST-GST-RCM-001`**: Notification No. 13/2017-Central Tax (Rate)
    - *Authority:* CBIC | *Date:* 2017-06-28 | *Effective From:* 2017-07-01
    - *Title:* Comprehensive notification specifying services subject to Reverse Charge Mechanism (RCM).
    - *Subjects:* `["rcm", "reverse_charge", "advocates", "director_services"]`

25. **`INST-GST-RCM-002`**: Notification No. 29/2018-Central Tax (Rate)
    - *Authority:* CBIC | *Date:* 2018-12-31 | *Effective From:* 2019-01-01
    - *Title:* Amendments in RCM for Goods Transport Agency (GTA) and security services.
    - *Relation:* `amends` `INST-GST-RCM-001`
    - *Subjects:* `["rcm", "gta", "security_services"]`

26. **`INST-GST-EWB-001`**: Central Goods and Services Tax Rules, 2017 - Rule 138
    - *Authority:* CBIC | *Date:* 2017-06-28 | *Effective From:* 2018-04-01
    - *Title:* Rule 138: Generation and movement conditions for Electronic Way Bill (E-Way Bill).
    - *Subjects:* `["e_way_bill", "rule_138", "consignment_value_50k"]`

27. **`INST-GST-EWB-002`**: Circular No. 47/21/2018-GST
    - *Authority:* CBIC | *Date:* 2018-06-08 | *Effective From:* 2018-06-08
    - *Title:* Clarifications on E-Way Bill generation in case of vehicle breakdown and transshipment.
    - *Subjects:* `["e_way_bill", "vehicle_breakdown", "validity_extension"]`

---

## 5. MSME / Udyam Schemes & Statutory Protections (Central Jurisdiction)

28. **`INST-MSME-UDYAM-001`**: Notification S.O. 2119(E)
    - *Authority:* Ministry of MSME | *Date:* 2020-06-26 | *Effective From:* 2020-07-01
    - *Title:* Composite criteria for classification of Micro, Small, and Medium Enterprises and Udyam Portal.
    - *Subjects:* `["udyam", "classification", "investment_turnover_composite"]`

29. **`INST-MSME-UDYAM-002`**: Notification S.O. 2347(E)
    - *Authority:* Ministry of MSME | *Date:* 2021-06-16 | *Effective From:* 2021-06-16
    - *Title:* Inclusion of Retail and Wholesale Trades under MSME classification for priority lending.
    - *Relation:* `amends` `INST-MSME-UDYAM-001`
    - *Subjects:* `["udyam", "retail_traders", "wholesale_trade"]`

30. **`INST-MSME-UDYAM-003`**: Notification S.O. 4926(E)
    - *Authority:* Ministry of MSME | *Date:* 2022-10-18 | *Effective From:* 2022-10-18
    - *Title:* Retention of non-tax MSME benefits for 3 years post-graduation to a higher category.
    - *Subjects:* `["udyam", "enterprise_upgradation", "benefit_continuation"]`

31. **`INST-MSME-DELAY-001`**: MSMED Act, 2006 - Section 15
    - *Authority:* Central Legislature | *Date:* 2006-06-16 | *Effective From:* 2006-10-02
    - *Title:* Statutory liability of buyer to make payment within 45 days (or agreed 15 days).
    - *Subjects:* `["delayed_payment", "section_15", "forty_five_days_limit"]`

32. **`INST-MSME-DELAY-002`**: MSMED Act, 2006 - Section 16 & 17
    - *Authority:* Central Legislature | *Date:* 2006-06-16 | *Effective From:* 2006-10-02
    - *Title:* Penal compound interest at 3x RBI bank rate for delayed payments to MSMEs.
    - *Subjects:* `["delayed_payment", "penal_interest", "three_times_bank_rate", "samadhaan"]`

33. **`INST-MSME-IT-001`**: Finance Act, 2023 - Insertion of Section 43B(h)
    - *Authority:* Ministry of Finance | *Date:* 2023-03-31 | *Effective From:* 2024-04-01
    - *Title:* Section 43B(h): Income tax disallowance of expenditure for unpaid dues to Micro/Small enterprises beyond MSMED limits.
    - *Subjects:* `["section_43b_h", "income_tax_deduction", "delayed_payments"]`

---

## 6. Gujarat State Policies & Commercial Tax Circulars (Gujarat Jurisdiction)

34. **`INST-GUJ-POLICY-001`**: Gujarat Industrial Policy 2020 - Resolution No. SSI/102020/346/CH
    - *Authority:* Industries & Mines Dept, Govt of Gujarat | *Date:* 2020-09-01 | *Effective From:* 2020-09-01
    - *Title:* Umbrella Scheme for Assistance to Micro, Small and Medium Enterprises (MSMEs) in Gujarat.
    - *Subjects:* `["gujarat_msme", "industrial_policy", "assistance_scheme"]`

35. **`INST-GUJ-POLICY-002`**: Gujarat MSME Capital Investment Subsidy Guidelines
    - *Authority:* Industries Commissionerate, Gujarat | *Date:* 2020-10-05 | *Effective From:* 2020-09-01
    - *Title:* Category-wise capital subsidy (up to 25% in Category 3 talukas, up to ₹35 Lakhs) for new MSME plants.
    - *Subjects:* `["capital_subsidy", "taluka_categories", "plant_machinery"]`

36. **`INST-GUJ-POLICY-003`**: Gujarat MSME Interest Subsidy Scheme on Term Loans
    - *Authority:* Industries Commissionerate, Gujarat | *Date:* 2020-10-05 | *Effective From:* 2020-09-01
    - *Title:* Term loan interest subsidy (5% to 7% per annum for 5 to 7 years) for MSME units.
    - *Subjects:* `["interest_subsidy", "term_loan", "financial_assistance"]`

37. **`INST-GUJ-POLICY-004`**: Gujarat Textile Policy 2019 - Power Tariff & Capital Subsidy
    - *Authority:* Industries & Mines Dept, Govt of Gujarat | *Date:* 2019-01-10 | *Effective From:* 2018-09-04
    - *Title:* Special incentives for weaving, knitting, and textile processing units in Surat and Gujarat.
    - *Subjects:* `["gujarat_textiles", "power_subsidy", "weaving_knitting"]`

38. **`INST-GUJ-LABOUR-001`**: Gujarat Shops and Establishments Act, 2019 (Act No. 4 of 2019)
    - *Authority:* Labour & Employment Dept, Gujarat | *Date:* 2019-03-07 | *Effective From:* 2019-05-01
    - *Title:* Regulation of employment, working hours, and registration exemptions for units with <10 workers.
    - *Subjects:* `["gujarat_labour", "shops_establishments", "gumasta_dhara", "small_shops"]`

39. **`INST-GUJ-SGST-001`**: Gujarat SGST Circular No. 01/2022-GST
    - *Authority:* Chief Commissioner of State Tax, Gujarat | *Date:* 2022-04-12 | *Effective From:* 2022-04-12
    - *Title:* Standard operating procedure for return scrutiny of MSMEs under Gujarat SGST Act.
    - *Subjects:* `["gujarat_sgst", "return_scrutiny", "sop"]`

40. **`INST-GUJ-SGST-002`**: Gujarat SGST Circular No. 03/2023-GST
    - *Authority:* Chief Commissioner of State Tax, Gujarat | *Date:* 2023-06-20 | *Effective From:* 2023-06-20
    - *Title:* Guidelines on physical verification of business premises and prevention of bogus billing.
    - *Subjects:* `["gujarat_sgst", "physical_verification", "bogus_billing"]`
