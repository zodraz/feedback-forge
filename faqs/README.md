# FeedbackForge FAQ Viewer

Beautiful web interface for viewing auto-generated FAQs from customer feedback stored in CosmosDB.

## Features

- 📚 Browse all generated FAQ collections
- 🔄 Real-time refresh from CosmosDB
- 📊 View FAQ statistics (frequency, ratings, platforms)
- 💬 See related customer feedback samples
- 🎨 Beautiful, responsive design
- 🌙 Dark/light mode support

## Prerequisites

1. **Backend server running** with FAQ data in CosmosDB:
   ```bash
   python -m feedbackforge serve --port 8081
   ```

2. **FAQs generated** and saved to CosmosDB:
   ```bash
   python -m feedbackforge faq
   ```

## Installation

```bash
cd src/faqs
npm install
```

## Development

```bash
npm run dev
```

The app will open at http://localhost:3002/

## Build for Production

```bash
npm run build
```

Output will be in `dist/` directory.

## Preview Production Build

```bash
npm run preview
```

## How It Works

1. **Fetches FAQs** from the backend API endpoint: `GET /api/faqs?limit=10`
2. **Displays** the most recent FAQ collection by default
3. **Allows switching** between different FAQ generations via dropdown
4. **Shows details** for each FAQ including:
   - Question and answer
   - Frequency of mentions
   - Average customer rating
   - Affected platforms
   - Related customer feedback samples

## API Requirements

The backend must expose the following endpoint:

```
GET /api/faqs?limit=<number>
```

Returns:
```json
[
  {
    "id": "2026-02-28T14-13-19-063202",
    "generated_at": "2026-02-28T14:13:19.063202",
    "faq_count": 4,
    "theme_count": 4,
    "faqs": [
      {
        "question": "Why isn't this feature working?",
        "answer": "We're aware...",
        "frequency": 16,
        "platforms": ["iOS", "Android"],
        "avg_rating": 1.0,
        "related_feedback": [...]
      }
    ]
  }
]
```

## Customization

### Change API URL

Edit `src/App.tsx`:
```typescript
const API_BASE_URL = 'http://localhost:8081/api'
```

### Change Port

Edit `vite.config.ts`:
```typescript
server: {
  port: 3002
}
```

### Styling

Modify `src/App.css` to customize colors, fonts, and layout.

## Troubleshooting

### No FAQs appear
- Check that backend is running on port 8081
- Verify FAQs exist in CosmosDB: run `python -m feedbackforge faq` first
- Check browser console for errors (F12)

### CORS errors
- Backend must allow requests from `http://localhost:3002`
- Check backend CORS configuration

### Connection refused
- Ensure backend is running: `python -m feedbackforge serve --port 8081`
- Check that API_BASE_URL matches your backend URL

## Technologies

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **CSS3** - Styling with animations

## License

MIT
