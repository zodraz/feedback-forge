# CLI Refactoring - FAQ Command

## What Changed

The FAQ Generator CLI has been refactored to use a cleaner subcommand structure.

### Before (Old Way)
```bash
python -m feedbackforge.cli_faq --days 30 --max-faqs 10
```

### After (New Way - Recommended)
```bash
python -m feedbackforge faq --days 30 --max-faqs 10
```

## Why This Change?

1. **Consistency**: All FeedbackForge commands now use the same pattern:
   - `python -m feedbackforge chat`
   - `python -m feedbackforge serve`
   - `python -m feedbackforge workflow`
   - `python -m feedbackforge faq` ✨ NEW!

2. **Discoverability**: Users can see all available commands with:
   ```bash
   python -m feedbackforge --help
   ```

3. **Scalability**: Easy to add more commands in the future (e.g., `report`, `analyze`, `export`)

## Backwards Compatibility

✅ **The old way still works!** No breaking changes.

You can still use:
```bash
# Old module-based invocation
python -m feedbackforge.cli_faq --days 30

# Direct script execution
python src/feedbackforge/cli_faq.py --days 30
```

## All Available Commands

### Main Commands

```bash
# Show all commands
python -m feedbackforge --help

# Chat interface (DevUI)
python -m feedbackforge chat
python -m feedbackforge chat --port 8090

# Production server (AG-UI)
python -m feedbackforge serve
python -m feedbackforge serve --port 8080 --reload

# Analysis workflow
python -m feedbackforge workflow
python -m feedbackforge workflow --max-surveys 50

# FAQ Generator (NEW!)
python -m feedbackforge faq
python -m feedbackforge faq --days 7 --max-faqs 20
```

### FAQ Command Options

```bash
python -m feedbackforge faq [OPTIONS]

Options:
  --days DAYS                    Number of days to look back (default: 30)
  --min-mentions MIN             Minimum mentions for FAQ inclusion (default: 3)
  --max-faqs MAX                 Maximum FAQs to generate (default: 15)
  --style {helpful,friendly,technical}
                                 Answer style (default: helpful)
  --formats {markdown,json,html} [...]
                                 Export formats (default: all)
```

### Examples

```bash
# Generate FAQs from last 30 days (all formats)
python -m feedbackforge faq

# Generate from last week, minimum 5 mentions
python -m feedbackforge faq --days 7 --min-mentions 5

# Generate top 20 FAQs in friendly style
python -m feedbackforge faq --max-faqs 20 --style friendly

# Export only to HTML
python -m feedbackforge faq --formats html

# Export to markdown and JSON
python -m feedbackforge faq --formats markdown json

# Advanced: Last 14 days, 2+ mentions, technical style, 25 FAQs
python -m feedbackforge faq --days 14 --min-mentions 2 --style technical --max-faqs 25
```

## Technical Details

### File Structure

```
src/feedbackforge/
├── __main__.py           # Main CLI entry point (routes to subcommands)
├── cli_faq.py           # FAQ command implementation
├── server.py            # Server command
├── workflow.py          # Workflow command
└── dashboard_agent.py   # Chat command
```

### Code Changes

**`src/feedbackforge/__main__.py`**
- Added `faq` subcommand to existing subparsers
- Imports `setup_faq_parser` and `run_faq_command` from `cli_faq`
- Routes `faq` command to `run_faq_command()`

**`src/feedbackforge/cli_faq.py`**
- Refactored `main()` to use two new functions:
  - `setup_faq_parser(parser)` - Configures argument parser
  - `run_faq_command(args)` - Executes the FAQ generation
- Kept original `main()` for backwards compatibility
- Changed `sys.exit()` to `return` in `run_faq_command()` for better control

### VSCode Debug Configurations

Updated `.vscode/launch.json`:
- **"Python: FAQ Generator"** - Uses new subcommand structure (recommended)
- **"Python: FAQ Generator (Legacy)"** - Uses old direct invocation (backwards compatible)

## Migration Guide

### If you have scripts using the old way:

**Option 1: Update to new way (recommended)**
```bash
# Before
python -m feedbackforge.cli_faq --days 30

# After
python -m feedbackforge faq --days 30
```

**Option 2: Keep using old way (still works)**
```bash
# No changes needed - old way still works!
python -m feedbackforge.cli_faq --days 30
```

### If you have scheduled jobs/cron:

```bash
# Cron example (update recommended but not required)
0 9 * * * cd /app && python -m feedbackforge faq --days 7 --formats markdown
```

### If you're calling from Python code:

```python
# Before
from feedbackforge.cli_faq import main
main()

# After (recommended)
from feedbackforge.cli_faq import run_faq_command
import argparse

parser = argparse.ArgumentParser()
# ... configure parser ...
args = parser.parse_args()
exit_code = run_faq_command(args)
```

## Testing

All three invocation methods have been tested:

```bash
# ✅ New way (recommended)
python -m feedbackforge faq --help

# ✅ Old module way (backwards compatible)
python -m feedbackforge.cli_faq --help

# ✅ Direct script (backwards compatible)
python src/feedbackforge/cli_faq.py --help
```

## Future Commands

This refactoring makes it easy to add more commands:

```bash
# Potential future commands
python -m feedbackforge export    # Export feedback data
python -m feedbackforge report    # Generate reports
python -m feedbackforge analyze   # Run specific analysis
python -m feedbackforge setup     # Setup wizard
python -m feedbackforge test      # Test configuration
```

## Summary

✅ **New command structure**: `python -m feedbackforge faq`
✅ **Backwards compatible**: Old ways still work
✅ **Better UX**: Consistent with other commands
✅ **Easy to extend**: Simple to add more commands
✅ **Well documented**: This guide + inline help

---

**Questions?** Check `python -m feedbackforge --help` or `python -m feedbackforge faq --help`
