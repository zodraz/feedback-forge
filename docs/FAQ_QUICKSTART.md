# Auto FAQ Generator - Quick Start

## 3-Step Quick Start

### 1. Prerequisites

Make sure you have RAG configured:
```bash
# .env must have:
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_API_KEY=your-key
```

If not, run: `python -m feedbackforge.rag_setup` first (see [RAG_QUICKSTART.md](./RAG_QUICKSTART.md))

### 2. Generate FAQs

```bash
python -m feedbackforge.cli_faq
```

### 3. View Results

Open the generated files:
- `FAQ_[timestamp].md` - Markdown
- `faq_[timestamp].json` - JSON
- `faq_[timestamp].html` - **Open this in browser!** 🎨

## That's It! 🎉

---

## Common Commands

```bash
# Last 7 days only
python -m feedbackforge.cli_faq --days 7

# Top 10 most common issues
python -m feedbackforge.cli_faq --max-faqs 10

# Friendly tone
python -m feedbackforge.cli_faq --style friendly

# HTML only
python -m feedbackforge.cli_faq --formats html
```

---

## What You Get

### Before (Manual):
- ❌ Manually read 1000+ feedback items
- ❌ Manually identify common questions
- ❌ Manually write answers
- ❌ Takes hours/days

### After (Automated):
- ✅ Auto-scans all feedback
- ✅ Auto-identifies patterns
- ✅ Auto-generates Q&A
- ✅ Takes 30 seconds

---

## Example Output

**Generated FAQ:**
```
Q: Why isn't the export feature working?

A: Thanks for asking! We're aware that 8 customers have
   reported this issue across iOS, Android platforms. Our
   team is actively investigating...

Frequency: 8 mentions | Platforms: iOS, Android | Rating: 2.3/5

Related Feedback:
- John Smith: "The export button doesn't respond..."
- Jane Doe: "I can't export my data to CSV..."
```

---

## Automate It

Run daily:
```bash
# Add to crontab
0 8 * * * cd /path/to/feedbackforge && python -m feedbackforge.cli_faq
```

---

**Full Guide**: [FAQ_GENERATOR_GUIDE.md](./FAQ_GENERATOR_GUIDE.md)
