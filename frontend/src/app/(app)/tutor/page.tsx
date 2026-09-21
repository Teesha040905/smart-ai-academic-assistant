"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAsyncData } from "@/lib/hooks";
import { Conversation, Message, Subject } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { ErrorState, LoadingState } from "@/components/ui/StateViews";
import { PageHeader } from "@/components/shared/PageHeader";

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
    <div className="space-y-4">
      <PageHeader
        title="AI Tutor"
        description="Ask questions grounded in your uploaded materials."
        action={
          <div className="flex gap-2">
            <select
              value={subjectId}
              onChange={(e) => setSubjectId(e.target.value)}
              className="h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm dark:border-slate-700 dark:bg-slate-900"
            >
              <option value="">All materials</option>
              {subjects.data?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
            <Button onClick={newConversation}>New chat</Button>
          </div>
        }
      />

      <div className="grid gap-4 lg:grid-cols-[240px_1fr]">
        <Card className="h-fit">
          <CardHeader title="Conversations" />
          <CardBody className="space-y-1 p-2">
            {!convs.data?.length ? (
              <p className="px-2 py-4 text-sm text-muted">Start a new chat.</p>
            ) : (
              convs.data.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => setActiveId(c.id)}
                  className={`w-full rounded-lg px-3 py-2 text-left text-sm ${
                    activeId === c.id
                      ? "bg-teal-50 text-teal-900 dark:bg-teal-950/50 dark:text-teal-100"
                      : "hover:bg-slate-100 dark:hover:bg-slate-800"
                  }`}
                >
                  {c.title}
                </button>
              ))
            )}
          </CardBody>
        </Card>

        <Card className="flex min-h-[28rem] flex-col">
          <CardHeader title="Chat" />
          <CardBody className="flex flex-1 flex-col gap-3">
            {!activeId ? (
              <p className="text-sm text-muted">Select or create a conversation.</p>
            ) : loadingChat ? (
              <LoadingState label="Loading messages…" />
            ) : (
              <div className="flex-1 space-y-3 overflow-y-auto pr-1">
                {messages.length === 0 ? (
                  <p className="text-sm text-muted">Send your first question.</p>
                ) : (
                  messages.map((m) => (
                    <div
                      key={m.id}
                      className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
                        m.role === "user"
                          ? "ml-auto bg-teal-700 text-white"
                          : "bg-slate-100 dark:bg-slate-800"
                      }`}
                    >
                      {m.content}
                    </div>
                  ))
                )}
              </div>
            )}
            <form onSubmit={sendMessage} className="flex gap-2">
              <Input
                placeholder="Ask about a concept…"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                disabled={!activeId}
              />
              <Button type="submit" loading={sending} disabled={!activeId}>
                Send
              </Button>
            </form>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
