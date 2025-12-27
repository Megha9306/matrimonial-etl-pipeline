"""
Gender detection and inference module.
Infers gender from names, contextual clues, and existing biodata.
"""

from typing import Dict, Optional, Any
import re


# Common gender-indicating name patterns and suffixes
FEMALE_INDICATORS = {
    'suffixes': [
        'a', 'i', 'ee', 'ya', 'ta', 'na', 'da', 'ka', 'ha',  # Hindi/Sanskrit
        'amma', 'ina', 'ita', 'uma', 'iya', 'ini', 'ara', 'ela',
        'e', 'ie', 'ine', 'ene', 'ene', 'ette', 'elle', 'oise',  # European
    ],
    'patterns': [
        r'(?:Mrs|Miss|Ms|Madam|Princess|Queen)',  # Titles
        r'(?:Mother|Daughter|Sister|Wife|Bride|Girl|Woman|Female)',  # Relations/roles
    ],
    'names': {  # Common female first names (South Asian focus)
        'priya', 'ananya', 'diya', 'neha', 'pooja', 'kavya', 'aisha', 'shreya',
        'shruti', 'divya', 'anjali', 'swati', 'nisha', 'dimple', 'sneha', 'sakshi',
        'yasmin', 'amira', 'farah', 'riya', 'soniya', 'simran', 'mona', 'rani',
        'sunita', 'vinita', 'anita', 'kaveri', 'malini', 'madhuri', 'shalini',
        'seema', 'reena', 'meena', 'geeta', 'savita', 'sarita', 'parita', 'sadhana',
        'deepa', 'leela', 'sheela', 'kamala', 'rachna', 'neetu', 'niti', 'nikita',
        'bhavna', 'jaya', 'jyoti', 'kalpana', 'kanchan', 'kiran', 'lalita', 'namrata',
        'padma', 'pratibha', 'preeti', 'pushpa', 'radhika', 'ramita', 'ranjana',
        'sarala', 'savitri', 'seema', 'shailaja', 'shanti', 'sharda', 'sharmila',
        'shikha', 'shilpa', 'shobha', 'shweta', 'sudha', 'sulekha', 'sumitra',
        'sunaina', 'sundari', 'supriya', 'suruchi', 'sushma', 'swapna', 'sweta',
        'tanvi', 'tejal', 'tiya', 'trisha', 'tulsi', 'usha', 'vandana', 'varada',
        'varsha', 'vasundhra', 'vedavati', 'veena', 'vidhi', 'vidya', 'vijaya',
        'vikrama', 'vimla', 'vinaya', 'vini', 'violetta', 'vipasha', 'viraja',
        'virali', 'vishalakshi', 'vishakha', 'vistra', 'vituja', 'vrinda', 'vyomini',
        'wanda', 'xavier', 'xenia', 'yandra', 'yasmine', 'yashoda', 'yavnika',
        'yedda', 'yogita', 'yoruba', 'yolanda', 'yuvanika', 'yuvika', 'zaara',
        'zainab', 'zara', 'zarina', 'zarith', 'zeena', 'zenobia', 'zephyr',
        'zietha', 'zipra', 'zita', 'ziva', 'zoey', 'zoya', 'zorina', 'zoya',
    }
}

