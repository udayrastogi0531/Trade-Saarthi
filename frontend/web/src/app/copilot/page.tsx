"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { DisciplineBanner } from "@/components/DisciplineBanner";
import { apiGet } from "@/lib/api";
import type { ObservabilityHealth } from "@/lib/types";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_URL = API.replace("http", "ws") + "/api/v1/ws/copilot";

type Message = { role: "user" | "assistant"; content: string };

export default function CopilotPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [language, setLanguage] = useState("hinglish");
  const [listening, setListening] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [connected, setConnected] = useState(false);
  const [health, setHealth] = useState<ObservabilityHealth | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamAssistRef = useRef(false);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    apiGet<ObservabilityHealth>("/observability/health").then(setHealth).catch(() => {});
  }, []);

  const playAudio = (b64: string, mime: string) => {
    const audio = new Audio(`data:${mime};base64,${b64}`);
    audio.play().catch(() => {});
  };

  const connectWs = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    const ws = new WebSocket(WS_URL);
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (ev) => {
      const data = JSON.parse(ev.data);
      if (data.type === "pong") return;
      if (data.type === "error") {
        setIsStreaming(false);
        setMessages((prev) => [...prev, { role: "assistant", content: `Error: ${data.message}` }]);
        return;
      }
      if (data.type === "token") {
        streamAssistRef.current = true;
        setIsStreaming(true);
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last?.role === "assistant" && streamAssistRef.current) {
            return [...prev.slice(0, -1), { role: "assistant", content: last.content + data.content }];
          }
          return [...prev, { role: "assistant", content: data.content }];
        });
      }
      if (data.type === "meta" && data.session_id) setSessionId(data.session_id);
      if (data.type === "done") {
        setIsStreaming(false);
        streamAssistRef.current = false;
        setMessages((prev) => {
          const copy = [...prev];
          if (copy.length && copy[copy.length - 1].role === "assistant") {
            copy[copy.length - 1] = { role: "assistant", content: data.content };
          }
          return copy;
        });
      }
      if (data.type === "alert") {
        setMessages((prev) => [...prev, { role: "assistant", content: `Alert: ${data.message}` }]);
        fetch(`${API}/api/v1/copilot/voice/synthesize`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: data.message.slice(0, 400), language }),
        })
          .then((r) => r.json())
          .then((d) => d.audio_base64 && playAudio(d.audio_base64, d.audio_mime));
      }
    };
    wsRef.current = ws;
  }, [language]);

  useEffect(() => {
    connectWs();
    const pingIv = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "ping" }));
      }
    }, 30000);
    return () => {
      clearInterval(pingIv);
      wsRef.current?.close();
    };
  }, [connectWs]);

  useEffect(() => {
    if (connected) return;
    const retry = setTimeout(() => connectWs(), 3000);
    return () => clearTimeout(retry);
  }, [connected, connectWs]);

  const sendHttp = async (text: string) => {
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    const res = await fetch(`${API}/api/v1/copilot/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, session_id: sessionId, language, account_id: 1 }),
    });
    const data = await res.json();
    setSessionId(data.session_id);
    setMessages((prev) => [...prev, { role: "assistant", content: data.reply }]);
    if (data.audio_base64) playAudio(data.audio_base64, data.audio_mime);
  };

  const sendMessage = (text: string) => {
    if (!text.trim()) return;
    setInput("");
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      sendHttp(text);
      return;
    }
    streamAssistRef.current = false;
    setMessages((prev) => [...prev, { role: "user", content: text }, { role: "assistant", content: "" }]);
    setIsStreaming(true);
    wsRef.current.send(
      JSON.stringify({ type: "chat", message: text, session_id: sessionId, language, account_id: 1 })
    );
  };

  const startListening = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
      recorder.onstop = async () => {
        setListening(false);
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        const form = new FormData();
        form.append("file", blob, "voice.webm");
        form.append("language", language);
        if (sessionId) form.append("session_id", sessionId);
        const res = await fetch(`${API}/api/v1/copilot/voice/chat`, { method: "POST", body: form });
        const data = await res.json();
        setSessionId(data.session_id);
        setMessages((prev) => [
          ...prev,
          { role: "user", content: "Voice message" },
          { role: "assistant", content: data.reply },
        ]);
        if (data.audio_base64) playAudio(data.audio_base64, data.audio_mime);
        stream.getTracks().forEach((t) => t.stop());
      };
      mediaRef.current = recorder;
      recorder.start();
      setListening(true);
    } catch {
      alert("Microphone access required");
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] max-w-4xl mx-auto">
      <header className="mb-4 flex items-center justify-between flex-wrap gap-2">
        <div>
          <Link href="/" className="text-xs text-gray-500 hover:text-white mb-1 block">
            {"<- Dashboard"}
          </Link>
          <h1 className="text-2xl font-bold">AI Trading Copilot</h1>
          <p className="text-sm text-gray-400">Voice - Hindi - Hinglish - Live market context</p>
        </div>
        <div className="flex items-center gap-3">
          <span
            className={`text-xs px-2 py-1 rounded ${
              connected ? "text-profit bg-profit/10" : "text-gray-400 bg-surface"
            }`}
          >
            {connected ? "Live WS" : "HTTP"}
          </span>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="bg-panel border border-border rounded-lg px-2 py-1 text-sm"
          >
            <option value="hinglish">Hinglish</option>
            <option value="hi">Hindi</option>
            <option value="en">English</option>
          </select>
        </div>
      </header>

      <DisciplineBanner
        executionEnabled={health?.execution_enabled}
        paperTrading={health?.paper_trading}
        conservativeMode={health?.conservative_mode}
      />

      <div className="flex-1 card overflow-y-auto space-y-3 mb-4 min-h-[400px]">
        {messages.length === 0 && (
          <div className="text-gray-500 text-sm p-4 space-y-2">
            <p className="font-medium text-gray-300">Example queries</p>
            <p>- Nifty ka trend kya hai?</p>
            <p>- Open trades batao</p>
            <p>- Risk exposure kitna hai?</p>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                m.role === "user" ? "bg-accent text-white" : "bg-surface border border-border"
              }`}
            >
              {m.content || (isStreaming && i === messages.length - 1 ? "|" : "")}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="card flex items-center gap-2 p-3">
        <button
          type="button"
          onClick={listening ? () => mediaRef.current?.stop() : startListening}
          className={`shrink-0 w-12 h-12 rounded-full flex items-center justify-center text-xl transition ${
            listening ? "bg-loss/80 animate-pulse ring-4 ring-loss/40" : "bg-surface border border-border hover:border-accent"
          }`}
        >
          MIC
        </button>
        <input
          className="flex-1 bg-transparent outline-none text-sm min-w-0"
          placeholder="Type or use mic..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage(input)}
        />
        <button
          type="button"
          onClick={() => sendMessage(input)}
          className="shrink-0 bg-accent hover:bg-blue-600 px-4 py-2 rounded-lg text-sm font-medium"
        >
          Send
        </button>
      </div>
    </div>
  );
}
