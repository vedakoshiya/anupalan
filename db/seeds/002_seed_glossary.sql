-- ==============================================================================
-- Seed: 002_seed_glossary.sql
-- Description: Baseline trilingual glossary (~100 terms) for Anupalan
-- Mapping colloquial Gujarati, Hindi, and Gujlish variants to canonical regulatory terms
-- ==============================================================================

INSERT INTO glossary (canonical_term, variants, language, definition) VALUES
-- 1. Input Tax Credit (ITC)
('Input Tax Credit', 
 ARRAY['ITC', 'itc', 'input credit', 'tax credit', 'ઈનપુટ ટેક્સ ક્રેડિટ', 'ઇનપુટ ક્રેડિટ', 'જમા કર', 'इनपुट टैक्स क्रेडिट', 'इनपुट क्रेडिट'], 
 'gu', 
 'Credit availed on taxes paid on purchase of inputs, capital goods, and services used in furtherance of business.'),

-- 2. Reverse Charge Mechanism (RCM)
('Reverse Charge Mechanism', 
 ARRAY['RCM', 'rcm', 'reverse charge', 'રિવર્સ ચાર્જ', 'આરસીએમ', 'ઉલટો કર', 'रिवर्स चार्ज', 'आरसीएम'], 
 'gu', 
 'Liability to pay tax by the recipient of supply of goods or services instead of the supplier.'),

-- 3. Job Work
('Job Work', 
 ARRAY['job work', 'jobwork', 'job-work', 'જોબ વર્ક', 'જોબવર્ક', 'કારીગરી કામ', 'પ્રોસેસિંગ કામ', 'जॉब वर्क', 'जॉबवर्क', 'मजदूरी काम'], 
 'gu', 
 'Undertaking any treatment or process on goods belonging to another registered person under Section 2(68) of CGST Act.'),

-- 4. Composition Scheme
('Composition Scheme', 
 ARRAY['composition', 'composition scheme', 'samadhan yojana', 'સમાધાન યોજના', 'કોમ્પોઝીશન સ્કીમ', 'કોમ્પોઝિશન', 'कंपोजीशन स्कीम', 'समाधान योजना'], 
 'gu', 
 'Simplified tax payment mechanism under Section 10 of CGST Act for eligible small taxpayers at fixed turnover percentage.'),

-- 5. E-Way Bill
('E-Way Bill', 
 ARRAY['eway bill', 'e-way bill', 'ewaybill', 'ewb', 'ઈ-વે બિલ', 'ઈવે બિલ', 'ઈવેબિલ', 'ई-वे बिल', 'ईवे बिल'], 
 'gu', 
 'Electronically generated compliance document for movement of goods valued above ₹50,000 under Rule 138.'),

-- 6. E-Invoicing
('E-Invoicing', 
 ARRAY['einvoice', 'e-invoice', 'e-invoicing', 'einvoicing', 'ઈ-ઈન્વોઇસ', 'ઇ-બિલ', 'ઈન્વોઈસિંગ', 'ई-इन्वॉयस', 'ई-चालान'], 
 'gu', 
 'Electronic reporting and authentication of B2B invoices on the GST Invoice Registration Portal (IRP).'),

-- 7. Udyam Registration
('Udyam Registration', 
 ARRAY['udyam', 'udyam registration', 'msme certificate', 'udyam portal', 'ઉદ્યમ', 'ઉદ્યમ નોંધણી', 'એમએસએમઈ સર્ટિફિકેટ', 'ઉદ્યોગ આધાર', 'उद्यम रजिस्ट्रेशन', 'एमएसएमई पंजीकरण'], 
 'gu', 
 'Official Government portal and registration process for MSME enterprise recognition under MSMED Act.'),

-- 8. Delayed Payment to MSMEs
('Delayed Payment', 
 ARRAY['delayed payment', 'late payment', '45 days payment', 'પેમેન્ટ વિલંબ', 'મોડું પેમેન્ટ', '૪૫ દિવસનું પેમેન્ટ', 'રૂપિયા બાકી', 'લેણાં', 'देरी से भुगतान', 'विलंबित भुगतान', '45 दिन का नियम'], 
 'gu', 
 'Mandatory timeline under Section 15 of MSMED Act requiring buyers to clear micro/small supplier dues within 45 days.'),

-- 9. Section 43B(h) Disallowance
('Section 43B(h)', 
 ARRAY['43B(h)', 'section 43b', '43b clause h', 'ઇનકમટેક્સ ૪૩બી', '૪૩બી(એચ)', 'ખર્ચ બાદ ન મળવો', 'धारा 43बी(एच)', '43बी का नियम'], 
 'gu', 
 'Income Tax provision disallowing deductions for payments owed to micro and small enterprises not settled within MSMED timelines.'),

