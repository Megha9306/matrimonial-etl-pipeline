"""
Prompt engineering module for matrimonial biodata extraction.
Isolates prompt logic from business logic for maintainability.
"""

from .config import FIELD_DESCRIPTIONS


def get_extraction_prompt(text: str) -> str:
    """
    Generate the extraction prompt for the LLM.
    
    Args:
        text: The plain text to extract matrimonial information from
        
    Returns:
        Formatted prompt string for the LLM
    """
    field_descriptions = "\n".join(
        [f"- {field}: {desc}" for field, desc in FIELD_DESCRIPTIONS.items()]
    )
    
    prompt = f"""Extract matrimonial biodata information from the following text.
Return ONLY a valid JSON object with the specified fields. 
Do not include any explanation, prose, or additional text.

Fields to extract:
{field_descriptions}

CRITICAL FIELD-SPECIFIC CONSTRAINTS (to prevent mismatched data):
1. LOCATION FIELDS (state, city, country, district, village, tahsil, zip_code, address):
   - state: ONLY a state/province/region name (e.g., "Rajasthan", "Maharashtra", "California")
     INVALID STATE VALUES: "Central University of Rajasthan", "XYZ University", "Some School", "Institution Name"
     VALID: Just the state name like "Rajasthan" if someone is from that state
   - city: ONLY a city/town name (e.g., "Bangalore", "Mumbai", "Delhi")
   - country: ONLY a country name (e.g., "India", "USA", "Canada")
   - district: ONLY a district name (e.g., "Alwar", "Jaipur")
   - village: ONLY a village name (e.g., "Rajgarh")
   - tahsil: ONLY a tahsil/administrative unit name
   - zip_code: ONLY numeric postal/zip codes (5-10 digits), NO addresses, NO names
   - address: ONLY street address, locality, area names - NOT personal names, NOT education, NOT institutions

2. EDUCATION FIELDS (education, specialization):
   - education: ONLY degree/qualification (e.g., "MBA", "B.Tech", "B.Com", "M.Sc")
   - specialization: ONLY field of study (e.g., "Computer Science", "Finance", "Marketing")
   - DO NOT put university/school names here - extract only the degree name
   - DO NOT extract institution names like "Central University of Rajasthan", "Delhi University", "IIT", etc.
   - If text says "M.B.A IN FINANCE FROM RAJASTHAN UNIVERSITY": extract education="M.B.A", specialization="Finance", NOT the university name
   - If text has combined format like "Msc(IT)" or "B.Tech(CSE)" → extract education="M.Sc" or "B.Tech", specialization="Information Technology" or "Computer Science"
   - If text says "MBA Finance" or "B.Tech Computer Science" → split into education="MBA"/"B.Tech", specialization="Finance"/"Computer Science"
   - Institution names should NEVER appear in ANY field - ignore them completely

3. PERSONAL FIELDS (first_name, last_name, full_name):
   - first_name: ONLY a person's first name
   - last_name: ONLY a person's last name/surname/family name
   - full_name: ONLY a person's full name
   - DO NOT include titles (Mr., Ms., Dr.) or family relations (Father, Brother, Sister)

4. OCCUPATION/INCOME FIELDS (occupation, annual_income):
   - occupation: ONLY job title or profession (e.g., "Engineer", "Teacher", "Business")
   - annual_income: ONLY income amount (numeric or range)
   - DO NOT put company names here

5. MARITAL STATUS AND MANGLIK FIELDS:
   - marital_status: MUST be one of: "Single", "Married", "Divorced", "Widowed", "Separated", "Un-Married", "Awaiting Divorce"
     Do NOT use any other value - extract ONLY if text explicitly matches one of these
   - manglik: MUST be one of: "Yes", "No", "Don't Know"
     Extract ONLY these exact values - never use "Maybe", "Perhaps", "Unknown" etc.

6. COMMUNITY FIELDS (caste, jaati, gotra, sakha, religion):
   - caste: Caste or community name
   - jaati: Family name or Jaati (e.g., "Pareek", "Sharma", "Patel")
   - gotra: ONLY gotra/clan name (e.g., "Upmanyu", "Bharadwaj")
   - sakha: ONLY sakha/vedic branch (e.g., "Rigveda", "Mudgal")
   - religion: ONLY religion name (e.g., "Hindu", "Muslim", "Christian")
   - DO NOT mix these fields - each has specific meaning

7. DATE/TIME FIELDS (date_of_birth, birth_time, age):
   - date_of_birth: ONLY dates in YYYY-MM-DD format or raw date strings
   - birth_time: ONLY time in HH:MM:SS or HH:MM AM/PM format
   - age: ONLY integer age in years
   - DO NOT put other text here

8. CONTACT FIELDS (mobile_no, phone_no, email_id):
   - mobile_no: Format as +91 followed by 10-digit number (e.g., "+91 9876543210")
     Extract the 10-digit mobile number and format it as: +91 xxxxxxxxxx
     Examples of conversions:
       * "9876543210" → "+91 9876543210"
       * "+919876543210" → "+91 9876543210"
       * "919876543210" → "+91 9876543210"
       * "09876543210" → "+91 9876543210"
   - phone_no: Landline phone numbers (varies by region format)
   - email_id: Email address with @ symbol

IMPORTANT INSTRUCTIONS FOR UNSTRUCTURED DATA:
- If the text is unstructured or contains mixed information, carefully parse and extract ALL available data
- For EDUCATION: Look for degrees (B.Tech, MBA, M.Sc, etc), specializations, fields of study
  Extract only the degree/qualification, NOT the institution name
  Example: "Studied B.Tech in Computer Science from XYZ University" → education="B.Tech", specialization="Computer Science"
- For CASTE/COMMUNITY: Search for Jaati, Caste, Gotra, and Sakha mentions anywhere in text
  These may appear in formats like:
    * "Pareek Brahmin" (jaati=Pareek, caste=Brahmin)
    * "Upmanyu Gotra" (gotra=Upmanyu)
    * "Rigveda Sakha" (sakha=Rigveda)
  Extract each component SEPARATELY and CORRECTLY
- For GENDER: If explicitly stated, use it. Otherwise, will be auto-inferred from name and context
- For LOCATION/ADDRESS: Extract city, state, district, village, and any postal/zip codes mentioned
  Keep location fields separate from address field
  Do NOT put personal names or education in location fields

Rules:
1. Extract ONLY information explicitly present in the text
2. RESPECT FIELD BOUNDARIES - do not put values from one field type into another
3. For fields with multiple parts (like address or education), capture the specific component only
4. Use null for fields with no matching information
5. Ensure date_of_birth is in YYYY-MM-DD format if present
6. Keep values as-is (no normalization or cleaning)
7. Return ONLY valid JSON, no other text
8. For education/caste/location with multiple values, pick the primary/most relevant one
9. ZIP CODES MUST BE NUMERIC ONLY (5-10 digits) - no addresses, no text

Text to extract from:
---
{text}
---

Return ONLY the JSON object (no markdown, no code blocks, no explanation):"""
    
    return prompt


def get_system_prompt() -> str:
    """
    Get the system prompt for the LLM.
    Defines the role and behavior of the extraction agent.
    
    Returns:
        System prompt string
    """
    return """You are a matrimonial biodata information extraction engine.
Your sole purpose is to extract structured information from unstructured text.
You must return ONLY valid JSON with no additional text, explanation, or prose.
Be precise and extract only what is explicitly present in the text."""
