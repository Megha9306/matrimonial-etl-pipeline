"""
Generate comprehensive summaries of matrimonial records using OpenAI.
Creates a full "About Yourself" section based on extracted profile data.
"""

import os
from typing import Dict, Any, Optional
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_profile_summary(profile: Dict[str, Any]) -> Optional[str]:
    """
    Generate a comprehensive summary of a matrimonial profile using OpenAI.
    
    Includes personal information, family details (parents), education, occupation,
    lifestyle interests, and any other relevant details from the extracted profile.
    
    Args:
        profile: Dictionary containing extracted biodata fields
        
    Returns:
        Generated summary string, or None if generation fails
    """
    
    # Build a description of the profile from available fields
    profile_text = _build_profile_text(profile)
    
    if not profile_text.strip():
        return None
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.5,
            max_tokens=500,
            messages=[
                {
                    "role": "system",
                    "content": """You are a matrimonial profile writer. Generate a natural, 
professional summary of a person's profile based on their extracted information.
The summary should be written in first person, highlight key characteristics, 
family background, education, occupation, and any relevant personal details.
Keep it concise but comprehensive (2-4 paragraphs maximum).
Format: Write in a warm, personal tone suitable for matrimonial profiles."""
                },
                {
                    "role": "user",
                    "content": f"""Based on this matrimonial profile information, write a comprehensive 
summary for the "About Yourself" section:

{profile_text}

Generate a natural summary that includes personal details, family background, education, 
occupation, and any other relevant information that helps paint a complete picture of this person."""
                }
            ]
        )
        
        if response.choices and len(response.choices) > 0:
            summary = response.choices[0].message.content.strip()
            return summary if summary else None
        
        return None
        
    except Exception as e:
        print(f"Error generating summary: {e}")
        return None


def _build_profile_text(profile: Dict[str, Any]) -> str:
    """
    Build a text description of the profile from extracted fields.
    
    Args:
        profile: Dictionary of extracted biodata fields
        
    Returns:
        Formatted text describing the profile
    """
    
    lines = []
    
    # Personal Information
    if profile.get("full_name"):
        lines.append(f"Name: {profile['full_name']}")
    
    if profile.get("gender"):
        lines.append(f"Gender: {profile['gender']}")
    
    if profile.get("date_of_birth"):
        lines.append(f"Date of Birth: {profile['date_of_birth']}")
    
    if profile.get("age"):
        lines.append(f"Age: {profile['age']}")
    
    # Physical Attributes
    if profile.get("height"):
        lines.append(f"Height: {profile['height']}")
    
    # Family & Community
    if profile.get("caste"):
        lines.append(f"Caste: {profile['caste']}")
    
    if profile.get("jaati"):
        lines.append(f"Jaati: {profile['jaati']}")
    
    if profile.get("religion"):
        lines.append(f"Religion: {profile['religion']}")
    
    if profile.get("gotra"):
        lines.append(f"Gotra: {profile['gotra']}")
    
    if profile.get("manglik"):
        lines.append(f"Manglik Status: {profile['manglik']}")
    
    # Marital Status
    if profile.get("marital_status"):
        lines.append(f"Marital Status: {profile['marital_status']}")
    
    # Education
    if profile.get("education"):
        education_line = f"Education: {profile['education']}"
        if profile.get("specialization"):
            education_line += f" ({profile['specialization']})"
        lines.append(education_line)
    
    # Occupation & Income
    if profile.get("occupation"):
        lines.append(f"Occupation: {profile['occupation']}")
    
    if profile.get("annual_income"):
        lines.append(f"Annual Income: {profile['annual_income']}")
    
    # Location
    location_parts = []
    if profile.get("city"):
        location_parts.append(profile["city"])
    if profile.get("state"):
        location_parts.append(profile["state"])
    if profile.get("country"):
        location_parts.append(profile["country"])
    
    if location_parts:
        lines.append(f"Location: {', '.join(location_parts)}")
    
    if profile.get("address"):
        lines.append(f"Address: {profile['address']}")
    
    # Contact Information
    if profile.get("mobile_no"):
        lines.append(f"Mobile: {profile['mobile_no']}")
    
    if profile.get("email_id"):
        lines.append(f"Email: {profile['email_id']}")
    
    # Birth Details
    if profile.get("birth_place"):
        lines.append(f"Birth Place: {profile['birth_place']}")
    
    if profile.get("birth_time"):
        lines.append(f"Birth Time: {profile['birth_time']}")
    
    # Existing summary/about yourself section
    if profile.get("about_yourself_summary"):
        lines.append(f"\nExisting Summary: {profile['about_yourself_summary']}")
    
    return "\n".join(lines)


__all__ = [
    "generate_profile_summary",
]