-- 10. Goods Transport Agency (GTA)
('Goods Transport Agency', 
 ARRAY['GTA', 'gta', 'transport service', 'transporter', 'ટ્રાન્સપોર્ટર', 'જીટીએ', 'માલવાહક સેવા', 'ભાડું', 'ट्रांसपोर्टर', 'जीटीए'], 
 'gu', 
 'Commercial service of goods transportation by road issuing a consignment note, often governed by RCM.'),

-- 11. Delivery Challan
('Delivery Challan', 
 ARRAY['delivery challan', 'challan', 'job work challan', 'ચલણ', 'ડિલિવરી ચલણ', 'જોબ વર્ક ચલણ', 'કાચું બિલ', 'डिलीवरी चालान', 'चालान'], 
 'gu', 
 'Document issued under Rule 55 for movement of goods for job work, exhibition, or other reasons without immediate sale.'),

-- 12. GSTR-1
('GSTR-1', 
 ARRAY['gstr-1', 'gstr1', 'r1', 'sales return', 'વેચાણ રિટર્ન', 'જીએસટીઆર ૧', 'આર-૧', 'जीएसटीआर-1', 'बिक्री विवरणी'], 
 'gu', 
 'Monthly or quarterly return detailing outward supplies of goods and services made by a registered taxpayer.'),

-- 13. GSTR-3B
('GSTR-3B', 
 ARRAY['gstr-3b', 'gstr3b', '3b', 'monthly return', 'ટેક્સ રિટર્ન', 'જીએસટીઆર ૩બી', '૩-બી', 'जीएसटीआर-3बी'], 
 'gu', 
 'Monthly self-declaration summary return for reporting summarized sales, input tax credit, and tax remittance.'),

-- 14. GSTR-2B
('GSTR-2B', 
 ARRAY['gstr-2b', 'gstr2b', '2b', 'auto drafted itc', 'ઇનપુટ સ્ટેટમેન્ટ', 'જીએસટીઆર ૨બી', '૨-બી', 'जीएसटीआर-2बी'], 
 'gu', 
 'Static auto-drafted statement indicating eligible and ineligible input tax credit available for each tax period.'),

-- 15. Form GST ITC-04
('Form GST ITC-04', 
 ARRAY['itc-04', 'itc 04', 'itc04', 'job work return', 'આઈટીસી-૦૪', 'જોબવર્ક રિટર્ન', 'आईटीसी-04', 'जॉब वर्क रिटर्न'], 
 'gu', 
 'Periodic statement furnished by a principal regarding goods sent to and received back from job workers.'),

-- 16. Blocked Credit (Section 17(5))
('Blocked Credit', 
 ARRAY['blocked credit', 'ineligible itc', 'section 17(5)', '17(5)', 'ક્રેડિટ ના મળે', 'અમાન્ય ક્રેડિટ', 'નામંજૂર આઈટીસી', 'ब्लॉक्ड क्रेडिट', 'अमान्य इनपुट'], 
 'gu', 
 'Specific categories of inward supplies where input tax credit is statutory denied under Section 17(5).'),

-- 17. Micro Enterprise
('Micro Enterprise', 
 ARRAY['micro unit', 'micro enterprise', 'sukshma udyog', 'સૂક્ષ્મ એકમ', 'નાનો ઉદ્યોગ', 'સૂક્ષ્મ ઉદ્યોગ', 'सूक्ष्म उद्यम', 'माइक्रो उद्यम'], 
 'gu', 
 'Enterprise with investment in plant/machinery up to ₹1 Crore and annual turnover up to ₹5 Crore.'),

-- 18. Small Enterprise
('Small Enterprise', 
 ARRAY['small unit', 'small enterprise', 'laghu udyog', 'લઘુ એકમ', 'લઘુ ઉદ્યોગ', 'लघु उद्यम', 'लघु उद्योग', 'स्मॉल उद्यम'], 
 'gu', 
 'Enterprise with investment in plant/machinery up to ₹10 Crore and annual turnover up to ₹50 Crore.'),

-- 19. Medium Enterprise
('Medium Enterprise', 
 ARRAY['medium unit', 'medium enterprise', 'madhyam udyog', 'મધ્યમ એકમ', 'મધ્યમ ઉદ્યોગ', 'मध्यम उद्यम', 'मध्यम उद्योग'], 
 'gu', 
 'Enterprise with investment in plant/machinery up to ₹50 Crore and annual turnover up to ₹250 Crore.'),

