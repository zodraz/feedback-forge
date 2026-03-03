# 📝 Auto FAQ Generator with RAG

## What It Does

The Auto FAQ Generator uses **semantic search and clustering** to automatically create FAQs from customer feedback. No manual work needed!

### Key Features:
- 🔍 **Finds Common Questions** - Uses RAG to identify repeated issues/questions
- 🎯 **Smart Clustering** - Groups similar feedback together
- ✍️ **Auto-Generates Answers** - Creates helpful responses based on patterns
- 📊 **Prioritizes by Frequency** - Most common issues first
- 📄 **Multiple Export Formats** - Markdown, JSON, HTML
- 🔄 **Auto-Updates** - Run daily/weekly to keep FAQs fresh

---

## Quick Start (3 Steps)

### 1. Make Sure RAG is Configured

You need Azure AI Search set up (see [RAG_QUICKSTART.md](./RAG_QUICKSTART.md)):

```bash
# Check .env has these:
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_API_KEY=your-key
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_KEY=...
```

### 2. Run the Generator

```bash
python -m feedbackforge.cli_faq
```

### 3. View Your FAQs

Opens these files:
- `FAQ_[timestamp].md` - Markdown format
- `faq_[timestamp].json` - JSON format
- `faq_[timestamp].html` - HTML format (open in browser!)

**That's it!** 🎉

---

## How It Works

```
┌─────────────────────────────────────────┐
│  Customer Feedback (last 30 days)      │
│  • 1,000+ feedback items                │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  RAG Semantic Search                    │
│  • "how to..."                          │
│  • "not working..."                     │
│  • "why does..."                        │
│  • "error with..."                      │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Smart Clustering                       │
│  • Groups similar questions             │
│  • Counts frequency                     │
│  • Filters by threshold (min 3)        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  FAQ Generation                         │
│  • Extracts clean questions             │
│  • Generates helpful answers            │
│  • Adds metadata (platforms, ratings)  │
│  • Links to real customer quotes       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Export to Markdown, JSON, HTML        │
└─────────────────────────────────────────┘
```

---

## Usage Examples

### Basic Usage

```bash
# Generate FAQs from last 30 days
python -m feedbackforge.cli_faq
```

### Custom Timeframe

```bash
# Only last 7 days
python -m feedbackforge.cli_faq --days 7

# Last 90 days
python -m feedbackforge.cli_faq --days 90
```

### Adjust Sensitivity

```bash
# Only show issues mentioned 5+ times (reduce noise)
python -m feedbackforge.cli_faq --min-mentions 5

# Show all issues mentioned 2+ times (more comprehensive)
python -m feedbackforge.cli_faq --min-mentions 2
```

### Limit FAQ Count

```bash
# Top 10 most common
python -m feedbackforge.cli_faq --max-faqs 10

# Top 25
python -m feedbackforge.cli_faq --max-faqs 25
```

### Change Answer Style

```bash
# Friendly tone
python -m feedbackforge.cli_faq --style friendly

# Technical tone
python -m feedbackforge.cli_faq --style technical

# Helpful (default)
python -m feedbackforge.cli_faq --style helpful
```

### Select Export Formats

```bash
# Only HTML
python -m feedbackforge.cli_faq --formats html

# Markdown and JSON
python -m feedbackforge.cli_faq --formats markdown json

# All formats (default)
python -m feedbackforge.cli_faq --formats markdown json html
```

### Complete Example

```bash
# Last 14 days, minimum 4 mentions, top 20, friendly style, HTML only
python -m feedbackforge.cli_faq \
  --days 14 \
  --min-mentions 4 \
  --max-faqs 20 \
  --style friendly \
  --formats html
```

---

## Programmatic Usage

Use in your own Python code:

```python
from feedbackforge.faq_generator import generate_faq

# Generate FAQs
result = generate_faq(
    timeframe_days=30,
    min_occurrences=3,
    max_faqs=15,
    answer_style="helpful",
    output_formats=["markdown", "html"]
)

print(f"Generated {len(result['faqs'])} FAQs")
print(f"Exported to: {result['exports']}")

# Access FAQ data
for faq in result['faqs']:
    print(f"Q: {faq['question']}")
    print(f"A: {faq['answer']}")
    print(f"Mentioned {faq['frequency']} times")
    print()
```

### Advanced: Custom Generation

```python
from feedbackforge.faq_generator import FAQGenerator

generator = FAQGenerator()

# Step 1: Find themes
themes = generator.find_common_themes(
    timeframe_days=30,
    min_occurrences=3,
    max_themes=20
)

# Step 2: Generate FAQ entries
faqs = generator.generate_faq_entries(
    themes,
    answer_style="technical"
)

# Step 3: Export
generator.export_to_markdown(faqs, "custom_faq.md")
generator.export_to_html(faqs, "custom_faq.html")
```

