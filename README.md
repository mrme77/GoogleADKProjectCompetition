# MANIS - Multi-Agent News Intelligence System

<div align="center">

**Automated multi-agent pipeline for intelligent news analysis and bias detection**

[![Google ADK](https://img.shields.io/badge/Google%20ADK-0.3.0-4285F4?logo=google)](https://developers.google.com/adk)
[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

*Built for the Google ADK Project Competition 2025*

[Features](#features) • [Quick Start](#quick-start) • [Architecture](#architecture) • [Documentation](#documentation)

</div>

---

## Overview

MANIS is a fully autonomous **6-stage multi-agent pipeline** that collects news from multiple sources via Google News, analyzes sentiment and political bias, scores credibility, and delivers intelligent email digests to your inbox 3 times daily—completely hands-free.

### The Problem

In today's information landscape:
- **Millions of articles** published daily across numerous sources
- **Bias blindness**: Readers unaware of how sources frame stories differently
- **Time constraints**: Reading multiple outlets for balanced perspective takes hours
- **Credibility uncertainty**: Distinguishing quality journalism from clickbait is difficult

### The Solution

MANIS automates what humans don't have time for:
- Aggregates news from diverse sources (left, center, right)
- Detects sentiment and political bias in framing
- Scores source credibility (0-100 scale)
- Compares how different outlets cover the same topics
- Delivers professional HTML digests 3x daily

**Example Output**: "Ukraine story covered by 5 sources - Central News (neutral, 85 credibility), National Tribune (negative tone, right-leaning, 72 credibility), Global Wire (neutral, 90 credibility)..."

---

## Features

### Automated Intelligence

- ✅ **Multi-Source Collection**: Google News RSS aggregates from multiple credible outlets
- ✅ **Sentiment Analysis**: Positive/negative/neutral tone detection (TextBlob)
- ✅ **Bias Detection**: Identifies left/center/right framing patterns
- ✅ **Credibility Scoring**: 0-100 reliability scores for 15+ major news sources
- ✅ **Entity Extraction**: People, organizations, locations (spaCy NER)
- ✅ **Comparative Analysis**: Shows how different sources frame the same stories

### Delivery & Automation

- ✅ **Professional HTML Emails**: 6-section digest with all insights
- ✅ **Automated Scheduling**: Runs 3x daily (7:30 AM, 12:30 PM, 4:30 PM) via cron
- ✅ **Gmail Integration**: SMTP delivery with app password authentication
- ✅ **Comprehensive Logging**: Timestamped logs for debugging

### Google ADK Showcase

- ✅ **Sequential Agent Pipeline**: 6-stage data enrichment workflow
- ✅ **Multi-Model Strategy**: Optimized Gemini model selection (flash-lite, flash, 2.5-flash)
- ✅ **Custom Tools**: 8 domain-specific tools (RSS, NLP, email)
- ✅ **State Management**: Inter-agent communication via `tool_context.state`
- ✅ **Production Ready**: Robust error handling, session persistence

---

## Architecture

### 6-Stage Sequential Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                   MANIS Root Agent (SequentialAgent)            │
│                                                                 │
│  [1. Collector] ──> Fetches from Google News RSS (11 articles)  │
│        │                                                        │
│        ▼                                                        │
│  [2. Preprocessor] ──> Cleans text, extracts entities (spaCy)   │
│        │                                                        │
│        ▼                                                        │
│  [3. Fact Checker] ──> Scores credibility, detects bias         │
│        │                                                        │
│        ▼                                                        │
│  [4. NLP Analyst] ──> Sentiment analysis (TextBlob), keywords   │
│        │                                                        │
│        ▼                                                        │
│  [5. Summarizer] ──> Generates HTML digest (6 sections)         │
│        │                                                        │
│        ▼                                                        │
│  [6. Email Delivery] ──> Sends via Gmail SMTP                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                       tool_context.state
                    (Shared state dictionary)
```

**Visual Architecture Diagrams:**

<div align="center">

![Agent Pipeline](<manis_agent/pictures/Screenshot 2025-11-15 at 6.23.40 PM.png>)
*6-Stage Sequential Agent Pipeline*

![Agent-Tool Relationships](<manis_agent/pictures/Screenshot 2025-11-15 at 6.23.52 PM.png>)
*Detailed Agent-Tool Relationships*

</div>

### Agent Details

| Agent | Model | Tools | Purpose |
|-------|-------|-------|---------|
| **Collector** | gemini-2.0-flash-lite | `fetch_google_news_rss` | Fetch RSS feeds from 3 topics |
| **Preprocessor** | gemini-2.0-flash-lite | `preprocess_articles` | Clean text, extract entities (spaCy) |
| **Fact Checker** | gemini-2.0-flash | `score_credibility`, `flag_claims` | Score source reliability |
| **NLP Analyst** | gemini-2.5-flash | `analyze_sentiment`, `detect_bias`, `extract_keywords` | Sentiment & bias analysis |
| **Summarizer** | gemini-2.5-flash | `get_analysis_results` | Generate HTML digest |
| **Email Delivery** | gemini-2.0-flash-lite | `send_email_digest` | Send via Gmail SMTP |

### Data Flow

Each agent enriches the data:

```
Raw RSS → [+metadata] → [+entities, claims] → [+credibility scores]
       → [+sentiment, bias] → [+HTML digest] → [Email sent]

State keys: collected_articles → preprocessed_articles → fact_checked_articles
         → nlp_analyzed_articles → daily_digest → email_sent
```

---

## Quick Start

### Prerequisites

- **macOS** (tested on macOS 14+) or Linux
- **Python 3.8+** (recommended: 3.12 or 3.13)
- **Gmail account** for receiving digests
- **[Google API Key](https://aistudio.google.com/app/apikey)** (free tier)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/manis.git
cd manis

# 2. Create virtual environment
python3 -m venv adk-env
source adk-env/bin/activate  # On Windows: adk-env\Scripts\activate

# 3. Install dependencies
pip install google-adk[database]==0.3.0
pip install -r requirements.txt

# 4. Download NLP models
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('brown'); nltk.download('punkt')"

# 5. Configure environment
cp manis_agent/.env.example manis_agent/.env
# Edit manis_agent/.env with your credentials (see Configuration below)

# 6. Test run
./run_manis.sh
```

**Expected**: Pipeline runs for ~2-3 minutes, email arrives at your inbox!

---

## Configuration

### Step 1: Get Google API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with Google account
3. Click **"Create API Key"**
4. Copy the key (starts with `AIza...`)

### Step 2: Setup Gmail App Password

**Important**: You need a Gmail **App Password**, not your regular password.

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** (required)
3. Search for **"App passwords"**
4. Select: **App: Mail**, **Device: Other (Custom name)** → "MANIS"
5. Click **Generate**
6. Copy the 16-character password (e.g., `ciao come stai pass`)

### Step 3: Configure .env File

Edit `manis_agent/.env`:

```bash
# Google ADK Configuration
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # ← Your API key

# MANIS Configuration
RECIPIENT_EMAIL=your_email@gmail.com  # ← Where to receive digests
MANIS_RUN_MODE=daily

# Gmail SMTP (REQUIRED for email delivery)
GMAIL_ADDRESS=your_gmail@gmail.com       # ← Your Gmail address
GMAIL_APP_PASSWORD="ciao come stai pass"  # ← App password (keep quotes!)
```

**Verify configuration**:

```bash
source manis_agent/.env
echo $GOOGLE_API_KEY  # Should show your key
echo $RECIPIENT_EMAIL  # Should show your email
```

---

## Running Tests

MANIS includes unit tests for critical tools to ensure reliability.

### Install Test Dependencies

```bash
pip install pytest pytest-mock pytest-asyncio
```

### Run Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_google_news_tools.py -v

# Run with coverage report
pytest tests/unit/ --cov=manis_agent --cov-report=term-missing
```

### Expected Output

```
tests/unit/test_google_news_tools.py::TestFetchGoogleNewsRSS::test_fetch_google_news_success PASSED
tests/unit/test_google_news_tools.py::TestFetchGoogleNewsRSS::test_fetch_google_news_invalid_topic PASSED
tests/unit/test_credibility_scoring.py::TestScoreArticleCredibility::test_score_known_source_reuters PASSED
tests/unit/test_credibility_scoring.py::TestScoreArticleCredibility::test_score_unknown_source_defaults PASSED
tests/unit/test_email_delivery.py::TestSendEmailDigest::test_send_email_success_via_smtp PASSED

============ 15+ tests passed in 3.2s ============
```

**Test Coverage:**
- ✅ **Google News Collector** - RSS fetching, state management, error handling
- ✅ **Credibility Scoring** - Source scoring, stats calculation, unknown sources
- ✅ **Email Delivery** - SMTP sending, error handling, state updates

All tests use mocks—no real API calls, internet access, or credentials required.

---

## Usage

### Manual Run

Run the pipeline manually to test:

```bash
# Option 1: Shell script (recommended)
./run_manis.sh

# Option 2: Direct ADK command
adk run manis_agent --input "Run full pipeline"

# Option 3: Interactive web UI
adk web
# Open browser at http://localhost:8000
# Type: "Run daily news collection and analysis"
```

**Check results**:
1. Look for email in your inbox (RECIPIENT_EMAIL)
2. Check logs: `tail -f logs/manis_*.log`

### Automated Scheduling (3x Daily)

#### Install Cron Jobs

```bash
./setup_cron.sh
```

**What this does**:
- Backs up existing crontab
- Installs 3 cron jobs (7:30 AM, 12:30 PM, 4:30 PM)
- Creates `logs/` directory
- Logs all output to `logs/cron.log`

**Verify installation**:

```bash
crontab -l
```

You should see:

```
# MANIS - Multi-Agent News Intelligence System
# Runs at 7:30 AM, 12:30 PM, and 4:30 PM daily

30 7 * * * cd '/path/to/project' && '/path/to/run_manis.sh' >> '/path/to/logs/cron.log' 2>&1
30 12 * * * cd '/path/to/project' && '/path/to/run_manis.sh' >> '/path/to/logs/cron.log' 2>&1
30 16 * * * cd '/path/to/project' && '/path/to/run_manis.sh' >> '/path/to/logs/cron.log' 2>&1
```

#### macOS Sleep Prevention (Critical!)

**Problem**: Cron jobs won't run if your Mac is asleep.

**Solution 1** - Keep Mac awake (recommended for testing):

```bash
caffeinate -s &
```

This prevents sleep while plugged in. To stop:

```bash
pkill caffeinate
```

**Solution 2** - Prevent sleep permanently:

```bash
# Never sleep when plugged into power
sudo pmset -c sleep 0

# To revert
sudo pmset -c sleep 10
```

**Solution 3** - Clamshell mode (external display):
1. Connect Mac to external monitor
2. Connect to power
3. Close the lid → Mac stays awake

#### Monitor Logs

```bash
# Watch cron logs in real-time
tail -f logs/cron.log

# View recent pipeline logs
ls -lt logs/manis_*.log | head -5

# Check latest run
cat $(ls -t logs/manis_*.log | head -1)
```

#### Modify Schedule

Edit crontab:

```bash
crontab -e
```

**Cron syntax**: `minute hour day month weekday command`

Examples:
- `30 7 * * *` - 7:30 AM daily
- `0 */4 * * *` - Every 4 hours
- `0 9 * * 1-5` - 9:00 AM weekdays only

#### Remove Automation

```bash
# Edit crontab and delete MANIS lines
crontab -e

# Or remove all cron jobs
crontab -r
```

---

## Email Digest Example

Each digest includes **6 comprehensive sections**:

<div align="center">

![Sample Email Digest](<manis_agent/pictures/Screenshot 2025-11-15 at 8.08.41 PM.png>)
*Sample Daily News Digest Output*

</div>

### 1. Executive Summary
- Total articles analyzed per run
- Time period coverage
- Sentiment breakdown (positive/negative/neutral %)
- Bias distribution (left/center/right)

### 2. Top Stories by Category
Organized by topic (Politics, Technology, Europe):
- Article headline with source
- Credibility score (0-100)
- Sentiment indicator
- Key entities mentioned
- Link to full article

### 3. Source Diversity & Perspective Analysis
- List of all sources analyzed
- Sentiment comparison across sources
- How left vs. right outlets frame the same stories
- Examples of contrasting language

### 4. Credibility Assessment
- High/medium/low credibility distribution
- Average credibility score
- Flagged claims requiring verification

### 5. Key Themes & Entities
- Top 10 keywords with frequency
- Most mentioned people, organizations, locations
- Emerging topics

### 6. Bottom Line
- What you need to know (key takeaways)
- Perspective differences to be aware of
- Links for further reading

---

## Troubleshooting

### "adk: command not found"

**Solution**:

```bash
source adk-env/bin/activate
adk --version
```

Scripts use full path `adk-env/bin/adk` automatically.

---

### "No module named 'en_core_web_sm'"

**Solution**:

```bash
python -m spacy download en_core_web_sm

# Verify
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('✓ OK')"
```

---

### "TextBlob corpora not found"

**Solution**:

```bash
python -c "import nltk; nltk.download('brown'); nltk.download('punkt')"
```

---

### "SMTP Authentication Error"

**Causes**:
- Incorrect Gmail app password
- 2-Step Verification not enabled
- Password not quoted in .env

**Solutions**:
1. Verify 2-Step Verification is enabled: [Google Account Security](https://myaccount.google.com/security)
2. Regenerate App Password
3. Ensure quotes in .env: `GMAIL_APP_PASSWORD="ciao come stai pass"`
4. Check no extra spaces: `GMAIL_ADDRESS=user@gmail.com` (no spaces)

---

### "export: not a valid identifier" (in run_manis.sh)

**Cause**: Unquoted values with spaces in .env

**Solution**:

```bash
# Correct
GMAIL_APP_PASSWORD="ciao come stai pass"

# Wrong
GMAIL_APP_PASSWORD=ciao come stai pass
```

---

### Cron job didn't run

**Possible causes**:
1. **Mac was asleep** → Run `caffeinate -s &`
2. **Cron not installed** → Verify: `crontab -l`
3. **Permission issues** → Check: `ls -la run_manis.sh` (should be executable)

**Debugging steps**:

```bash
# 1. Check cron is running (macOS)
sudo launchctl list | grep cron

# 2. Check cron logs
cat logs/cron.log

# 3. Check system logs
log show --predicate 'process == "cron"' --last 1h

# 4. Test manually
./run_manis.sh

# 5. Check permissions
chmod +x run_manis.sh setup_cron.sh
```

**macOS specific**: Give Terminal **Full Disk Access**
1. System Preferences → Security & Privacy → Privacy
2. Full Disk Access → Add Terminal/iTerm

---

### Pipeline runs but no email received

**Check**:
1. **Spam folder** - MANIS emails might be filtered
2. **Logs** - Check for errors: `grep -i error logs/manis_*.log`
3. **State** - Verify digest was created (should see HTML in logs)
4. **Gmail quota** - Check you haven't hit daily send limit

---

## Project Structure

```
manis/
├── manis_agent/                   # Main package
│   ├── agent.py                   # Root SequentialAgent
│   ├── .env                       # Configuration (gitignored)
│   ├── pictures/                  # Architecture diagrams & screenshots
│   └── agents/                    # 6-stage pipeline
│       ├── collectors/
│       │   └── google_news_collector/
│       │       ├── agent.py       # LlmAgent (flash-lite)
│       │       └── tools.py       # fetch_google_news_rss()
│       ├── preprocessor/
│       │   ├── agent.py           # LlmAgent (flash-lite)
│       │   └── tools.py           # preprocess_articles(), spaCy NER
│       ├── fact_checker/
│       │   ├── agent.py           # LlmAgent (flash)
│       │   └── tools.py           # score_credibility(), credibility DB
│       ├── nlp_analyst/
│       │   ├── agent.py           # LlmAgent (2.5-flash)
│       │   └── tools.py           # sentiment, bias, keywords
│       ├── summarizer/
│       │   ├── agent.py           # LlmAgent (2.5-flash)
│       │   └── tools.py           # HTML digest generation
│       └── delivery/
│           ├── agent.py           # LlmAgent (flash-lite)
│           └── tools.py           # Gmail SMTP
│
├── run_manis.sh                   # Pipeline runner script
├── setup_cron.sh                  # Cron installer
├── requirements.txt               # Python dependencies
├── logs/                          # Execution logs (gitignored)
├── tests/                         # Unit tests
│   └── unit/                      # Unit tests for tools
└── README.md                      # This file
```

---

## Performance & Cost

### Current Stats (per run)

- **Runtime**: 2-3 minutes
- **Articles**: 11 articles from 3 topics
- **API Requests**: ~50-100 (Gemini)
- **Cost**: **FREE** (within Gemini free tier: 1,500 requests/day)

### Scaling

- **Daily**: 11 articles × 3 runs = **33 articles/day**
- **Monthly**: ~1,000 articles analyzed
- **Cost**: $0 (well within free tier)

### Optimization

- **Model selection**: flash-lite for simple tasks (cost-optimized), 2.5-flash for complex analysis
- **Parallel collection**: Use ParallelAgent for multiple sources simultaneously
- **Caching**: Source credibility scores cached in-memory

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Framework** | Google ADK 0.3.0 | Agent orchestration |
| **LLM** | Gemini 2.0/2.5 Flash | Natural language processing |
| **NLP** | spaCy 3.8+ | Entity extraction, NER |
| **Sentiment** | TextBlob | Sentiment analysis |
| **RSS** | feedparser 6.0 | News feed parsing |
| **Email** | SMTP/Gmail API | Digest delivery |
| **Automation** | cron (macOS/Linux) | Scheduled execution |
| **Language** | Python 3.8+ | Core implementation |

---

## FAQ

**Q: How much does this cost to run?**
A: **Free!** Google Gemini API has a generous free tier (1,500 requests/day). MANIS uses ~150 requests/day (3 runs × 50 requests).

**Q: Can I change the schedule?**
A: Yes! Edit `setup_cron.sh` before running, or modify crontab directly with `crontab -e`.

**Q: Does this work on Windows/Linux?**
A: Code is cross-platform. For Windows, replace cron with Task Scheduler. For Linux, same cron setup as macOS.

**Q: How do I stop automated runs?**
A: `crontab -e` (delete MANIS lines) or `crontab -r` (remove all jobs).

**Q: What happens if my Mac sleeps during a scheduled run?**
A: The job is skipped (won't run when Mac wakes). Use `caffeinate -s &` to prevent sleep.

**Q: How long does each run take?**
A: 2-3 minutes for the full pipeline (collect → analyze → email).

---

## Contributing

This project was built for the **Google ADK Project Competition 2025**. Contributions welcome after the competition!

### Areas for Contribution

- Additional news sources (international, topic-specific)
- Advanced fact-checking with external APIs (Google Fact Check, PolitiFact)
- Multi-language support
- Slack/Telegram/Discord delivery
- Web dashboard for historical trends
- Topic modeling with Gensim
- ML-based bias classifier

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Google ADK Team** - For the excellent agent framework
- **Kaggle** - For hosting the 5 Days Google AI Agents Intensive course
- **Gemini API** - Powering all LLM intelligence
- **spaCy** - Entity extraction and NER
- **TextBlob** - Sentiment analysis
- **Google News RSS** - Multi-source news aggregation

---

## Support

- **Issues**: Check `logs/` directory for detailed error messages
- **Documentation**: See full docs in [Documentation](#documentation) section
- **Google ADK**: [Official Docs](https://developers.google.com/adk)

---

<div align="center">

**Built with**: Google ADK • Gemini AI • Python • spaCy • TextBlob

**[⭐ Star this repo](https://github.com/yourusername/manis)** if you find it useful!

</div>