-- 20. Capital Subsidy
('Capital Subsidy', 
 ARRAY['capital subsidy', 'investment subsidy', 'subsidy on machinery', 'પ્લાન્ટ સબસિડી', 'મૂડી સહાય', 'સબસિડી', 'મશીનરી સહાય', 'कैपिटल सब्सिडी', 'पूंजीगत सब्सिडी'], 
 'gu', 
 'Government financial grant calculated as a percentage of eligible capital investment in plant and machinery.'),

-- 21. Interest Subsidy
('Interest Subsidy', 
 ARRAY['interest subsidy', 'loan subsidy', 'term loan assistance', 'વ્યાજ સહાય', 'વ્યાજ સબસિડી', 'લોન સહાય', 'બ્યાજ સહાય', 'ब्याज सब्सिडी', 'ऋण सहायता'], 
 'gu', 
 'State assistance providing reimbursement of a fixed percentage of interest charged on bank term loans.'),

-- 22. Dedh Lakh (1,50,000)
('150000', 
 ARRAY['dedh lakh', '1.5 lakh', '150000', 'દોઢ લાખ', '૧૫૦૦૦૦', '૧.૫ લાખ', 'डेढ़ लाख'], 
 'gu', 
 'Vernacular numeric representation for one lakh fifty thousand (1,50,000).'),

-- 23. Dedh Crore (1,50,00,000)
('15000000', 
 ARRAY['dedh crore', '1.5 crore', '1.5 cr', '15000000', 'દોઢ કરોડ', '૧૫૦૦૦૦૦૦', '૧.૫ કરોડ', 'डेढ़ करोड़'], 
 'gu', 
 'Vernacular numeric representation for one crore fifty lakhs (1,50,00,000) — Composition threshold.'),

-- 24. Chalis Lakh (40,00,000)
('4000000', 
 ARRAY['chalis lakh', '40 lakh', '40L', '4000000', 'ચાલીસ લાખ', '૪૦ લાખ', '૪૦૦૦૦૦૦', 'चालीस लाख'], 
 'gu', 
 'Vernacular numeric representation for forty lakhs (40,00,000) — Goods GST registration exemption limit.'),

-- 25. Bees Lakh (20,00,000)
('2000000', 
 ARRAY['bees lakh', '20 lakh', '20L', '2000000', 'વીસ લાખ', '૨૦ લાખ', '૨૦૦૦૦૦૦', 'बीस लाख'], 
 'gu', 
 'Vernacular numeric representation for twenty lakhs (20,00,000) — Services GST registration threshold.'),

-- 26. Pachas Lakh (50,00,000)
('5000000', 
 ARRAY['pachas lakh', '50 lakh', '50L', '5000000', 'પચાસ લાખ', '૫૦ લાખ', '૫૦૦૦૦૦૦', 'पचास लाख'], 
 'gu', 
 'Vernacular numeric representation for fifty lakhs (50,00,000) — Composition scheme limit for service providers.'),

-- 27. Paanch Crore (5,00,00,000)
('50000000', 
 ARRAY['paanch crore', '5 crore', '5 cr', '50000000', 'પાંચ કરોડ', '૫ કરોડ', '૫૦૦૦૦૦૦૦', 'पांच करोड़'], 
 'gu', 
 'Vernacular numeric representation for five crores (5,00,00,000) — E-Invoicing applicability threshold for MSMEs.'),

-- 28. Paanch Takka (5%)
('5%', 
 ARRAY['5%', 'paanch takka', '5 takka', '5 percent', 'પાંચ ટકા', '૫%', '૫ ટકા', 'पांच प्रतिशत', '5 प्रतिशत'], 
 'gu', 
 'Tax percentage rate (5%) applicable to textile job work, essential commodities, and transport.'),

-- 29. Baar Takka (12%)
('12%', 
 ARRAY['12%', 'baar takka', '12 takka', '12 percent', 'બાર ટકા', '૧૨%', '૧૨ ટકા', 'बारह प्रतिशत', '12 प्रतिशत'], 
 'gu', 
 'Tax percentage rate (12%) applicable to registered job work and intermediate manufacturing goods.'),

-- 30. Adhaar Takka (18%)
('18%', 
 ARRAY['18%', 'adhaar takka', '18 takka', '18 percent', 'અઢાર ટકા', '૧૮%', '૧૮ ટકા', 'अठारह प्रतिशत', '18 प्रतिशत'], 
 'gu', 
 'Standard service tax rate (18%) and rate for job work performed for unregistered principals.'),