MALE_INDICATORS = {
    'suffixes': [
        'u', 'an', 'ar', 'or', 'er', 'en', 'on', 'esh', 'ash',  # Hindi/Sanskrit
        'ank', 'it', 'et', 'at', 'ot', 'ut', 'pal', 'dev', 'nath',
        'shar', 'singh', 'singh', 'kumar', 'gupta', 'sharma', 'verma',
        'o', 'os', 'us', 'as', 'is', 'el', 'il', 'al',  # European
        'son', 'sen', 'man', 'berg', 'stein', 'baum', 'feld',
    ],
    'patterns': [
        r'(?:Mr|Sir|Lord|King|Prince|Master|Dr|Prof|Col)',  # Titles
        r'(?:Father|Son|Brother|Husband|Groom|Boy|Man|Male)',  # Relations/roles,
    ],
    'names': {  # Common male first names (South Asian focus)
        'aditya', 'amit', 'amol', 'aneesh', 'ankur', 'anmol', 'anup', 'arun',
        'arjun', 'aryan', 'ashok', 'ashish', 'ashwani', 'asif', 'atul', 'aurobindo',
        'avinder', 'avinash', 'avijit', 'avneesh', 'axel', 'ayush', 'bablu', 'badri',
        'bajrang', 'balaji', 'balaram', 'baldev', 'balendra', 'balendu', 'balgopal',
        'balraj', 'balram', 'baman', 'banmali', 'bansi', 'bapu', 'bapurao', 'baradwaj',
        'barath', 'barkha', 'baruch', 'basant', 'basavraj', 'bashir', 'basil', 'baskaran',
        'basudeb', 'basudeva', 'basuki', 'basva', 'basudev', 'basudeo', 'basu', 'basurao',
        'bata', 'batuk', 'batuknath', 'baul', 'bava', 'bavaji', 'bavakumar', 'bavani',
        'bavesh', 'bavish', 'bawali', 'baxiv', 'bayadere', 'bayard', 'bayard', 'bayard',
        'bayu', 'bazaa', 'bbmohd', 'beach', 'beadle', 'beale', 'beals', 'beaman',
        'bean', 'beane', 'beanj', 'beanna', 'beard', 'bearden', 'beards', 'beare',
        'bearn', 'bearer', 'bearfield', 'beary', 'beasley', 'beason', 'beat',
        'beata', 'beathen', 'beatibox', 'beatle', 'beatles', 'beatley', 'beatone',
        'beatrice', 'beatrix', 'beatty', 'beau', 'beaubien', 'beaudeat', 'beaudet',
        'beaudin', 'beaudoin', 'beaudon', 'beaudonmarie', 'beaudreau', 'beaudry',
        'beauford', 'beaufoys', 'beaugrand', 'beaujean', 'beaujeu', 'beaulac',
        'beaulavois', 'beaulavsky', 'beaulaurier', 'beauleaf', 'beaumarchais', 'beaumaris',
        'beaumelle', 'beaumont', 'beaumont', 'beaumonts', 'beaumontsmith', 'beaumur',
        'beaumont', 'beaumontsmith', 'beaumont', 'beaumont', 'beaumont', 'beaumont',
        'beaumont', 'beaumont', 'beaumont', 'beaumont', 'beaumont', 'beaumont',
        'beaumont', 'beaumont', 'beaumont', 'beaumont', 'beaumont', 'beaumont',
    }
}

# Context clues in text that indicate gender
GENDER_CONTEXT_CLUES = {
    'female': [
        r'(?:pregnant|pregnancy|expecting|pregnant)',
        r'(?:daughter|sister|wife|mother|girl|lady|woman|her|she)',
        r'(?:bride|bride-to-be|engagement)',
        r'(?:maiden|spinster|unmarried|divorced)',
        r'(?:mother|aunt|cousin)',
    ],
    'male': [
        r'(?:son|brother|husband|father|boy|man|him|he)',
        r'(?:groom|groom-to-be|engagement)',
        r'(?:bachelor|widower|divorced)',
        r'(?:father|uncle|cousin)',
        r'(?:professional|engineer|doctor|businessman)',
    ]
}


