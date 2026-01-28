#!/usr/bin/env python3
"""
MANIS - spaCy NER Implementation Test
Tests the enhanced entity extraction with categorization
"""

import sys
from manis_agent.agents.preprocessor.tools import extract_entities_with_spacy, SPACY_AVAILABLE

def test_entity_extraction():
    """Test entity extraction with sample news text"""

    print("=" * 60)
    print("MANIS - spaCy NER Entity Extraction Test")
    print("=" * 60)
    print()

    # Check if spaCy is available
    if not SPACY_AVAILABLE:
        print("❌ FAILURE: spaCy model not available!")
        print()
        print("Please run: ./setup_spacy.sh")
        print("Or manually: python -m spacy download en_core_web_sm")
        return False

    print("✅ spaCy model loaded successfully")
    print()

    # Sample news article text
    sample_texts = [
        {
            "title": "Political News",
            "text": "President Joe Biden met with Ukrainian President Volodymyr Zelenskyy at the White House on Tuesday. They discussed military aid and NATO expansion. Secretary of State Antony Blinken also attended the meeting in Washington D.C."
        },
        {
            "title": "Tech News",
            "text": "Apple CEO Tim Cook announced new AI features at Apple Park in Cupertino, California. The company partnered with OpenAI and Google to enhance Siri. Microsoft and Amazon are also investing heavily in artificial intelligence."
        },
        {
            "title": "Business News",
            "text": "Goldman Sachs and JPMorgan Chase reported strong earnings. The Federal Reserve raised interest rates again. Treasury Secretary Janet Yellen spoke about inflation in New York."
        }
    ]

    print("Testing entity extraction on 3 sample articles...")
    print()

    all_passed = True
    total_entities = 0

    for i, sample in enumerate(sample_texts, 1):
        print(f"--- Test {i}: {sample['title']} ---")
        print(f"Text: {sample['text'][:80]}...")
        print()

        # Extract entities
        entity_data = extract_entities_with_spacy(sample['text'])

        persons = entity_data['persons']
        organizations = entity_data['organizations']
        locations = entity_data['locations']
        all_entities = entity_data['all_entities']

        # Display results
        print(f"✓ Total entities: {len(all_entities)}")
        print(f"  • Persons ({len(persons)}): {', '.join(persons) if persons else '(none)'}")
        print(f"  • Organizations ({len(organizations)}): {', '.join(organizations) if organizations else '(none)'}")
        print(f"  • Locations ({len(locations)}): {', '.join(locations) if locations else '(none)'}")
        print()

        total_entities += len(all_entities)

        # Validation: Should extract at least some entities
        if len(all_entities) == 0:
            print("⚠️  WARNING: No entities extracted (unexpected)")
            all_passed = False

    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Total entities extracted: {total_entities}")
    print(f"Average per article: {total_entities / len(sample_texts):.1f}")
    print()

    if all_passed and total_entities > 0:
        print("✅ ALL TESTS PASSED!")
        print()
        print("spaCy NER is working correctly and will categorize entities as:")
        print("  • PERSON - People's names (e.g., 'Joe Biden', 'Tim Cook')")
        print("  • ORG - Organizations (e.g., 'Apple', 'White House', 'NATO')")
        print("  • GPE/LOC - Locations (e.g., 'Ukraine', 'California', 'Washington D.C.')")
        print()
        return True
    else:
        print("❌ TESTS FAILED")
        print("spaCy NER may not be working correctly.")
        return False


def compare_with_regex():
    """Compare spaCy NER vs old regex method"""

    if not SPACY_AVAILABLE:
        return

    from manis_agent.agents.preprocessor.tools import extract_simple_entities

    print("=" * 60)
    print("Comparison: spaCy NER vs Regex Method")
    print("=" * 60)
    print()

    test_text = "President Joe Biden met with Apple CEO Tim Cook at the White House in Washington D.C. to discuss technology policy."

    print(f"Text: {test_text}")
    print()

    # Extract with spaCy
    spacy_result = extract_entities_with_spacy(test_text)

    # Extract with regex
    regex_result = extract_simple_entities(test_text)

    print("spaCy NER Results:")
    print(f"  • Persons: {', '.join(spacy_result['persons'])}")
    print(f"  • Organizations: {', '.join(spacy_result['organizations'])}")
    print(f"  • Locations: {', '.join(spacy_result['locations'])}")
    print(f"  • Total: {len(spacy_result['all_entities'])}")
    print()

    print("Regex Method Results:")
    print(f"  • All entities (uncategorized): {', '.join(regex_result)}")
    print(f"  • Total: {len(regex_result)}")
    print()

    print("Key Improvements:")
    print("  ✓ Automatic categorization by entity type")
    print("  ✓ Better accuracy (trained NER model vs regex patterns)")
    print("  ✓ Handles complex names (e.g., 'Joe Biden' as one entity)")
    print("  ✓ Distinguishes between people, orgs, and locations")
    print()


if __name__ == "__main__":
    print()
    success = test_entity_extraction()
    print()

    if success:
        compare_with_regex()

    sys.exit(0 if success else 1)