---

## Output Formats

### 1. Markdown (FAQ_[timestamp].md)

```markdown
# Frequently Asked Questions

*Auto-generated from customer feedback on 2026-02-27*

---

## 1. Why isn't the export feature working?

Thanks for asking! We're aware that 8 customers have reported
this issue across iOS, Android platforms. Our team is actively
investigating and will provide updates soon...

**Frequency**: Mentioned 8 times | **Platforms**: iOS, Android | **Avg Rating**: 2.3/5

<details>
<summary>📝 Related Customer Feedback</summary>

- **John Smith**: The export button doesn't respond when I click it...
- **Jane Doe**: I can't export my data to CSV...

</details>

---
```

**Best for:**
- Documentation sites
- GitHub wikis
- Internal knowledge bases

### 2. JSON (faq_[timestamp].json)

```json
{
  "generated_at": "2026-02-27T19:30:00",
  "faq_count": 15,
  "faqs": [
    {
      "question": "Why isn't the export feature working?",
      "answer": "Thanks for asking! We're aware that...",
      "frequency": 8,
      "platforms": ["iOS", "Android"],
      "segments": ["Enterprise", "SMB"],
      "avg_rating": 2.3,
      "sample_count": 8,
      "related_feedback": [...]
    }
  ]
}
```

**Best for:**
- APIs
- Data pipelines
- Analytics tools
- Custom integrations

### 3. HTML (faq_[timestamp].html)

Beautiful, styled HTML page with:
- ✨ Clean, modern design
- 📱 Mobile-responsive
- 🎨 Color-coded badges
- 📊 Expandable feedback samples
- 🔍 Easy to read

**Best for:**
- Customer-facing FAQ pages
- Support portals
- Email newsletters
- Team presentations

---

## Automation

### Daily FAQ Updates

Create a cron job or scheduled task:

**Linux/Mac (crontab):**
```bash
# Run every day at 8 AM
0 8 * * * cd /path/to/feedbackforge && python -m feedbackforge.cli_faq --days 7
```

**Windows (Task Scheduler):**
```powershell
# Create scheduled task
schtasks /create /tn "FAQ Generator" /tr "python -m feedbackforge.cli_faq" /sc daily /st 08:00
```

**Docker/Kubernetes:**
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: faq-generator
spec:
  schedule: "0 8 * * *"  # Daily at 8 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: faq-gen
            image: feedbackforge:latest
            command: ["python", "-m", "feedbackforge.cli_faq"]
```

### CI/CD Integration

**GitHub Actions:**
```yaml
name: Update FAQs
on:
  schedule:
    - cron: '0 8 * * *'  # Daily at 8 AM
  workflow_dispatch:  # Manual trigger

jobs:
  generate-faq:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e .
      - run: python -m feedbackforge.cli_faq
      - uses: actions/upload-artifact@v3
        with:
          name: faq-files
          path: FAQ_*.md
```

---

## Examples of Generated FAQs

### Example 1: Question Detection

**Input Feedback:**
- "How do I export my data to CSV?"
- "Can I download my information?"
- "Where's the export button?"

**Generated FAQ:**
```
Q: How do I export data?
A: Thanks for asking! Based on feedback from 12 customers,
   here's what we recommend:
   1. Check our documentation at docs.example.com
   2. Contact our support team for personalized help

Frequency: 12 mentions | Platforms: Web, Desktop | Avg: 3.5/5
```

### Example 2: Issue Detection

**Input Feedback:**
- "App crashes when I open settings"
- "Settings page not loading"
- "Can't access settings - error"

**Generated FAQ:**
```
Q: Why isn't settings working?
A: We're aware that 15 customers have reported this issue
   on iOS, Android platforms. Our team is actively
   investigating and will provide updates soon. In the
   meantime, please contact support@example.com.

Frequency: 15 mentions | Platforms: iOS, Android | Avg: 1.8/5
```

---

## Customization

### Custom Answer Templates

Extend the `FAQGenerator` class:

```python
from feedbackforge.faq_generator import FAQGenerator

class CustomFAQGenerator(FAQGenerator):
    def _generate_answer(self, theme, style="helpful"):
        # Add your custom logic
        if theme['count'] > 10:
            return "This is a HOT topic! Here's what we know..."

        return super()._generate_answer(theme, style)
```

### Custom Export Format

```python
def export_to_pdf(faqs, filepath):
    """Export FAQs to PDF."""
    # Use reportlab, weasyprint, or similar
    pass