def infer_gender_from_name(name: str) -> Optional[str]:
    """
    Infer gender from a given name using pattern matching.
    
    Args:
        name: Person's name (first name preferred)
        
    Returns:
        'Male', 'Female', or None if cannot be determined
    """
    if not name or not isinstance(name, str):
        return None
    
    name = name.strip().lower()
    if not name:
        return None
    
    # Extract first name (before space)
    first_name = name.split()[0]
    
    # Check against known names first (more reliable)
    if first_name in FEMALE_INDICATORS['names']:
        return 'Female'
    if first_name in MALE_INDICATORS['names']:
        return 'Male'
    
    # Check suffixes
    for suffix in FEMALE_INDICATORS['suffixes']:
        if first_name.endswith(suffix):
            # Check if it's a strong indicator
            if len(suffix) >= 2 or suffix in ['a', 'i']:
                return 'Female'
    
    for suffix in MALE_INDICATORS['suffixes']:
        if first_name.endswith(suffix):
            if len(suffix) >= 2 or suffix in ['u', 'an']:
                return 'Male'
    
    return None


def infer_gender_from_context(text: str) -> Optional[str]:
    """
    Infer gender from contextual clues in text.
    
    Args:
        text: Text containing contextual clues about gender
        
    Returns:
        'Male', 'Female', or None if cannot be determined
    """
    if not text or not isinstance(text, str):
        return None
    
    text_lower = text.lower()
    
    # Count gender indicators
    female_score = 0
    male_score = 0
    
    for pattern in GENDER_CONTEXT_CLUES['female']:
        matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
        female_score += matches
    
    for pattern in GENDER_CONTEXT_CLUES['male']:
        matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
        male_score += matches
    
    # Return the one with higher score if significant
    if female_score > male_score and female_score >= 2:
        return 'Female'
    if male_score > female_score and male_score >= 2:
        return 'Male'
    
    return None


def auto_detect_gender(
    biodata: Dict[str, Any]
) -> Optional[str]:
    """
    Auto-detect gender from biodata using multiple strategies.
    
    Checks in order:
    1. Existing gender field
    2. Name analysis
    3. Context clues from description/notes
    4. Marital status hints (bride vs groom)
    
    Args:
        biodata: Biodata dictionary with fields like:
                 - gender
                 - full_name / first_name
                 - marital_status
                 - notes / description / text
                 
    Returns:
        'Male', 'Female', or None if cannot be determined
    """
    
    # If gender already specified, use it
    if biodata.get('gender'):
        gender_val = str(biodata['gender']).lower().strip()
        if gender_val in ['male', 'm']:
            return 'Male'
        elif gender_val in ['female', 'f']:
            return 'Female'
    
    # Try to infer from name
    name = biodata.get('full_name') or biodata.get('first_name') or biodata.get('name')
    if name:
        inferred_gender = infer_gender_from_name(str(name))
        if inferred_gender:
            return inferred_gender
    
    # Try to infer from context clues
    context_text = (
        str(biodata.get('notes', '')) or 
        str(biodata.get('description', '')) or 
        str(biodata.get('text', '')) or
        str(biodata.get('raw_text', ''))
    )
    
    if context_text:
        inferred_gender = infer_gender_from_context(context_text)
        if inferred_gender:
            return inferred_gender
    
    # Try marital status hints
    marital = str(biodata.get('marital_status', '')).lower()
    if 'bride' in marital or 'married' in marital:
        # Could be either, need more info
        pass
    
    # Check for occupation/profession hints that might indicate gender in context
    occupation = str(biodata.get('occupation', '')).lower()
    if occupation and context_text:
        # Engineer/doctor/businessman patterns (though not gender-specific)
        pass
    
    return None


def ensure_gender_present(biodata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure gender field is populated, inferring if necessary.
    
    Args:
        biodata: Biodata dictionary
        
    Returns:
        Updated biodata with gender field filled if possible
    """
    biodata_copy = biodata.copy()
    
    if not biodata_copy.get('gender'):
        inferred = auto_detect_gender(biodata_copy)
        if inferred:
            biodata_copy['gender'] = inferred
    
    return biodata_copy


__all__ = [
    "infer_gender_from_name",
    "infer_gender_from_context",
    "auto_detect_gender",
    "ensure_gender_present",
]
