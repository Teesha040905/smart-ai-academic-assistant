"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { API_BASE, api, getToken } from "@/lib/api";
import { useAsyncData } from "@/lib/hooks";
import { Conversation, Message, Subject } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { ErrorState, LoadingState } from "@/components/ui/StateViews";
import { Icon } from "@/components/ui/Icon";

export default function TutorPage() {
  const convLoader = useCallback(() => api.get<Conversation[]>("/ai/conversations"), []);
  const subjectLoader = useCallback(() => api.get<Subject[]>("/subjects"), []);
  const convs = useAsyncData(convLoader, []);
  const subjects = useAsyncData(subjectLoader, []);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loadingChat, setLoadingChat] = useState(false);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [subjectId, setSubjectId] = useState("");
  const [showHistory, setShowHistory] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  useEffect(() => {
    if (!activeId) {
      setMessages([]);
      return;
    }
    setLoadingChat(true);
    api
      .get<Conversation>(`/ai/conversations/${activeId}`)
      .then((c) => setMessages(c.messages))
      .catch(() => setMessages([]))
      .finally(() => setLoadingChat(false));
  }, [activeId]);

  async function newConversation() {
    const c = await api.post<Conversation>("/ai/conversations", {
      title: "Study session",
      subject_id: subjectId || null,
    });
    await convs.reload();
    setActiveId(c.id);
    setShowHistory(false);
  }

  async function exportPdf() {
    if (!activeId) return;
    setDownloadingPdf(true);
    try {
      const token = getToken();
      const res = await fetch(`${API_BASE}/ai/conversations/${activeId}/pdf`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error("Failed to export PDF");
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Study_Notes_${activeId.slice(0, 8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("PDF download failed", err);
    } finally {
      setDownloadingPdf(false);
    }
  }

  async function sendMessage(e: FormEvent) {
    e.preventDefault();
    if (!activeId || !draft.trim()) return;
    setSending(true);
    try {
      await api.post<Message>(`/ai/conversations/${activeId}/messages`, {
        content: draft.trim(),
        use_rag: true,
        subject_id: subjectId || null,
      });
      setDraft("");
      const c = await api.get<Conversation>(`/ai/conversations/${activeId}`);
      setMessages(c.messages);
    } finally {
      setSending(false);
    }
  }

  if (convs.loading) return <LoadingState />;
  if (convs.error) return <ErrorState message={convs.error} onRetry={convs.reload} />;

  return (
    <div className="absolute inset-0 z-10 flex flex-col bg-slate-50 dark:bg-slate-900">
      <Card className="flex flex-1 flex-col overflow-hidden rounded-none border-0 shadow-none bg-transparent">
        
        {/* Chatbot Header */}
        <div className="flex items-center justify-between border-b border-slate-100 bg-white p-3 px-4 dark:border-slate-800 dark:bg-slate-900 z-20">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="rounded-md p-2 text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800 transition-colors"
              title="Toggle Chat History"
            >
              <Icon name="menu" className="h-5 w-5" />
            </button>
            <div>
              <h2 className="font-semibold text-slate-800 dark:text-slate-100">AI Tutor</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 hidden sm:block">Ask questions based on your materials</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <select
              value={subjectId}
              onChange={(e) => setSubjectId(e.target.value)}
              className="h-9 w-32 sm:w-auto rounded-lg border border-slate-200 bg-slate-50 px-3 text-xs sm:text-sm dark:border-slate-700 dark:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              <option value="">All materials</option>
              {subjects.data?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
            {activeId && messages.length > 0 && (
              <Button
                onClick={exportPdf}
                loading={downloadingPdf}
                variant="secondary"
                className="h-9 text-xs sm:text-sm px-3 flex items-center gap-1.5 border-slate-200 text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
                title="Download Study Notes as PDF"
              >
                <Icon name="download" className="h-4 w-4 text-teal-600 dark:text-teal-400" />
                <span className="hidden sm:inline">Export PDF</span>
              </Button>
            )}
            <Button onClick={newConversation} className="h-9 text-sm px-4 shadow-sm bg-[#043634] hover:bg-teal-900 text-white dark:bg-[#5eead4] dark:text-[#043634] dark:hover:bg-teal-300">
              <span>New Chat</span>
            </Button>
          </div>
        </div>

        {/* Main Body (History Panel + Chat Area) */}
        <div className="relative flex flex-1 overflow-hidden bg-slate-50/50 dark:bg-slate-950/50">
          
          {/* History Sidebar (Inside Chatbot) */}
          <div 
            className={`absolute bottom-0 left-0 top-0 z-10 w-64 md:w-72 border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 transition-transform duration-300 ease-in-out ${
              showHistory ? "translate-x-0" : "-translate-x-full"
            }`}
          >
            <div className="flex h-full flex-col">
              <div className="p-3 border-b border-slate-100 dark:border-slate-800">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">Chat History</h3>
              </div>
              <div className="flex-1 space-y-1 overflow-y-auto p-2">
                {!convs.data?.length ? (
                  <p className="px-2 py-4 text-sm text-slate-400 text-center">No previous chats.</p>
                ) : (
                  convs.data.map((c) => (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => {
                        setActiveId(c.id);
                        if (window.innerWidth < 768) setShowHistory(false);
                      }}
                      className={`w-full rounded-lg px-3 py-2.5 text-left text-sm transition-all duration-200 truncate ${
                        activeId === c.id
                          ? "bg-[#043634] text-white shadow-md dark:bg-[#5eead4] dark:text-[#043634]"
                          : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                      }`}
                    >
                      {c.title || "Study Session"}
                    </button>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Chat Content Area */}
          <div className="flex flex-1 flex-col z-0 transition-all duration-300">
            <div className="flex-1 overflow-y-auto p-4 sm:p-6">
              <div className="mx-auto flex w-full max-w-4xl flex-col space-y-6 pb-4 h-full">
                {!activeId ? (
                  <div className="flex h-full flex-col items-center justify-center text-center opacity-70">
                    <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-white border border-slate-200 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                      <Icon name="spark" className="h-8 w-8 text-[#043634] dark:text-[#5eead4]" />
                    </div>
                    <h3 className="text-xl font-semibold text-slate-800 dark:text-slate-200">How can I help you learn today?</h3>
                    <p className="mt-2 max-w-sm text-sm text-slate-500 dark:text-slate-400">
                      Select a conversation or start a new chat to begin.
                    </p>
                    <Button onClick={newConversation} className="mt-8 bg-[#043634] text-white dark:bg-[#5eead4] dark:text-[#043634]">
                      Start a New Chat
                    </Button>
                  </div>
                ) : loadingChat ? (
                  <div className="flex h-full items-center justify-center">
                    <LoadingState label="Loading messages..." />
                  </div>
                ) : (
                  <>
                    {messages.length === 0 ? (
                      <div className="flex h-full items-center justify-center text-center text-slate-500 opacity-80">
                        <p>Send your first question below.</p>
                      </div>
                    ) : (
                      messages.map((m) => (
                        <div key={m.id} className={`flex w-full ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                          {m.role === "user" ? (
                            <div className="max-w-[75%] rounded-3xl bg-slate-100 px-5 py-3 text-[15px] text-slate-800 whitespace-pre-wrap break-words dark:bg-slate-800 dark:text-slate-100">
                              {m.content}
                            </div>
                          ) : (
                            <div className="flex w-full gap-4">
                              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
                                <Icon name="spark" className="h-4 w-4 text-[#043634] dark:text-[#5eead4]" />
                              </div>
                              <div className="pt-1 w-full min-w-0 prose prose-slate dark:prose-invert max-w-none text-[15px] leading-relaxed prose-p:my-2 prose-headings:font-semibold prose-headings:my-3 prose-pre:bg-slate-800 prose-pre:text-slate-50 prose-a:text-teal-600 dark:prose-a:text-teal-400 break-words">
                                <ReactMarkdown 
                                  remarkPlugins={[remarkGfm]}
                                >
                                  {m.content}
                                </ReactMarkdown>
                              </div>
                            </div>
                          )}
                        </div>
                      ))
                    )}
                  </>
                )}
              </div>
            </div>

            {/* Message Input Area */}
            {activeId && (
              <div className="border-t border-slate-100 bg-white p-3 sm:p-4 dark:border-slate-800 dark:bg-slate-900">
                <form onSubmit={sendMessage} className="relative flex w-full max-w-4xl mx-auto items-center">
                  <div className="relative flex-1 w-full">
                    <input
                      type="text"
                      placeholder="Ask about a concept..."
                      value={draft}
                      onChange={(e) => setDraft(e.target.value)}
                      disabled={!activeId}
                      className="w-full pl-6 pr-24 py-3.5 rounded-full border border-slate-200 shadow-sm outline-none focus:ring-2 focus:ring-[#043634] dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 dark:focus:ring-[#5eead4]"
                    />
                    <Button 
                      type="submit" 
                      loading={sending} 
                      disabled={!activeId || !draft.trim()}
                      className="absolute right-2 top-1/2 -translate-y-1/2 flex h-10 w-10 items-center justify-center rounded-full p-0 bg-[#043634] text-white hover:bg-teal-900 disabled:opacity-50 dark:bg-[#5eead4] dark:text-[#043634] dark:hover:bg-teal-300"
                    >
                      {!sending && <Icon name="arrow-up" className="h-5 w-5" />}
                    </Button>
                  </div>
                </form>
                <div className="mt-2 text-center text-[10px] text-slate-400">
                  AI Tutor may produce inaccurate information about people, places, or facts.
                </div>
              </div>
            )}
          </div>

          {/* Overlay to close history on mobile */}
          {showHistory && (
            <div 
              className="absolute inset-0 z-0 bg-slate-900/10 backdrop-blur-[1px] md:hidden"
              onClick={() => setShowHistory(false)}
            />
          )}

        </div>
      </Card>
    </div>
  );
}
