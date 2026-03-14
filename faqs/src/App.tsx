import { useState, useEffect } from 'react'
import './App.css'

// Load API URL from environment variables
// const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8081/api'
const 

if (import.meta.env.PROD) {
  // code inside here will be tree-shaken in production builds
  console.log('Production mode')
  var API_BASE_URL ="https://feedbackforge-backend.ashycliff-a7a13cfc.swedencentral.azurecontainerapps.io/api"
} else {
  console.log('Development mode')
  var API_BASE_URL ="http://localhost:8081/api"
}

interface FaqItem {
  question: string
  answer: string
  frequency: number
  platforms: string[]
  segments: string[]
  avg_rating: number
  sample_count: number
  last_mentioned: string
  related_feedback: Array<{
    customer: string
    text: string
  }>
}

interface FaqDocument {
  id: string
  generated_at: string
  faq_count: number
  theme_count: number
  faqs: FaqItem[]
}

function App() {
  const [faqDocuments, setFaqDocuments] = useState<FaqDocument[]>([])
  const [selectedDocument, setSelectedDocument] = useState<FaqDocument | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch FAQs from the backend
  const fetchFaqs = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/faqs?limit=10`)

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const data = await response.json()

      if (!data || data.length === 0) {
        setFaqDocuments([])
        setSelectedDocument(null)
      } else {
        setFaqDocuments(data)
        setSelectedDocument(data[0]) // Select the most recent by default
      }
    } catch (err) {
      console.error('Failed to fetch FAQs:', err)
      setError(err instanceof Error ? err.message : 'Failed to load FAQs')
      setFaqDocuments([])
      setSelectedDocument(null)
    } finally {
      setLoading(false)
    }
  }

  // Fetch on mount
  useEffect(() => {
    fetchFaqs()
  }, [])

  // Format date for display
  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString)
      return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return dateString
    }
  }

  return (
    <div className="app">
      <div className="container">
        <header className="header">
          <h1>📚 FAQ Viewer</h1>
          <p>Browse auto-generated FAQs from customer feedback</p>
        </header>

        <div className="controls">
          <button onClick={fetchFaqs}>🔄 Refresh</button>

          {faqDocuments.length > 0 && (
            <select
              value={selectedDocument?.id || ''}
              onChange={(e) => {
                const doc = faqDocuments.find(d => d.id === e.target.value)
                setSelectedDocument(doc || null)
              }}
            >
              {faqDocuments.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {formatDate(doc.generated_at)} ({doc.faq_count} FAQs)
                </option>
              ))}
            </select>
          )}
        </div>

        {loading && (
          <div className="loading">
            Loading FAQs
          </div>
        )}

        {error && (
          <div className="error">
            <h2>⚠️ Error</h2>
            <p>{error}</p>
            <p style={{ marginTop: '10px', fontSize: '0.9rem' }}>
              Make sure the backend is running: <code>python -m feedbackforge serve --port 8081</code>
            </p>
          </div>
        )}

        {!loading && !error && faqDocuments.length === 0 && (
          <div className="no-faqs">
            <h2>No FAQs Found</h2>
            <p>No FAQ documents are available yet.</p>
            <p>Generate some FAQs first:</p>
            <code style={{
              display: 'block',
              marginTop: '20px',
              padding: '15px',
              background: 'rgba(255, 255, 255, 0.2)',
              borderRadius: '8px'
            }}>
              python -m feedbackforge faq
            </code>
          </div>
        )}

        {!loading && selectedDocument && (
          <div className="faq-document">
            <div className="faq-document-header">
              <h2>FAQ Collection</h2>
              <div className="faq-meta">
                <span>
                  📅 Generated: {formatDate(selectedDocument.generated_at)}
                </span>
                <span>
                  <span className="badge count">{selectedDocument.faq_count} FAQs</span>
                </span>
                <span>
                  <span className="badge themes">{selectedDocument.theme_count} Themes</span>
                </span>
              </div>
            </div>

            <div className="faq-list">
              {selectedDocument.faqs.map((faq, index) => (
                <div key={index} className="faq-item">
                  <div className="faq-question">
                    <span className="faq-number">{index + 1}.</span>
                    <span>{faq.question}</span>
                  </div>

                  <div className="faq-answer">{faq.answer}</div>

                  <div className="faq-stats">
                    <span className="stat-badge frequency">
                      📊 {faq.frequency} mentions
                    </span>
                    <span className="stat-badge rating">
                      ⭐ {faq.avg_rating}/5
                    </span>
                    {faq.platforms.filter(p => p !== null).length > 0 && (
                      <span className="stat-badge platforms">
                        💻 {faq.platforms.filter(p => p !== null).join(', ')}
                      </span>
                    )}
                  </div>

                  {faq.related_feedback && faq.related_feedback.length > 0 && (
                    <details className="feedback-samples">
                      <summary>📝 View Related Customer Feedback</summary>
                      {faq.related_feedback.map((feedback, idx) => (
                        <div key={idx} className="feedback-sample">
                          <strong>{feedback.customer}:</strong>
                          {feedback.text}
                        </div>
                      ))}
                    </details>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
