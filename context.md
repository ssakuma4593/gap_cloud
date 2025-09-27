This project involves building a Python-based research gap analysis and visualization tool that:

    Loads medical research abstracts from AWS S3.

    Parses abstracts into structured data (title, authors, year, text).

    Uses OpenAI GPT (or similar LLM) to extract summaries of research gaps from abstracts.

    Stores extracted gaps and metadata in memory for fast access and analysis.

    Supports an interactive frontend (Dash or Streamlit) showing word clouds of gaps by year and topic.

    Emphasizes secure handling of credentials via environment variables.

    Implements modular code organized into scripts for loading data, gap extraction, and in-memory data storage.

    Will be developed incrementally with clear PR-based deliverables.

When answering questions or generating code, please consider:

    Best practices for data engineering, API integration, and visualization.

    Maintaining security (e.g., avoid exposing secrets).

    Writing clear, reusable, and documented Python code.

    Providing explanations and context appropriate to an experienced developer audience.

    Designing for scalability and easy future enhancement.


Here is what the abstract.text files look like:
1. Future Healthc J. 2019 Jun;6(2):94-98. doi: 10.7861/futurehosp.6-2-94.

The potential for artificial intelligence in healthcare.

Davenport T(1), Kalakota R(2).

Author information:
(1)Babson College, Wellesley, USA.
(2)Deloitte Consulting, New York, USA.

The complexity and rise of data in healthcare means that artificial intelligence 
(AI) will increasingly be applied within the field. Several types of AI are 
already being employed by payers and providers of care, and life sciences 
companies. The key categories of applications involve diagnosis and treatment 
recommendations, patient engagement and adherence, and administrative 
activities. Although there are many instances in which AI can perform healthcare 
tasks as well or better than humans, implementation factors will prevent 
large-scale automation of healthcare professional jobs for a considerable 
period. Ethical issues in the application of AI to healthcare are also 
discussed.

DOI: 10.7861/futurehosp.6-2-94
PMCID: PMC6616181
PMID: 31363513


2. Clin Microbiol Infect. 2020 May;26(5):584-595. doi: 10.1016/j.cmi.2019.09.009. 
Epub 2019 Sep 17.

Machine learning for clinical decision support in infectious diseases: a 
narrative review of current applications.

Peiffer-Smadja N(1), Rawson TM(2), Ahmad R(2), Buchard A(3), Georgiou P(4), 
Lescure FX(5), Birgand G(2), Holmes AH(2).

Author information:
(1)National Institute for Health Research Health Protection Research Unit in 
Healthcare Associated Infections and Antimicrobial Resistance, Imperial College 
London, London, UK; French Institute for Medical Research (Inserm), Infection 
Antimicrobials Modelling Evolution (IAME), UMR 1137, University Paris Diderot, 
Paris, France. Electronic address: n.peiffer-smadja@ic.ac.uk.
(2)National Institute for Health Research Health Protection Research Unit in 
Healthcare Associated Infections and Antimicrobial Resistance, Imperial College 
London, London, UK.
(3)Babylon Health, London, UK.
(4)Department of Electrical and Electronic Engineering, Imperial College, 
London, UK.
(5)French Institute for Medical Research (Inserm), Infection Antimicrobials 
Modelling Evolution (IAME), UMR 1137, University Paris Diderot, Paris, France; 
Infectious Diseases Department, Bichat-Claude Bernard Hospital, 
Assistance-Publique Hôpitaux de Paris, Paris, France.

Erratum in
    Clin Microbiol Infect. 2020 Aug;26(8):1118. doi: 10.1016/j.cmi.2020.05.020.

BACKGROUND: Machine learning (ML) is a growing field in medicine. This narrative 
review describes the current body of literature on ML for clinical decision 
support in infectious diseases (ID).
OBJECTIVES: We aim to inform clinicians about the use of ML for diagnosis, 
classification, outcome prediction and antimicrobial management in ID.
SOURCES: References for this review were identified through searches of 
MEDLINE/PubMed, EMBASE, Google Scholar, biorXiv, ACM Digital Library, arXiV and 
IEEE Xplore Digital Library up to July 2019.
CONTENT: We found 60 unique ML-clinical decision support systems (ML-CDSS) 
aiming to assist ID clinicians. Overall, 37 (62%) focused on bacterial 
infections, 10 (17%) on viral infections, nine (15%) on tuberculosis and four 
(7%) on any kind of infection. Among them, 20 (33%) addressed the diagnosis of 
infection, 18 (30%) the prediction, early detection or stratification of sepsis, 
13 (22%) the prediction of treatment response, four (7%) the prediction of 
antibiotic resistance, three (5%) the choice of antibiotic regimen and two (3%) 
the choice of a combination antiretroviral therapy. The ML-CDSS were developed 
for intensive care units (n = 24, 40%), ID consultation (n = 15, 25%), medical 
or surgical wards (n = 13, 20%), emergency department (n = 4, 7%), primary care 
(n = 3, 5%) and antimicrobial stewardship (n = 1, 2%). Fifty-three ML-CDSS (88%) 
were developed using data from high-income countries and seven (12%) with data 
from low- and middle-income countries (LMIC). The evaluation of ML-CDSS was 
limited to measures of performance (e.g. sensitivity, specificity) for 57 
ML-CDSS (95%) and included data in clinical practice for three (5%).
IMPLICATIONS: Considering comprehensive patient data from socioeconomically 
diverse healthcare settings, including primary care and LMICs, may improve the 
ability of ML-CDSS to suggest decisions adapted to various clinical contexts. 
Currents gaps identified in the evaluation of ML-CDSS must also be addressed in 
order to know the potential impact of such tools for clinicians and patients.

Copyright © 2019 European Society of Clinical Microbiology and Infectious 
Diseases. Published by Elsevier Ltd. All rights reserved.

DOI: 10.1016/j.cmi.2019.09.009
PMID: 31539636 [Indexed for MEDLINE]