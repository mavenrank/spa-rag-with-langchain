import React, { useState, useRef, useEffect } from "react";
import {
    FaPaperPlane,
    FaRobot,
    FaUser,
    FaDatabase,
    FaExclamationCircle,
    FaSpinner,
} from "react-icons/fa";
import "./Chat.css";

function Chat() {
    const [messages, setMessages] = useState([
        {
            role: "assistant",
            content:
                "Hello! I am your Pagila Database Assistant. Ask me anything about the movies, actors, or rental data.",
        },
    ]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [models, setModels] = useState([]);
    const [selectedModel, setSelectedModel] = useState(
        "mistralai/mistral-7b-instruct:free"
    );
    const [loadingModels, setLoadingModels] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const fetchModels = async () => {
        setLoadingModels(true);
        try {
            const response = await fetch("http://127.0.0.1:8000/models");
            if (!response.ok) throw new Error("Failed to search models");
            const data = await response.json();
            setModels(data.models || []);
            // Set default if available
            if (data.models && data.models.length > 0) {
                // Try to keep current if valid, else pick first
                const exists = data.models.find((m) => m.id === selectedModel);
                if (!exists) {
                    setSelectedModel(data.models[0].id);
                }
            }
        } catch (err) {
            console.error(err);
            alert("Could not fetch models");
        } finally {
            setLoadingModels(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMessage = { role: "user", content: input };
        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setIsLoading(true);

        try {
            const response = await fetch("http://127.0.0.1:8000/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    query: input,
                    model: selectedModel,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(
                    errorData.detail ||
                        `Network response was not ok: ${response.status} ${response.statusText}`
                );
            }

            const data = await response.json();
            const assistantMessage = {
                role: "assistant",
                content: data.response,
                metadata: data.metadata,
            };
            setMessages((prev) => [...prev, assistantMessage]);
        } catch (error) {
            console.error("Error:", error);
            setMessages((prev) => [
                ...prev,
                {
                    role: "error",
                    content: `Error: ${error.message}. Please check if the backend is running.`,
                },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="chat-container">
            <div className="chat-header">
                <div className="header-left">
                    <div className="header-icon-container">
                        <FaDatabase className="header-icon" />
                    </div>
                    <div>
                        <h1>Pagila AI Agent</h1>
                        <p className="status-text">Connected to PostgreSQL</p>
                    </div>
                </div>

                <div className="header-right">
                    {models.length === 0 ? (
                        <button
                            className="model-check-btn"
                            onClick={fetchModels}
                            disabled={loadingModels}
                        >
                            {loadingModels ? "Loading..." : "Check Free Models"}
                        </button>
                    ) : (
                        <select
                            className="model-select"
                            value={selectedModel}
                            onChange={(e) => setSelectedModel(e.target.value)}
                        >
                            <option value="" disabled>
                                Select Model
                            </option>
                            {models.map((m) => (
                                <option key={m.id} value={m.id}>
                                    {m.name || m.id}
                                </option>
                            ))}
                        </select>
                    )}
                </div>
            </div>

            <div className="messages-area">
                {messages.map((msg, index) => (
                    <div key={index} className={`message ${msg.role}`}>
                        <div className="avatar">
                            {msg.role === "assistant" && <FaRobot />}
                            {msg.role === "user" && <FaUser />}
                            {msg.role === "error" && <FaExclamationCircle />}
                        </div>
                        <div className="message-bubble">
                            {msg.content}
                            {msg.metadata && (
                                <div className="message-meta">
                                    {msg.metadata.model} •{" "}
                                    {msg.metadata.duration}s
                                </div>
                            )}
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="message assistant">
                        <div className="avatar">
                            <FaRobot />
                        </div>
                        <div className="message-bubble loading">
                            <FaSpinner className="spinner" /> Thinking...
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <form className="input-area" onSubmit={handleSubmit}>
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask a question about the database..."
                    disabled={isLoading}
                />
                <button type="submit" disabled={isLoading || !input.trim()}>
                    <FaPaperPlane />
                </button>
            </form>
        </div>
    );
}

export default Chat;
