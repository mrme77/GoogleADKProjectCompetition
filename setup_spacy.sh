#!/bin/bash

# MANIS - spaCy Model Installation Script
# This script downloads the spaCy English language model needed for entity extraction
# Uses uv for faster installation (falls back to pip if uv not available)

set -e  # Exit on error

echo "=========================================="
echo "MANIS - spaCy Model Setup"
echo "=========================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found. Please install Python 3.8+ first."
    exit 1
fi

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Warning: No virtual environment detected."
    echo "   It's recommended to activate your virtual environment first:"
    echo "   source adk-env/bin/activate"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# Detect package manager (uv or pip)
if command -v uv &> /dev/null; then
    PKG_MANAGER="uv pip"
    echo "✨ Using uv (fast package installer)"
else
    PKG_MANAGER="pip"
    echo "📦 Using pip (standard package installer)"
fi
echo ""

echo "📦 Installing spaCy (if not already installed)..."
$PKG_MANAGER install --quiet --upgrade spacy>=3.8.0

echo ""
echo "📥 Downloading spaCy English language model (en_core_web_sm)..."
echo "   Size: ~12 MB"
echo ""

# Use uv run if available for faster execution
if command -v uv &> /dev/null; then
    uv run python -m spacy download en_core_web_sm
else
    python3 -m spacy download en_core_web_sm
fi

echo ""
echo "✅ Verifying installation..."

# Test if model loads correctly
PYTHON_CMD="python3"
if command -v uv &> /dev/null; then
    PYTHON_CMD="uv run python"
fi

$PYTHON_CMD -c "
import spacy
try:
    nlp = spacy.load('en_core_web_sm')
    print('✅ spaCy model loaded successfully!')

    # Test entity extraction
    doc = nlp('Apple CEO Tim Cook announced new products in Cupertino.')
    entities = [(ent.text, ent.label_) for ent in doc.ents]

    print(f'✅ Entity extraction test passed!')
    print(f'   Found {len(entities)} entities: {entities}')

except Exception as e:
    print(f'❌ Error: {e}')
    exit(1)
"

echo ""
echo "=========================================="
echo "✅ spaCy setup complete!"
echo "=========================================="
echo ""
echo "MANIS will now use spaCy NER for entity extraction with categorization:"
echo "  • PERSON - People's names"
echo "  • ORG - Organizations, companies, agencies"
echo "  • GPE/LOC - Locations, countries, cities"
echo ""
echo "Next steps:"
echo "  1. Run MANIS: ./run_manis.sh"
echo "  2. Check preprocessor output for categorized entities"
echo ""
