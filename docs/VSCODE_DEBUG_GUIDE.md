# VSCode Debugging Guide for FeedbackForge

## Quick Start

The project is now configured for easy debugging in VSCode!

## Available Debug Configurations

Press `F5` or go to **Run and Debug** (Ctrl+Shift+D) and select:

### 1. **Python: FeedbackForge Server**
- Launches the FastAPI server with debugging enabled
- Breakpoints will work in all server code
- Access at http://localhost:8000

### 2. **Python: FAQ Generator CLI**
- Debugs the FAQ generator with sample arguments
- Default: generates FAQs from last 30 days, max 10 FAQs
- Edit `.vscode/launch.json` to change arguments

### 3. **Python: RAG Setup**
- Debugs the RAG setup and indexing script
- Use this to debug index creation and data indexing

### 4. **Python: Current File**
- Debugs the currently open Python file
- Works for most standalone scripts

### 5. **Python: Current File as Module**
- Runs the current file as a Python module
- Use this for files with relative imports

## Debugging Tips

### Setting Breakpoints
1. Click in the left gutter next to any line number
2. Red dot indicates an active breakpoint
3. Run debugger (F5) and execution will pause at breakpoint

### Debug Console
- Evaluate expressions while paused
- Type variable names to inspect values
- Execute Python code in current context

### Step Through Code
- **F10** - Step Over (execute current line)
- **F11** - Step Into (enter function calls)
- **Shift+F11** - Step Out (exit current function)
- **F5** - Continue (run until next breakpoint)

## Import Issues Fixed

The following fix was applied to support VSCode debugging:

### Problem
```python
# ❌ Fails when run directly in debugger
from .faq_generator import generate_faq
# ImportError: attempted relative import with no known parent package
```

### Solution
```python
# ✅ Works both as module and directly
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from .faq_generator import generate_faq
except ImportError:
    from feedbackforge.faq_generator import generate_faq
```

## Running from Command Line

You can still run files normally:

```bash
# As a module (recommended)
python -m feedbackforge.cli_faq --help
python -m feedbackforge.server

# Directly
python src/feedbackforge/cli_faq.py --help
```

## Environment Variables

Make sure your `.env` file is configured:

```bash
# Azure AI Search (for RAG)
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_API_KEY=your-key

# Azure OpenAI (for embeddings)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small

# Cosmos DB (optional)
COSMOS_DB_ENDPOINT=https://your-db.documents.azure.com:443/
COSMOS_DB_KEY=your-key
```

## Troubleshooting

### "Module not found" errors
- Make sure `PYTHONPATH` includes `src/` directory
- The launch.json already sets this for you

### Breakpoints not hitting
- Check that "justMyCode" is set to `false` in launch.json
- Make sure you're using the correct debug configuration

### Import errors persist
- Restart VSCode
- Delete `__pycache__` directories: `find . -type d -name __pycache__ -exec rm -rf {} +`
- Reinstall package: `pip install -e .`

## Next Steps

1. **Try the debugger**: Open `src/feedbackforge/cli_faq.py` and press F5
2. **Set a breakpoint**: Click next to line 19 (`def main():`)
3. **Step through**: Use F10 to step through the code
4. **Inspect variables**: Hover over variables or use Debug Console

Happy debugging! 🐛🔍
