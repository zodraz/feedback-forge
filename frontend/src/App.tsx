import { useState, useRef, useEffect, FormEvent } from "react";
import "./App.css";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

const AG_UI_URL = "http://localhost:8080";

function App() {
  return (
    <div className="app-container">
      <Header />
      <main className="main-content">
        <Sidebar />
        <ChatContainer />
      </main>
    </div>
  );
}

function Header() {
  return (
    <header className="header">
      <div className="header-brand">
        <span className="header-icon">📊</span>
        <h1>FeedbackForge</h1>
      </div>
      <p className="header-tagline">Executive Dashboard Assistant</p>
    </header>
  );
}

function Sidebar() {
  const quickActions = [
    { icon: "📈", label: "Weekly Summary", query: "Show me this week's feedback summary" },
    { icon: "🔥", label: "Top Issues", query: "What are the top issues this week?" },
    { icon: "🚨", label: "Anomalies", query: "Check for any anomalies in recent feedback" },
    { icon: "🏆", label: "Competitors", query: "What are customers saying about competitors?" },
    { icon: "⚠️", label: "Churn Risks", query: "Show me customers at risk of churning" },
    { icon: "📱", label: "iOS Issues", query: "Tell me more about the iOS crashes" },
  ];

  return (
    <aside className="sidebar">
      <h2>Quick Actions</h2>
      <div className="quick-actions">
        {quickActions.map((action, index) => (
          <button
            key={index}
            className="quick-action-btn"
            onClick={() => {
              navigator.clipboard.writeText(action.query);
              const event = new CustomEvent('quickAction', { detail: action.query });
              window.dispatchEvent(event);
            }}
          >
            <span className="action-icon">{action.icon}</span>
            <span className="action-label">{action.label}</span>
          </button>
        ))}
      </div>

      <div className="sidebar-info">
        <h3>Available Tools</h3>
        <ul>
          <li>Weekly summaries</li>
          <li>Issue deep-dives</li>
          <li>Competitor analysis</li>
          <li>Customer context</li>
          <li>Anomaly detection</li>
          <li>Alert management</li>
          <li>Action generation</li>
          <li>Team escalation</li>
        </ul>
      </div>
    </aside>
  );
}

function ChatContainer() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Hi! I'm your Executive Dashboard Assistant. I can help you analyze customer feedback, identify trends, and generate actionable insights.\n\nTry asking me:\n- 'Show me this week's feedback summary'\n- 'What are the top issues?'\n- 'Check for any anomalies'",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [threadId] = useState(() => `thread-${Date.now()}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Listen for quick action events
  useEffect(() => {
    const handleQuickAction = (e: CustomEvent) => {
      setInput(e.detail);
    };
    window.addEventListener('quickAction', handleQuickAction as EventListener);
    return () => window.removeEventListener('quickAction', handleQuickAction as EventListener);
  }, []);

  const sendMessage = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    // Create assistant message placeholder
    const assistantMessageId = `assistant-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      {
        id: assistantMessageId,
        role: "assistant",
        content: "",
        timestamp: new Date(),
      },
    ]);

    try {
      // Build message history for AG-UI
      const agUiMessages = messages
        .filter((m) => m.id !== "welcome")
        .map((m) => ({
          id: m.id,
          role: m.role,
          content: m.content,
        }));

      agUiMessages.push({
        id: userMessage.id,
        role: "user",
        content: userMessage.content,
      });

      const response = await fetch(AG_UI_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          thread_id: threadId,
          run_id: `run-${Date.now()}`,
          messages: agUiMessages,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Process SSE stream
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantContent = "";

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));

                // Handle different AG-UI event types
                if (data.type === "TEXT_MESSAGE_CONTENT") {
                  assistantContent += data.delta || "";
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantMessageId
                        ? { ...m, content: assistantContent }
                        : m
                    )
                  );
                } else if (data.type === "TEXT_MESSAGE_END" || data.type === "RUN_FINISHED") {
                  // Message complete
                } else if (data.type === "TOOL_CALL_START") {
                  // Show tool being called
                  const toolName = data.tool_call?.name || "tool";
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantMessageId
                        ? { ...m, content: assistantContent + `\n\n_Using ${toolName}..._` }
                        : m
                    )
                  );
                } else if (data.type === "TOOL_CALL_END") {
                  // Remove tool indicator when done
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantMessageId
                        ? { ...m, content: assistantContent }
                        : m
                    )
                  );
                }
              } catch {
                // Ignore parse errors for non-JSON lines
              }
            }
          }
        }
      }
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantMessageId
            ? { ...m, content: "Sorry, I encountered an error. Please make sure the server is running at " + AG_UI_URL }
            : m
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.role}`}>
            <div className="message-avatar">
              {message.role === "user" ? "👤" : "🤖"}
            </div>
            <div className="message-content">
              <div className="message-text">{message.content}</div>
              <div className="message-time">
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}
        {isLoading && messages[messages.length - 1]?.content === "" && (
          <div className="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={sendMessage} className="chat-input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about feedback, issues, competitors..."
          className="chat-input"
          disabled={isLoading}
        />
        <button type="submit" className="chat-submit" disabled={isLoading || !input.trim()}>
          {isLoading ? "..." : "Send"}
        </button>
      </form>
    </div>
  );
}

export default App;