-- 31. HSN Code
('HSN Code', 
 ARRAY['HSN', 'hsn', 'hsn code', 'commodity code', 'એચએસએન કોડ', 'એચએસએન', 'માલનો કોડ', 'एचएसएन कोड', 'एचएसएन'], 
 'gu', 
 'Harmonized System of Nomenclature code used for systematic classification of goods under GST.'),

-- 32. SAC Code
('SAC Code', 
 ARRAY['SAC', 'sac', 'sac code', 'service code', 'એસએસી કોડ', 'એસએસી', 'સર્વિસ કોડ', 'एसएसी कोड', 'एसएसी'], 
 'gu', 
 'Services Accounting Code prescribed for uniform categorization and tax levy on services.'),

-- 33. Weaving & Knitting (Textiles)
('Weaving and Knitting', 
 ARRAY['weaving', 'knitting', 'textile job work', 'કાપડ વણાટ', 'વણાટકામ', 'નીટિંગ', 'કાપડ પ્રોસેસ', 'ટેક્સટાઇલ જોબવર્ક', 'बुनाई', 'कढ़ाई', 'कपड़ा बुनाई'], 
 'gu', 
 'Textile manufacturing and job work processes prevalent in Surat and Gujarat industrial clusters.'),

-- 34. Dyeing and Printing
('Dyeing and Printing', 
 ARRAY['dyeing', 'printing', 'mill process', 'ડાઇંગ', 'પ્રિન્ટિંગ', 'પ્રોસેસિંગ મિલ', 'કાપડ ડાઇંગ', 'ડાઈંગ મિલ', 'रंगाई और छपाई', 'डाइंग'], 
 'gu', 
 'Textile processing sector involving coloring and design printing on grey fabrics under job work.'),

-- 35. Grey Fabric
('Grey Fabric', 
 ARRAY['grey fabric', 'grey cloth', 'taka', 'કાચું કાપડ', 'ગ્રે કાપડ', 'તાકા', 'ગ્રે તાકો', 'ग्रे कपड़ा', 'कच्चा कपड़ा'], 
 'gu', 
 'Raw unbleached and undyed woven or knitted cloth delivered to job workers for finishing.'),

-- 36. Karigar / Artisan
('Artisan / Job Worker', 
 ARRAY['karigar', 'job worker', 'artisan', 'કારીગર', 'જોબ વર્કર', 'મજૂર', 'કારીગરો', 'कारीगर', 'जॉब वर्कर'], 
 'gu', 
 'Skilled craftsman or small sub-contractor performing processing, embroidery, or diamond polishing.'),

-- 37. Munshi / Accountant
('Accountant / Munshi', 
 ARRAY['munshi', 'accountant', 'tax consultant', 'મુનશી', 'એકાઉન્ટન્ટ', 'નામાવાળા', 'મુનીમ', 'मुंशी', 'मुनीम', 'लेखाकार'], 
 'gu', 
 'Traditional or certified bookkeeper responsible for maintaining day-to-day accounts and compliance.'),

-- 38. Bahi-Khata / Books of Account
('Books of Account', 
 ARRAY['bahi khata', 'khata', 'books of account', 'ચોપડા', 'ખાતાવહી', 'બહી ખાતા', 'રોકડમેળ', 'ખાતું', 'बही-खाता', 'खाताबही', 'लेखा पुस्तकें'], 
 'gu', 
 'Statutory financial journals, ledgers, and inventory registers required to be maintained under Section 35.'),

-- 39. MSME Samadhaan
('MSME Samadhaan', 
 ARRAY['samadhaan', 'samadhan portal', 'msefc', 'સમાધાન પોર્ટલ', 'પેમેન્ટ ફરિયાદ', 'ફેસિલિટેશન કાઉન્સિલ', 'समाधान पोर्टल', 'एमएसएमई समाधान'], 
 'gu', 
 'Government conciliation and arbitration portal for delayed payments recovery under MSEFC.'),

-- 40. Gumastha Dhara (Shops & Establishments)
('Shops and Establishments Registration', 
 ARRAY['gumastha', 'gumasta dhara', 'shops establishment', 'ગુમાસ્તા ધારો', 'ગુમાસ્તા લાયસન્સ', 'દુકાન નોંધણી', 'ગુમાસ્તો', 'गुमाश्ता धारा', 'दुकान लाइसेंस'], 
 'gu', 
 'Local municipal/state regulatory registration under Gujarat Shops and Establishments Act, 2019.'),

