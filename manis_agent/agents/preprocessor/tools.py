"""Text preprocessing and entity extraction tools."""

import re
from typing import Dict, List
from google.adk.tools.tool_context import ToolContext

# Load spaCy model for Named Entity Recognition
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
except (ImportError, OSError):
    # spaCy not installed or model not downloaded
    nlp = None
    SPACY_AVAILABLE = False
    print("[PREPROCESSOR] spaCy model not available, using fallback entity extraction")


def extract_entities_with_spacy(text: str) -> Dict[str, List[str]]:
    """
    Extract named entities using spaCy NER with categorization.

    Args:
        text: Clean article text

    Returns:
        Dict with 'persons', 'organizations', 'locations', and 'all_entities' keys
    """
    if not SPACY_AVAILABLE or nlp is None:
        # Fallback to old regex-based method
        simple_entities = extract_simple_entities(text)
        return {
            'persons': [],
            'organizations': [],
            'locations': [],
            'all_entities': simple_entities
        }

    # Process text with spaCy
    doc = nlp(text)

    persons = []
    organizations = []
    locations = []

    for ent in doc.ents:
        entity_text = ent.text.strip()

        # Skip very short entities (likely errors)
        if len(entity_text) <= 2:
            continue

        if ent.label_ == "PERSON":
            persons.append(entity_text)
        elif ent.label_ == "ORG":
            organizations.append(entity_text)
        elif ent.label_ in ("GPE", "LOC"):  # GPE = Geo-Political Entity, LOC = Location
            locations.append(entity_text)

    # Deduplicate while preserving order
    persons = list(dict.fromkeys(persons))[:15]
    organizations = list(dict.fromkeys(organizations))[:15]
    locations = list(dict.fromkeys(locations))[:15]

    # Combine all entities for backward compatibility
    all_entities = persons + organizations + locations

    return {
        'persons': persons,
        'organizations': organizations,
        'locations': locations,
        'all_entities': all_entities
    }


def preprocess_articles(tool_context: ToolContext) -> Dict:
    """
    Clean and preprocess collected articles.

    - Removes HTML tags and extra whitespace
    - Extracts basic entities (simplified for MVP)
    - Creates claim list from article text
    - Normalizes text for analysis

    Args:
        tool_context: ADK tool context with collected articles in state

    Returns:
        Dictionary with preprocessed articles and extraction statistics
    """
    # Get collected articles from state
    articles = tool_context.state.get('collected_articles', [])

    if not articles:
        return {
            'success': False,
            'error': 'No articles found in state. Run collectors first.',
            'processed_count': 0
        }

    processed_articles = []
    total_entities = 0
    total_claims = 0

    for article in articles:
        # Skip if article is not a dictionary
        if not isinstance(article, dict):
            continue

        # Clean text
        text = article.get('text', article.get('description', ''))

        # Remove extra whitespace
        clean_text = re.sub(r'\s+', ' ', text).strip()

        # Extract entities with spaCy NER (categorized by type)
        entity_data = extract_entities_with_spacy(clean_text)
        total_entities += len(entity_data['all_entities'])

        # Extract key claims (sentences with strong verbs indicating assertions)
        claims = extract_claims(clean_text)
        total_claims += len(claims)

        # Add preprocessing results to article
        processed_article = article.copy()
        processed_article['clean_text'] = clean_text
        processed_article['entities'] = entity_data['all_entities']  # Flat list for backward compat
        processed_article['persons'] = entity_data['persons']
        processed_article['organizations'] = entity_data['organizations']
        processed_article['locations'] = entity_data['locations']
        processed_article['claims'] = claims
        processed_article['word_count'] = len(clean_text.split())

        processed_articles.append(processed_article)

    # Check if any articles were successfully processed
    if not processed_articles:
        return {
            'success': False,
            'error': 'No valid articles found to preprocess. All articles were invalid or skipped.',
            'processed_count': 0
        }

    # Update state with processed articles
    tool_context.state['preprocessed_articles'] = processed_articles

    # Calculate entity category statistics
    total_persons = sum(len(a.get('persons', [])) for a in processed_articles)
    total_orgs = sum(len(a.get('organizations', [])) for a in processed_articles)
    total_locations = sum(len(a.get('locations', [])) for a in processed_articles)

    tool_context.state['preprocessing_stats'] = {
        'total_articles': len(processed_articles),
        'total_entities': total_entities,
        'total_persons': total_persons,
        'total_organizations': total_orgs,
        'total_locations': total_locations,
        'total_claims': total_claims,
        'avg_word_count': sum(a['word_count'] for a in processed_articles) / len(processed_articles)
    }

    # Collect sample entities from first 2 articles for reporting
    sample_persons = list(set([e for a in processed_articles[:2] for e in a.get('persons', [])]))[:5]
    sample_orgs = list(set([e for a in processed_articles[:2] for e in a.get('organizations', [])]))[:5]
    sample_locations = list(set([e for a in processed_articles[:2] for e in a.get('locations', [])]))[:5]

    return {
        'success': True,
        'processed_count': len(processed_articles),
        'total_entities': total_entities,
        'total_persons': total_persons,
        'total_organizations': total_orgs,
        'total_locations': total_locations,
        'total_claims': total_claims,
        'sample_persons': sample_persons,
        'sample_organizations': sample_orgs,
        'sample_locations': sample_locations,
        'using_spacy': SPACY_AVAILABLE
    }


def extract_simple_entities(text: str) -> List[str]:
    """
    Extract simple entities from text (names, organizations).
    Simplified approach for MVP - uses pattern matching.

    Args:
        text: Clean article text

    Returns:
        List of entity strings
    """
    entities = []

    # Pattern for capitalized words (potential names)
    # Matches sequences of 2-3 capitalized words
    name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b'
    names = re.findall(name_pattern, text)
    entities.extend(names)

    # Pattern for organizations (words ending in Inc., Corp., LLC, etc.)
    org_pattern = r'\b([A-Z][A-Za-z\s&]+(?:Inc\.|Corp\.|LLC|Co\.|Ltd\.|Organization|Agency|Department|Committee))'
    orgs = re.findall(org_pattern, text)
    entities.extend(orgs)

    # Remove duplicates while preserving order
    seen = set()
    unique_entities = []
    for entity in entities:
        entity_lower = entity.lower()
        if entity_lower not in seen and len(entity) > 3:  # Filter short matches
            seen.add(entity_lower)
            unique_entities.append(entity)

    return unique_entities[:20]  # Limit to top 20 entities


def extract_claims(text: str) -> List[str]:
    """
    Extract key claims from article text.
    Simplified approach: splits into sentences and identifies assertive statements.

    Args:
        text: Clean article text

    Returns:
        List of claim strings
    """
    # Split into sentences (simple approach)
    sentences = re.split(r'[.!?]+', text)

    claims = []

    # Keywords indicating claims/assertions
    claim_verbs = [
        'said', 'says', 'stated', 'announced', 'reported', 'confirmed',
        'revealed', 'claimed', 'argued', 'warned', 'predicted', 'declared'
    ]

    for sentence in sentences:
        sentence = sentence.strip()

        # Skip short sentences
        if len(sentence.split()) < 5:
            continue

        # Check if sentence contains claim verbs
        sentence_lower = sentence.lower()
        if any(verb in sentence_lower for verb in claim_verbs):
            claims.append(sentence)

        # Limit to top 5 claims per article
        if len(claims) >= 5:
            break

    return claims
