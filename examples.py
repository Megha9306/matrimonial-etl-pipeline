"""
Example usage of the LLM Extraction module.
Demonstrates how to use extract_profile() in the pipeline.
"""

import json
import os
from llmextractor import extract_profile, LLMExtractor


def example_1_simple_extraction():
    """Example 1: Simple extraction with default settings."""
    print("=" * 60)
    print("EXAMPLE 1: Simple Profile Extraction")
    print("=" * 60)
    
    text = """
    Name: Priya Sharma
    Age: 26
    Date of Birth: 15 March 1998
    Height: 5'6"
    Gender: Female
    Marital Status: Single
    Profession: Software Developer
    Education: B.Tech in Computer Science
    Religion: Hindu
    Caste: Sharma (Brahmin)
    Location: Bangalore, Karnataka
    """
    
    profile = extract_profile(text)
    print("\nExtracted Profile:")
    print(json.dumps(profile, indent=2))


def example_2_incomplete_data():
    """Example 2: Extraction with missing/incomplete data."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Incomplete Data (Missing Fields)")
    print("=" * 60)
    
    text = """
    Rajesh Kumar
    Works as a Consultant
    From Mumbai
    """
    
    profile = extract_profile(text)
    print("\nExtracted Profile (with nulls for missing fields):")
    print(json.dumps(profile, indent=2))


def example_3_custom_model():
    """Example 3: Using a different model."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Custom Model (Gemini 1.5 Pro)")
    print("=" * 60)
    
    text = """
    Anjali Verma, 24, Doctor, Hindu, Delhi
    """
    
    # Using Gemini 1.5 Pro instead of default gemini-2.0-flash
    profile = extract_profile(text, model="gemini-1.5-pro")
    print("\nExtracted Profile (using Gemini 1.5 Pro):")
    print(json.dumps(profile, indent=2))


def example_4_class_usage():
    """Example 4: Using LLMExtractor class directly."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: LLMExtractor Class Usage")
    print("=" * 60)
    
    # Initialize extractor once
    extractor = LLMExtractor(model="gemini-2.0-flash")
    
    texts = [
        "Vikram Singh, 30, Engineer, Sikh, Delhi",
        "Neha Patel, 25, Doctor, Hindu, Pune",
        "Meera Gupta, 28, Teacher, Hindu, Jaipur",
    ]
    
    print("\nExtracting multiple profiles...")
    for i, text in enumerate(texts, 1):
        profile = extractor.extract(text)
        print(f"\nProfile {i}:")
        print(f"  Name: {profile['full_name']}")
        print(f"  Profession: {profile['profession']}")
        print(f"  Location: {profile['location']}")


def example_5_error_handling():
    """Example 5: Error handling with empty/invalid input."""
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Error Handling")
    print("=" * 60)
    
    # Empty text
    profile1 = extract_profile("")
    print("\nEmpty text input:")
    print(f"Result: {profile1}")
    print(f"All fields null: {all(v is None for v in profile1.values())}")
    
    # Whitespace only
    profile2 = extract_profile("   \n  \t  ")
    print("\nWhitespace-only input:")
    print(f"All fields null: {all(v is None for v in profile2.values())}")


if __name__ == "__main__":
    # Set GOOGLE_API_KEY before running:
    # export GOOGLE_API_KEY="your-google-api-key"
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY environment variable not set")
        print("Set it with: export GOOGLE_API_KEY='your-google-api-key'")
        exit(1)
    
    try:
        # Run examples
        example_1_simple_extraction()
        example_2_incomplete_data()
        example_3_custom_model()
        example_4_class_usage()
        example_5_error_handling()
        
    except Exception as e:
        print(f"\nError: {e}")
        print("\nNote: Ensure GOOGLE_API_KEY is set correctly")