-- 41. Bogus Billing
('Bogus Billing / Fake Invoicing', 
 ARRAY['bogus billing', 'fake invoice', 'circular trading', 'બોગસ બિલિંગ', 'ખોટા બિલ', 'હવાલા બિલ', 'બોગસ આઈટીસી', 'फर्जी बिलिंग', 'बोगस बिल'], 
 'gu', 
 'Fraudulent generation of tax invoices without actual movement of underlying goods to illegitimately claim ITC.'),

-- 42. Annual Return (GSTR-9)
('GSTR-9 Annual Return', 
 ARRAY['gstr-9', 'gstr9', 'annual return', 'વાર્ષિક રિટર્ન', 'જીએસટીઆર ૯', 'જીએસટીઆર-૯', 'वार्षिक रिटर्न', 'जीएसटीआर-9'], 
 'gu', 
 'Comprehensive annual audit return consolidating all monthly/quarterly filings of a financial year.'),

-- 43. Audit Threshold
('GST Audit Threshold', 
 ARRAY['audit limit', 'gst audit', 'self certification', 'ઓડિટ મર્યાદા', 'જીએસટી ઓડિટ', 'સીએ ઓડિટ', 'ऑडिट सीमा', 'जीएसटी ऑडिट'], 
 'gu', 
 'Annual turnover threshold requiring self-certified reconciliation statement in Form GSTR-9C.'),

-- 44. Credit Note
('Credit Note', 
 ARRAY['credit note', 'cr note', 'ક્રેડિટ નોટ', 'જમા ચિઠ્ઠી', 'ભાવ ઘટાડો', 'ક્રેડીટ નોટ', 'क्रेडिट नोट', 'जमा चिट्ठी'], 
 'gu', 
 'Statutory instrument issued under Section 34 by supplier reducing tax liability due to returns, discounts, or defects.'),

-- 45. Debit Note
('Debit Note', 
 ARRAY['debit note', 'dr note', 'ડેબિટ નોટ', 'ઉધાર ચિઠ્ઠી', 'ડેબીટ નોટ', 'डेबिट नोट', 'उधार चिट्ठी'], 
 'gu', 
 'Statutory instrument issued by supplier increasing tax liability due to upward price revisions or quantity additions.'),

-- 46. Interest on Delayed Payment
('Penal Interest', 
 ARRAY['penal interest', 'delay interest', '3x bank rate', 'દંડનીય વ્યાજ', 'પેનલ્ટી વ્યાજ', '૩ ગણું વ્યાજ', 'વ્યાજ ચૂકવણી', 'दंडात्मक ब्याज', 'विलंब ब्याज'], 
 'gu', 
 'Statutory compound interest payable at 3 times RBI repo rate for delayed payments to MSMEs under Section 16 of MSMED Act.'),

-- 47. 180 Days Payment Rule
('180 Days Rule for ITC', 
 ARRAY['180 days rule', '180 divas', 'payment within 180 days', '૧૮૦ દિવસનો નિયમ', '૧૮૦ દિવસમાં ચુકવણી', 'આઈટીસી રિવર્સલ', '180 दिन का नियम'], 
 'gu', 
 'Proviso to Section 16(2) CGST Act mandating reversal of ITC if recipient fails to pay supplier within 180 days.'),

-- 48. Form DRC-01B (ITC Mismatch)
('Form DRC-01B', 
 ARRAY['drc-01b', 'drc01b', 'itc intimation', 'ડીઆરસી-૦૧બી', 'આઈટીસી નોટિસ', 'ડિફરન્સ નોટિસ', 'डीआरसी-01बी'], 
 'gu', 
 'Electronic intimation issued systemically for substantial difference between ITC availed in GSTR-3B and available in GSTR-2B.'),

-- 49. Form DRC-01C (Liability Mismatch)
('Form DRC-01C', 
 ARRAY['drc-01c', 'drc01c', 'liability intimation', 'ડીઆરસી-૦૧સી', 'ટેક્સ તફાવત નોટિસ', 'લાયબિલિટી નોટિસ', 'डीआरसी-01सी'], 
 'gu', 
 'System-generated intimation for variance between tax liability reported in GSTR-1 and tax discharged via GSTR-3B.'),

-- 50. Taluka Category (Gujarat MSME Subsidy)
('Taluka Category', 
 ARRAY['taluka category', 'category 1 2 3', 'taluka grading', 'તાલુકા કેટેગરી', 'પછાત તાલુકો', 'કેટેગરી ૩ તાલુકો', 'તાલુકા વર્ગીકરણ', 'तालुका श्रेणी'], 
 'gu', 
 'State industrial classification dividing talukas into Category 1, 2, and 3 to determine quantum of capital subsidy.');
