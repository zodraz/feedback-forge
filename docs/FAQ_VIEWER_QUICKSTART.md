# FAQ Viewer - Quick Start Guide

Beautiful web interface for viewing auto-generated FAQs from customer feedback stored in CosmosDB.

## 🚀 Quick Start

### Step 1: Start the Backend Server

```bash
python -m feedbackforge serve --port 8081
```

This starts the API server that provides FAQ data.

### Step 2: Generate Some FAQs

In a new terminal, generate FAQs from feedback data:

```bash
python -m feedbackforge faq --max-faqs 10
```

This will:
- Analyze customer feedback using RAG
- Generate FAQ entries
- Save them to CosmosDB (or in-memory if Cosmos not configured)
- Export to markdown/JSON/HTML files

### Step 3: Start the FAQ Viewer

In another terminal:

```bash
cd faqs
npm install  # First time only
npm run dev
```

The FAQ viewer will open at **http://localhost:3002/**

## 📸 What You'll See

The FAQ viewer displays:

- **📚 FAQ Collections** - All generated FAQ sets with timestamps
- **📊 Statistics** - FAQ count, theme count, generation date
- **🔍 FAQ Details** - Questions, answers, frequency, ratings
- **💬 Customer Feedback** - Related customer quotes for each FAQ
- **🎨 Beautiful UI** - Modern, responsive design with smooth animations

## 🔄 Workflow

```
┌─────────────────────────────────────────────────────────┐
│  1. Generate FAQs                                       │
│     python -m feedbackforge faq                         │
│                                                         │
│  2. FAQs saved to CosmosDB                             │
│     Collection: "faqs"                                  │
│                                                         │
│  3. Backend serves FAQs                                │
│     GET /api/faqs                                       │
│                                                         │
│  4. FAQ Viewer fetches & displays                      │
│     http://localhost:3002/                             │
└─────────────────────────────────────────────────────────┘
```

## 🎯 Features

### Browse Collections
- View all generated FAQ collections
- Switch between different FAQ generations
- See generation timestamps and counts

### View FAQ Details
Each FAQ shows:
- **Question** - Clear, well-formatted question
- **Answer** - Helpful, context-aware answer
- **Frequency** - How many customers mentioned this
- **Rating** - Average customer satisfaction score
- **Platforms** - Which platforms are affected (iOS, Android, Web, etc.)
- **Related Feedback** - Sample customer quotes

### Refresh Data
- Click the 🔄 Refresh button to fetch latest FAQs
- No page reload needed

## 🛠️ Configuration

### Change API URL

Edit `faqs/src/App.tsx`:

```typescript
const API_BASE_URL = 'http://localhost:8081/api'
```

### Change Port

Edit `faqs/vite.config.ts`:

```typescript
server: {
  port: 3002  // Change to your preferred port
}
```

## 📝 API Endpoints Used

The FAQ viewer uses these backend endpoints:

### Get All FAQs
```
GET /api/faqs?limit=<number>
```

**Response:**
```json
[
  {
    "id": "2026-02-28T14-13-19-063202",
    "generated_at": "2026-02-28T14:13:19.063202",
    "faq_count": 4,
    "theme_count": 4,
    "faqs": [...]
  }
]
```

### Get Specific FAQ
```
GET /api/faqs/{faq_id}
```

**Response:** Single FAQ document

## 🐛 Troubleshooting

### No FAQs Appear

**Problem:** FAQ viewer shows "No FAQs Found"

**Solution:**
1. Check backend is running: `curl http://localhost:8081/health`
2. Generate FAQs: `python -m feedbackforge faq`
3. Verify data in Cosmos: Check Azure portal or use test script
4. Click Refresh button in FAQ viewer

### Connection Refused

**Problem:** "Failed to load FAQs: Failed to fetch"

**Solution:**
1. Ensure backend is running on port 8081
2. Check CORS is enabled in backend
3. Verify API_BASE_URL in `faqs/src/App.tsx`

### Empty FAQ Collections

**Problem:** FAQ collections show up but have 0 FAQs

**Solution:**
1. Check FAQ generation parameters:
   ```bash
   python -m feedbackforge faq --min-mentions 2 --max-faqs 20
   ```
2. Ensure there's enough feedback data in the system
3. Lower `--min-mentions` to capture more FAQs

### CORS Errors

**Problem:** CORS policy blocking requests

**Solution:**
Backend (server.py) already includes CORS configuration for `*` origins.
If you need specific origins:

```python
origins = ["http://localhost:3002", "http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    ...
)
```

## 📦 Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Fast dev server and build tool
- **CSS3** - Modern styling with animations
- **Fetch API** - RESTful API communication

## 🎨 Customization

### Change Colors

Edit `src/faqs/src/App.css`:

```css
.app {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  /* Change to your brand colors */
}
```

### Add Features

The codebase is well-structured for adding:
- Search/filter functionality
- Export FAQs to PDF/CSV
- FAQ voting/feedback
- Analytics dashboard
- Multi-language support

## 🚢 Deployment

### Build for Production

```bash
cd faqs
npm run build
```

Output in `dist/` directory. Serve with:
- Nginx
- Apache
- Netlify
- Vercel
- Azure Static Web Apps

### Environment Variables

For production, set:
```bash
VITE_API_URL=https://your-backend.com/api
```

Update `src/App.tsx`:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8081/api'
```

## 📊 Sample FAQ Data

Example FAQ entry:

```json
{
  "question": "Why isn't this feature working?",
  "answer": "We're aware that 16 customers have reported this issue...",
  "frequency": 16,
  "platforms": ["iOS", "Android"],
  "segments": ["SMB", "Enterprise"],
  "avg_rating": 1.0,
  "sample_count": 16,
  "last_mentioned": "2026-02-27T18:10:29.026Z",
  "related_feedback": [
    {
      "customer": "MegaSystems",
      "text": "Checkout not working! Can't complete my purchase."
    }
  ]
}
```

## 🎓 Next Steps

1. **Customize Styling** - Make it match your brand
2. **Add Search** - Filter FAQs by keyword
3. **Export Features** - Let users download FAQs
4. **Analytics** - Track which FAQs are viewed most
5. **Feedback Loop** - Let users vote on FAQ helpfulness

## 📚 Related Documentation

- [FAQ Generation Guide](FAQ_QUICKSTART.md)
- [Backend API Documentation](http://localhost:8081/docs)
- [Project Structure](docs/PROJECT_STRUCTURE.md)

## 💡 Tips

- **Refresh Regularly** - Click refresh to see newly generated FAQs
- **Use Dropdown** - Switch between different FAQ collections
- **Expand Feedback** - Click to see related customer quotes
- **Mobile Friendly** - Responsive design works on all devices

---

**Status**: ✅ Ready to Use
**Port**: 3002
**Dependencies**: Backend server (port 8081) + FAQ data in CosmosDB
