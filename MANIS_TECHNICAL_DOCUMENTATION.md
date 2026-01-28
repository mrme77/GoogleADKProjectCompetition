# MANIS Technical Documentation
## Multi-Agent News Intelligence System

**Version:** 1.0
**Last Updated:** January 27, 2026

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Pipeline Stages](#pipeline-stages)
4. [Technology Stack](#technology-stack)
5. [Data Flow](#data-flow)
6. [Configuration](#configuration)

---

## System Overview

MANIS (Multi-Agent News Intelligence System) is an automated news aggregation and analysis pipeline that:

- **Collects** news articles from Google News RSS feeds
- **Analyzes** content for sentiment, bias, and credibility
- **Generates** comprehensive HTML-formatted daily digests
- **Delivers** reports via email (Gmail)

### Core Purpose

MANIS helps users understand **media framing** and **perspective differences** across news sources by:

- Tracking sentiment distribution across topics
- Detecting political bias indicators in language
- Scoring source credibility based on journalistic standards
- Highlighting how different outlets frame the same stories

---

## Architecture

### Multi-Agent Sequential Pipeline

MANIS uses **Google ADK (Agent Development Kit)** with a sequential agent architecture where each specialized agent performs one stage of the pipeline:

```
Root Agent (Orchestrator)
    ├── Stage 1: Google News Collector
    ├── Stage 2: Preprocessor
    ├── Stage 3: Fact Checker
    ├── Stage 4: NLP Analyst
    ├── Stage 5: Summarizer
    └── Stage 6: Email Delivery
```

### Agent Communication

- **State Management**: Agents share data through `tool_context.state` (key-value store)
- **Sequential Execution**: Each agent waits for the previous stage to complete
- **Data Enrichment**: Each agent adds metadata to articles as they flow through the pipeline

### LLM Provider

All agents use: `openrouter/google/gemini-2.5-flash-lite-preview-09-2025`

---

## Pipeline Stages

### Stage 1: Google News Collector

**Agent**: `google_news_collector`
**File**: `manis_agent/agents/collectors/google_news_collector/agent.py`

#### Purpose
Fetches recent news articles from Google News RSS feeds across three topic categories.

#### Tools Used
- **Function**: `fetch_google_news_rss()`
- **Libraries**:
  - `feedparser` - Parse RSS/Atom feeds
  - `requests` - HTTP requests for URL resolution
  - `BeautifulSoup` - HTML parsing for description cleanup

#### What It Does

1. **Fetches RSS Feeds** for three topics:
   - **Politics** (4 articles): US politics, elections, Congress, Senate, White House
   - **Technology** (3 articles): Tech, AI, cybersecurity, software (filters out sports)
   - **Europe** (4 articles): European Union, Ukraine war, Russia-Ukraine, NATO, EU

2. **Filters Articles**:
   - Only includes articles from last **48 hours**
   - Excludes sports content from tech category using keyword filtering
   - Total target: **11 articles**

3. **Resolves Google News URLs**:
   - Google RSS feeds return redirect URLs like `https://news.google.com/rss/articles/CBMi...`
   - `resolve_google_news_url()` follows redirects to get actual article URLs
   - Uses HEAD/GET requests with custom User-Agent

4. **Extracts Metadata**:
   - Title (splits "Article Title - Source Name" format)
   - Original source (e.g., "BBC", "Reuters", "The New York Times")
   - Publication timestamp
   - Clean description (HTML tags removed)
   - Category, region, URL

#### Output Stored in State
```python
state['collected_articles'] = [
    {
        'title': str,
        'url': str,               # Resolved direct URL
        'source': str,            # Original news outlet
        'aggregator': 'Google News',
        'original_source': str,
        'region': 'US' or 'EU/International',
        'category': 'politics' | 'technology' | 'europe',
        'timestamp': str (ISO format),
        'description': str,
        'text': str
    },
    ...
]
```

---

### Stage 2: Preprocessor

**Agent**: `preprocessor`
**File**: `manis_agent/agents/preprocessor/agent.py`

#### Purpose
Cleans article text and extracts entities and claims for downstream analysis.

#### Tools Used
- **Function**: `preprocess_articles()`
- **Libraries**:
  - `spacy` - Named Entity Recognition (NER) with machine learning
  - `re` - Regular expressions for pattern matching

#### What It Does

1. **Text Cleaning**:
   - Removes extra whitespace: `re.sub(r'\s+', ' ', text)`
   - Normalizes formatting

2. **Entity Extraction** (`extract_entities_with_spacy()`):
   - **Uses spaCy NER** (model: `en_core_web_sm`) for accurate entity extraction
   - **Automatic Categorization by Type**:
     - **PERSON**: People's names (e.g., "Joe Biden", "Tim Cook")
     - **ORG**: Organizations, companies, agencies (e.g., "Apple", "White House", "NATO")
     - **GPE/LOC**: Locations, countries, cities (e.g., "Ukraine", "California", "Washington D.C.")
   - **Fallback**: If spaCy unavailable, uses regex-based `extract_simple_entities()`:
     - Pattern 1 - Names: Sequences of 2-3 capitalized words
       - Regex: `r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})\b'`
     - Pattern 2 - Organizations: Words ending in Corp., Inc., LLC, Agency, Department
       - Regex: `r'\b([A-Z][A-Za-z\s&]+(?:Inc\.|Corp\.|LLC|Co\.|Ltd\.|Organization|Agency|Department|Committee))'`
   - Deduplicates and returns up to 15 entities per category (persons, organizations, locations)
   - **Benefits over regex**:
     - Much higher accuracy (trained NER model)
     - Handles complex names (e.g., "President Joe Biden" as one entity)
     - Automatic type classification
     - Robust to variations in formatting

3. **Claim Extraction** (`extract_claims()`):
   - Splits text into sentences using: `re.split(r'[.!?]+', text)`
   - Identifies assertive statements using claim verbs:
     - `'said', 'says', 'stated', 'announced', 'reported', 'confirmed', 'revealed', 'claimed', 'argued', 'warned', 'predicted', 'declared'`
   - Returns up to 5 claims per article

4. **Word Count**:
   - Calculates: `len(clean_text.split())`

#### Output Stored in State
```python
state['preprocessed_articles'] = [
    {
        ...previous_fields,
        'clean_text': str,
        'entities': [str, ...],           # Flat list (backward compat)
        'persons': [str, ...],            # Up to 15 person entities
        'organizations': [str, ...],      # Up to 15 organization entities
        'locations': [str, ...],          # Up to 15 location entities
        'claims': [str, ...],             # Up to 5 claims
        'word_count': int
    },
    ...
]

state['preprocessing_stats'] = {
    'total_articles': int,
    'total_entities': int,
    'total_persons': int,
    'total_organizations': int,
    'total_locations': int,
    'total_claims': int,
    'avg_word_count': float
}
```

---

### Stage 3: Fact Checker

**Agent**: `fact_checker`
**File**: `manis_agent/agents/fact_checker/agent.py`

#### Purpose
Scores article credibility based on source reputation and flags dubious claims.

#### Tools Used
- **Function 1**: `score_article_credibility()`
- **Function 2**: `flag_dubious_claims()`
- **Libraries**: None (uses pre-defined database)

#### What It Does

##### Credibility Scoring

Uses a **hardcoded source credibility database** (`SOURCE_CREDIBILITY`) with ratings for major outlets:

| Source | Credibility Score | Political Bias | Bias Score (1-10) | Notes |
|--------|------------------|----------------|-------------------|-------|
| Reuters | 90 | center | 1 | Very high fact accuracy |
| Associated Press (AP) | 90 | center | 1 | Very high fact accuracy |
| BBC | 88 | center | 2 | International public broadcaster |
| NPR | 85 | center-left | 3 | Strong fact-checking standards |
| Wall Street Journal | 82 | center-right | 3 | Business-focused, strong reporting |
| Financial Times | 80 | center | 2 | Strong economic analysis |
| NY Times | 78 | center-left | 4 | Thorough reporting, editorial lean |
| Washington Post | 76 | center-left | 4 | Strong investigative journalism |
| Politico | 75 | center | 3 | Policy-focused |
| The White House (.gov) | 75 | government | 5 | Official, reflects admin |
| Guardian | 74 | left | 5 | Progressive editorial stance |
| CNN | 72 | center-left | 4 | Generally factual |
| Independent | 70 | center-left | 4 | British, center-left |
| **Unknown** | 60 | unknown | 5 | Default for unlisted sources |

**Credibility Tiers**:
- **High**: Score ≥ 80
- **Medium**: Score 60-79
- **Low**: Score < 60

##### Claim Flagging

Flags claims needing verification based on:

1. **Verification Keywords**:
   - `'reportedly', 'allegedly', 'claims', 'unconfirmed', 'sources say', 'anonymous', 'rumored', 'speculation'`

2. **High-Bias Sources**:
   - Articles with bias_score ≥ 7

Each flagged claim includes:
- The claim text
- Source outlet
- Article title
- Reason (verification keyword or high bias)
- Credibility score

#### Output Stored in State
```python
state['fact_checked_articles'] = [
    {
        ...previous_fields,
        'credibility_score': int (0-100),
        'bias_score': int (1-10),
        'fact_accuracy_rating': str ('very high', 'high', etc.),
        'credibility_notes': str
    },
    ...
]

state['credibility_stats'] = {
    'high_credibility': int,     # Count with score ≥ 80
    'medium_credibility': int,   # Count with score 60-79
    'low_credibility': int,      # Count with score < 60
    'high_bias': int,            # Count with bias_score ≥ 7
    'low_bias': int              # Count with bias_score < 4
}

state['flagged_claims'] = [
    {
        'claim': str,
        'source': str,
        'article_title': str,
        'reason': 'verification_keyword' | 'high_bias_source',
        'credibility_score': int
    },
    ...
]
```

---

### Stage 4: NLP Analyst

**Agent**: `nlp_analyst`
**File**: `manis_agent/agents/nlp_analyst/agent.py`

#### Purpose
Analyzes sentiment, detects political bias patterns, and extracts keywords.

#### Tools Used
- **Function 1**: `analyze_sentiment()`
- **Function 2**: `detect_political_bias()`
- **Function 3**: `extract_keywords()`
- **Libraries**:
  - `textblob` - Sentiment analysis
  - `collections.Counter` - Word frequency counting

#### What It Does

##### 1. Sentiment Analysis

Uses **TextBlob** to analyze article sentiment:

```python
blob = TextBlob(text)
polarity = blob.sentiment.polarity        # -1 (negative) to +1 (positive)
subjectivity = blob.sentiment.subjectivity # 0 (objective) to 1 (subjective)
```

**Classification**:
- **Positive**: polarity > 0.1
- **Negative**: polarity < -0.1
- **Neutral**: -0.1 ≤ polarity ≤ 0.1

Calculates:
- Sentiment distribution (positive/negative/neutral counts)
- Average polarity across all articles
- Average subjectivity across all articles

##### 2. Political Bias Detection

Uses **keyword frequency analysis** to detect bias indicators:

**Left-leaning keywords** (10 terms):
- `'progressive', 'reform', 'equality', 'climate', 'healthcare', 'workers', 'regulation', 'discrimination', 'rights', 'justice'`

**Right-leaning keywords** (10 terms):
- `'conservative', 'traditional', 'freedom', 'security', 'border', 'tax', 'deregulation', 'law and order', 'values', 'patriot'`

**Emotional language indicators** (11 terms):
- `'crisis', 'disaster', 'threat', 'dangerous', 'attack', 'destroy', 'scandal', 'corrupt', 'failing', 'radical', 'extreme'`

**Per-Article Analysis**:
- Counts occurrences of each keyword set
- Assigns bias_direction: `'left-leaning'`, `'right-leaning'`, or `'neutral'`

**Per-Source Aggregation**:
- Groups articles by source
- Sums bias signals across all articles from each source
- Calculates averages per article for each source

##### 3. Keyword Extraction

Extracts top keywords across entire article corpus:

1. **Tokenization**: Extract words with 4+ letters using `re.findall(r'\b[a-z]{4,}\b', text)`
2. **Stopword Filtering**: Remove common words:
   - `'that', 'this', 'with', 'from', 'have', 'been', 'their', 'said', 'will', 'were', 'what', 'would', 'there', 'about', 'which', 'when', 'they', 'more', 'than', 'other', 'some', 'into', 'could', 'only'`
3. **Frequency Count**: `Counter(filtered_words).most_common(20)`

Returns top 20 keywords with counts.

#### Output Stored in State
```python
state['nlp_analyzed_articles'] = [
    {
        ...previous_fields,
        'sentiment_polarity': float (-1 to 1),
        'sentiment_subjectivity': float (0 to 1),
        'sentiment_category': 'positive' | 'negative' | 'neutral'
    },
    ...
]

state['sentiment_stats'] = {
    'positive': int,         # Article count
    'negative': int,
    'neutral': int,
    'avg_polarity': float,
    'avg_subjectivity': float
}

state['bias_analyzed_articles'] = [
    {
        ...previous_fields,
        'bias_direction': 'left-leaning' | 'right-leaning' | 'neutral',
        'left_keyword_count': int,
        'right_keyword_count': int,
        'emotional_language_count': int
    },
    ...
]

state['bias_analysis'] = {
    'source_key': {
        'display_name': str,
        'articles': int,
        'left_signals': int,
        'right_signals': int,
        'emotional_language': int,
        'avg_left_signals': float,
        'avg_right_signals': float,
        'avg_emotional': float
    },
    ...
}

state['top_keywords'] = [
    ('word', count),
    ...
]  # Top 20 keywords
```

---

### Stage 5: Summarizer

**Agent**: `summarizer`
**File**: `manis_agent/agents/summarizer/agent.py`

#### Purpose
Generates a comprehensive HTML-formatted daily news digest from analyzed data.

#### Tools Used
- **Function**: `get_analysis_results()`
- **Libraries**:
  - `datetime` - Current date for digest header

#### What It Does

##### Data Retrieval

Calls `get_analysis_results()` which:
1. Retrieves all analyzed articles from state (tries multiple keys in fallback order)
2. Counts articles by aggregator (Google News)
3. Extracts unique original sources for diversity metrics
4. Gets current date in YYYY-MM-DD format

Returns comprehensive data package:
```python
{
    'success': True,
    'current_date': str,
    'total_articles': int,
    'google_news_count': int,
    'original_sources': [str, ...],
    'source_diversity': int,
    'articles': [dict, ...],
    'sentiment_stats': dict,
    'bias_analysis': dict,
    'top_keywords': [(word, count), ...],
    'credibility_stats': dict,
    'flagged_claims': [dict, ...]
}
```

##### HTML Digest Generation

The LLM generates a **dark-themed HTML email** with inline CSS (for email compatibility):

**Section 1: Executive Summary**
- Overview of news landscape
- Total articles analyzed
- Time period covered
- Key themes
- Coverage areas

**Section 2: Articles by Topic**
- Groups articles by category (politics, technology, europe)
- Creates article cards with:
  - Title and source
  - 2-3 sentence summary
  - Sentiment label and polarity score
  - Credibility score
  - Key entities
  - Link to article

**Section 3: Credibility Assessment**
- Distribution (high/medium/low credibility counts)
- Average credibility score
- Flagged claims needing verification
- Brief interpretation

**Section 4: Coverage Analysis & Media Framing**
- **Sentiment Distribution by Topic**: Percentage breakdown (positive/negative/neutral) for each category
- **Source Perspective Differences**: How different outlets frame the same stories (compares bias_label and sentiment)
- **Most Covered Topics**: Count of articles by theme (uses category field, must add up to total)

**Section 5: Bottom Line**
- Key takeaways
- Notable perspective differences between sources
- Recommendations for further reading

**Design Specifications**:
- Dark background (#1e1e1e)
- Light text (#f0f0f0)
- Blue headers (#4a9eff)
- Dark grey cards (#2d2d2d)
- All styles inline for email client compatibility

#### Output Stored in State
```python
state['daily_digest'] = str  # Complete HTML document
```

---

### Stage 6: Email Delivery

**Agent**: `email_delivery`
**File**: `manis_agent/agents/delivery/agent.py`

#### Purpose
Delivers the daily digest via Gmail SMTP or Gmail API.

#### Tools Used
- **Function 1**: `send_email_digest()`
- **Function 2**: `test_email_connection()` (optional)
- **Libraries**:
  - `smtplib` - SMTP email sending (primary method)
  - `email.mime` - Email message construction
  - `google-auth`, `google-api-python-client` - Gmail API (fallback method)

#### What It Does

##### HTML Extraction & Sanitization

Before sending, cleans the digest HTML:

1. **Remove markdown fences**: Strips ````html` code blocks if LLM included them
2. **Extract HTML envelope**: Finds `<!DOCTYPE html>` to `</html>` to remove conversational text
3. **Cleanup stray markers**: Removes leading `#` or `*` characters

##### Email Sending Methods

**Method 1: SMTP (Preferred)**
- Requires environment variables:
  - `GMAIL_ADDRESS`: Sender Gmail address
  - `GMAIL_APP_PASSWORD`: Gmail app password (not regular password)
- Connects to `smtp.gmail.com:587` with TLS
- Sends HTML email with UTF-8 encoding

**Method 2: Gmail API (Fallback)**
- Uses OAuth 2.0 authentication
- Requires `credentials.json` file
- Generates/refreshes `token.json`
- Encodes message as base64 and sends via API

##### Recipient Management

- Reads from `RECIPIENT_EMAIL` environment variable
- Supports **multiple recipients** (comma-separated): `email1@example.com, email2@example.com`

##### Email Format

```
From: GMAIL_ADDRESS
To: RECIPIENT_EMAIL(S)
Subject: Daily News Intelligence Report - YYYY-MM-DD
Content-Type: text/html; charset=utf-8
Body: [HTML digest]
```

#### Output Stored in State
```python
state['delivery_status'] = {
    'success': bool,
    'method': 'smtp' | 'gmail_api',
    'recipients': [str, ...],
    'timestamp': str,
    'error': str (if failed)
}
```

---

## Technology Stack

### Core Framework
- **Google ADK (Agent Development Kit)** - Multi-agent orchestration
  - `SequentialAgent` - Pipeline orchestration
  - `Agent` - Individual agent creation
  - `ToolContext` - State management

### LLM Provider
- **OpenRouter** - LLM routing service
  - Model: `google/gemini-2.5-flash-lite-preview-09-2025`
  - Used by all 6 agents for decision-making

### Python Libraries

#### Data Collection
- `feedparser` - RSS/Atom feed parsing
- `requests` - HTTP requests for URL resolution
- `beautifulsoup4` - HTML parsing and cleanup

#### NLP & Analysis
- `textblob` - Sentiment analysis (polarity, subjectivity)
- `re` (standard library) - Regular expressions for pattern matching

#### Email Delivery
- `smtplib` (standard library) - SMTP email sending
- `email.mime` (standard library) - Email message construction
- `google-auth` - OAuth 2.0 authentication
- `google-auth-oauthlib` - OAuth flow
- `google-api-python-client` - Gmail API client

#### Utilities
- `collections.Counter` - Word frequency counting
- `datetime` - Date/time handling
- `json` - JSON serialization
- `os` - Environment variable access
- `base64` - Email encoding

---

## Data Flow

### State Keys Through Pipeline

| Stage | Input Keys | Output Keys | Enrichment |
|-------|-----------|-------------|------------|
| **Collector** | None | `collected_articles` | Title, URL, source, category, timestamp, description |
| **Preprocessor** | `collected_articles` | `preprocessed_articles`, `preprocessing_stats` | clean_text, entities, claims, word_count |
| **Fact Checker** | `preprocessed_articles` | `fact_checked_articles`, `credibility_stats`, `flagged_claims` | credibility_score, bias_score, fact_accuracy_rating |
| **NLP Analyst** | `fact_checked_articles` | `nlp_analyzed_articles`, `sentiment_stats`, `bias_analyzed_articles`, `bias_analysis`, `top_keywords` | sentiment_polarity, sentiment_category, bias_direction, keyword_counts |
| **Summarizer** | `bias_analyzed_articles`, all stats | `daily_digest` | HTML report |
| **Delivery** | `daily_digest` | `delivery_status` | Email confirmation |

### Article Metadata Evolution

**After Collector**:
```python
{
    'title': str,
    'url': str,
    'source': str,
    'category': str,
    'timestamp': str,
    'text': str
}
```

**After Preprocessor** (adds):
```python
{
    'clean_text': str,
    'entities': [str, ...],
    'claims': [str, ...],
    'word_count': int
}
```

**After Fact Checker** (adds):
```python
{
    'credibility_score': int,
    'bias_score': int,
    'fact_accuracy_rating': str
}
```

**After NLP Analyst** (adds):
```python
{
    'sentiment_polarity': float,
    'sentiment_category': str,
    'bias_direction': str,
    'left_keyword_count': int,
    'right_keyword_count': int
}
```

---

## Configuration

### Environment Variables

Required:
- `RECIPIENT_EMAIL` - Email recipient(s), comma-separated
- `GMAIL_ADDRESS` - Sender Gmail address
- `GMAIL_APP_PASSWORD` - Gmail app password (not regular password)

Optional:
- `OPENROUTER_API_KEY` - If using OpenRouter (may be set via ADK)

### Gmail Setup

#### Option 1: SMTP with App Password (Recommended)

1. Enable 2-factor authentication on Gmail
2. Generate app password:
   - Go to Google Account → Security
   - Search "App passwords"
   - Create password for "Mail"
3. Set environment variables:
   ```bash
   export GMAIL_ADDRESS="your-email@gmail.com"
   export GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
   export RECIPIENT_EMAIL="recipient@example.com"
   ```

#### Option 2: Gmail API with OAuth

1. Create Google Cloud project
2. Enable Gmail API
3. Download `credentials.json`
4. First run will open browser for OAuth consent
5. `token.json` will be saved for future runs

### Execution

```bash
# Set environment variables
export RECIPIENT_EMAIL="you@example.com"
export GMAIL_ADDRESS="sender@gmail.com"
export GMAIL_APP_PASSWORD="your-app-password"

# Run MANIS pipeline
python -m manis_agent.agent
# Or however the ADK execution works
```

---

## Key Design Decisions

### Why Sequential Architecture?
- Each stage depends on previous stage's output
- Clear data flow and debugging
- Easier to understand and maintain

### Why Source-Based Credibility?
- MVP approach for fast implementation
- Transparent methodology (users can inspect database)
- Future: Can integrate external fact-check APIs

### Why TextBlob for Sentiment?
- Lightweight, no external API calls
- Good enough accuracy for news articles
- Fast execution

### Why Keyword-Based Bias Detection?
- Interpretable results
- No training data required
- Captures explicit framing language
- Future: Can add ML-based models

### Why Email Delivery?
- Universal format (everyone has email)
- HTML rendering support
- Scheduled digest model
- Future: Can add web dashboard

---

## Limitations & Future Improvements

### Current Limitations

1. **Bias Detection**: Keyword-based, doesn't capture subtle framing
2. **Credibility Database**: Manual curation, limited to ~15 sources
3. **No Article Text**: Uses descriptions only (full text scraping not implemented)
4. **English Only**: No multi-language support
5. **Entity Context**: Entities extracted but not disambiguated (e.g., "Apple" company vs. fruit)

### Potential Enhancements

1. ~~**Better Entity Extraction**~~ ✅ **IMPLEMENTED**:
   - ~~Use spaCy NER (Named Entity Recognition)~~ ✅ Done
   - ~~Categorize entities by type (Person/Org/Location)~~ ✅ Done

2. **Advanced Bias Detection**:
   - Train ML model on labeled data
   - Analyze sentence-level framing
   - Compare headline vs. article content

3. **Dynamic Credibility**:
   - Integrate Media Bias/Fact Check API
   - Use Wikipedia/Wikidata for source info
   - Track accuracy over time

4. **Full Article Analysis**:
   - Scrape full article text with newspaper3k
   - Compare intro vs. conclusion framing
   - Analyze quote attribution patterns

5. **Interactive Dashboard**:
   - Web UI for browsing reports
   - Historical trend analysis
   - User customization (topics, sources)

6. **Multi-Language Support**:
   - Translate non-English articles
   - Analyze international news in native language

---

## Troubleshooting

### Common Issues

**No articles collected**:
- Check if RSS feeds are accessible
- Verify 48-hour cutoff isn't too restrictive
- Look at debug output for filtering reasons

**Entity extraction returns article titles**:
- Regex patterns matching title format instead of content
- Check `clean_text` field is properly populated

**Email not sending**:
- Verify `GMAIL_APP_PASSWORD` is app password, not regular password
- Check 2FA is enabled on Gmail
- Confirm `RECIPIENT_EMAIL` is set
- Try `test_email_connection()` tool first

**HTML formatting broken in email**:
- Some email clients don't support all CSS
- Ensure all styles are inline (not in `<style>` tags)
- Test with multiple email clients

**Sentiment seems wrong**:
- TextBlob is tuned for general text, news may differ
- Very short descriptions may not have enough signal
- Consider full article text for better accuracy

---

## Conclusion

MANIS demonstrates how a multi-agent pipeline can automate complex information processing tasks:

1. **Data Collection** - Aggregate from multiple sources
2. **Preprocessing** - Extract structured information
3. **Analysis** - Apply NLP and credibility assessment
4. **Synthesis** - Generate human-readable reports
5. **Delivery** - Distribute to end users

The sequential architecture makes the system **transparent**, **debuggable**, and **extensible** for future enhancements.
