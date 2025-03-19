# Program types with their specific eligibility criteria
GRANT_PROGRAMS = {
    "Oxfam": {
        "description": "Oxfam International humanitarian and development programs",
        "eligibility_criteria": {
            "Legal Entity": "Is the applicant a legally registered entity with valid documentation?",
            "Experience": "Does the applicant have at least 3 years of experience in humanitarian or development work?",
            "Financial Capacity": "Does the applicant have sufficient financial capacity and adequate financial management systems?",
            "Target Area": "Is the project implemented in Oxfam's priority geographical areas?",
            "Project Duration": "Does the project duration fall within 12-36 months?",
            "Gender Focus": "Does the project incorporate gender equality principles?",
            "Co-funding": "Does the project secure at least a 15% co-funding?"
        },
        "report_questions": [
            "What is the primary objective of this project?",
            "What problem does the project aim to solve?",
            "Who are the target beneficiaries and how many people will benefit?",
            "What is the total budget and how is it allocated across major categories?",
            "What are the key activities and timeline?",
            "How will the project measure success? What are the key performance indicators?",
            "How does the project promote gender equality?",
            "What risks have been identified and how will they be mitigated?",
            "Does the implementing organization have relevant experience for this project?",
            "Is there a sustainability plan for after the grant period ends?"
        ]
    },
    "F4J (Funding for Justice)": {
        "description": "Funding for justice, human rights and legal empowerment projects",
        "eligibility_criteria": {
            "Legal Entity": "Is the applicant a legally registered not-for-profit entity?",
            "Experience": "Does the applicant have at least 2 years of experience in rights-based work?",
            "Human Rights Focus": "Does the project explicitly address a human rights or justice issue?",
            "Target Group": "Does the project target marginalized or vulnerable populations?",
            "Project Duration": "Is the project duration between 6-24 months?",
            "Budget Limit": "Is the requested budget under $100,000?",
            "Co-funding": "Is the project able to provide at least 10% co-funding?"
        },
        "report_questions": [
            "What human rights or justice issue does this project address?",
            "How will the project empower marginalized or vulnerable groups?",
            "What is the project's theory of change?",
            "What are the key activities and timeline?",
            "What is the total budget and how is it allocated?",
            "What measurable outcomes are expected?",
            "What risks have been identified and how will they be mitigated?",
            "What is the organization's experience with similar rights-based work?",
            "How will the project sustain its impact after the funding period?",
            "What advocacy or policy change components does the project include?"
        ]
    },
    "UNDP": {
        "description": "United Nations Development Programme sustainable development grants",
        "eligibility_criteria": {
            "Legal Entity": "Is the applicant a legally registered entity?",
            "Alignment with SDGs": "Does the project explicitly align with one or more SDGs?",
            "Development Focus": "Is the primary focus on sustainable development?",
            "Local Implementation": "Does the project have a local implementation strategy?",
            "Project Duration": "Is the project duration between 12-48 months?",
            "Environmental Impact": "Does the project demonstrate positive environmental impact?",
            "Co-funding": "Does the project secure at least 20% co-funding?"
        },
        "report_questions": [
            "Which Sustainable Development Goals does this project address?",
            "What is the primary development challenge being addressed?",
            "What is the project's implementation strategy?", 
            "Who are the main beneficiaries and stakeholders?",
            "What is the total budget and key budget allocations?",
            "What are the expected outcomes and impacts?",
            "How does the project promote environmental sustainability?",
            "What is the monitoring and evaluation framework?",
            "What partnerships are involved in this project?",
            "How will the project ensure long-term sustainability?"
        ]
    }
} 