generator = FAQGenerator()
themes = generator.find_common_themes()
faqs = generator.generate_faq_entries(themes)
export_to_pdf(faqs, "faq.pdf")
```

---

## Best Practices

### 1. Regular Updates
- ✅ Run daily or weekly
- ✅ Keep timeframe reasonable (7-30 days)
- ✅ Archive old versions for comparison

### 2. Tune Parameters
- Start with defaults
- Adjust `--min-mentions` based on volume
- Higher volume → increase threshold
- Lower volume → decrease threshold

### 3. Review Before Publishing
- FAQs are auto-generated - review for accuracy
- Edit answers to add specific solutions
- Add links to documentation/resources

### 4. Track Trends
- Save JSON outputs over time
- Monitor which questions are trending
- Identify seasonal patterns

### 5. Integrate with Support
- Share FAQs with support team
- Update help docs automatically
- Use in chatbot responses

---

## Troubleshooting

### No FAQs Generated

**Problem:** Returns empty or very few FAQs

**Solutions:**
```bash
# 1. Lower the threshold
python -m feedbackforge.cli_faq --min-mentions 2

# 2. Increase timeframe
python -m feedbackforge.cli_faq --days 60

# 3. Increase max count
python -m feedbackforge.cli_faq --max-faqs 25

# 4. Check RAG is configured
python -c "from feedbackforge.rag_search import rag_search_client; print(rag_search_client)"
```

### Poor Quality FAQs

**Problem:** Questions/answers don't make sense

**Solutions:**
- Increase `--min-mentions` to focus on common issues
- Review and edit generated FAQs before publishing
- Adjust answer style (`--style`)
- Consider custom answer templates

### Slow Generation

**Problem:** Takes too long to generate

**Solutions:**
- Reduce timeframe (`--days 7`)
- Reduce max FAQs (`--max-faqs 10`)
- Check Azure AI Search performance tier
- Use caching for embeddings

---

## Cost Estimation

### Azure AI Search Queries
- ~10-20 queries per FAQ generation
- Basic tier: Included in monthly cost
- **Cost**: ~$0 extra per run

### Total
- **Per run**: ~$0
- **Monthly (daily runs)**: ~$0
- **Only ongoing cost**: Azure AI Search subscription (~$75/month)

---

## Integration Examples

### 1. Website FAQ Page

```javascript
// Fetch FAQ JSON
fetch('/api/faq.json')
  .then(r => r.json())
  .then(data => {
    data.faqs.forEach(faq => {
      displayFAQ(faq.question, faq.answer);
    });
  });
```

### 2. Chatbot Context

```python
# Use FAQs as chatbot knowledge base
with open('faq.json') as f:
    faqs = json.load(f)

# Add to chatbot context
context = "\n".join([
    f"Q: {faq['question']}\nA: {faq['answer']}"
    for faq in faqs['faqs']
])
```

### 3. Email Newsletter

```python
# Generate weekly FAQ email
result = generate_faq(timeframe_days=7, max_faqs=5)

email_body = "Top 5 Questions This Week:\n\n"
for faq in result['faqs']:
    email_body += f"Q: {faq['question']}\n"
    email_body += f"A: {faq['answer']}\n\n"

send_email(to="team@example.com", body=email_body)
```

---

## FAQ About FAQs 😄

### Q: How accurate are the generated FAQs?

A: The FAQs are based on real customer feedback patterns. Accuracy depends on:
- Data quality
- Feedback volume
- RAG configuration quality

**Recommendation:** Always review before publishing.

### Q: Can I edit the generated FAQs?

A: Yes! All formats are editable:
- **Markdown**: Edit in any text editor
- **JSON**: Modify programmatically
- **HTML**: Edit the HTML file

### Q: How often should I regenerate FAQs?

A: Depends on feedback volume:
- **High volume** (100+ daily): Daily
- **Medium volume** (20-100 daily): Weekly
- **Low volume** (<20 daily): Monthly

### Q: Can I customize the questions/answers?

A: Yes! See the [Customization](#customization) section.

### Q: What if I don't have RAG set up?

A: The FAQ generator requires RAG (Azure AI Search). See [RAG_QUICKSTART.md](./RAG_QUICKSTART.md) for setup.

---

## Next Steps

1. ✅ **Run your first FAQ generation**
   ```bash
   python -m feedbackforge.cli_faq
   ```

2. ✅ **Review the output files**
   - Open the HTML file in a browser
   - Check the Markdown for accuracy

3. ✅ **Customize parameters**
   - Adjust timeframe and thresholds
   - Try different styles

4. ✅ **Automate it**
   - Set up daily/weekly generation
   - Integrate with your workflow

5. ✅ **Publish FAQs**
   - Add to your website
   - Share with support team
   - Use in documentation

---

**Last Updated**: 2026-02-27
**Version**: 1.0.0

Need help? Check the [main README](./README.md) or open an issue!
