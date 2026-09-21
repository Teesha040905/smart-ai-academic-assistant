"use client";

import { useCallback, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { useAsyncData } from "@/lib/hooks";
import { Flashcard, Subject } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ErrorState, LoadingState } from "@/components/ui/StateViews";
import { PageHeader } from "@/components/shared/PageHeader";

export default function FlashcardsPage() {
  const cardsLoader = useCallback(() => api.get<Flashcard[]>("/flashcards"), []);
  const subjectLoader = useCallback(() => api.get<Subject[]>("/subjects"), []);
  const cards = useAsyncData(cardsLoader, []);
  const subjects = useAsyncData(subjectLoader, []);
  const [subjectId, setSubjectId] = useState("");
  const [index, setIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [generating, setGenerating] = useState(false);

  const deck = cards.data || [];
  const current = deck[index];

  const subjectName = useMemo(() => {
    if (!current?.subject_id) return null;
    return subjects.data?.find((s) => s.id === current.subject_id)?.name;
  }, [current, subjects.data]);

  async function generate() {
    setGenerating(true);
    try {
      await api.post("/ai/flashcards", {
        subject_id: subjectId || null,
        count: 10,
      });
      await cards.reload();
      setIndex(0);
      setRevealed(false);
    } finally {
      setGenerating(false);
    }
  }

  async function review(rating: "easy" | "medium" | "hard") {
    if (!current) return;
    await api.post(`/flashcards/${current.id}/review`, { rating });
    setRevealed(false);
    setIndex((i) => (i + 1 >= deck.length ? 0 : i + 1));
    await cards.reload();
  }

  if (cards.loading) return <LoadingState />;
  if (cards.error) return <ErrorState message={cards.error} onRetry={cards.reload} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Flashcards"
        description="Spaced repetition review for key concepts."
        action={
          <div className="flex gap-2">
            <select
              value={subjectId}
              onChange={(e) => setSubjectId(e.target.value)}
              className="h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm dark:border-slate-700 dark:bg-slate-900"
            >
              <option value="">Any subject</option>
              {subjects.data?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
            <Button onClick={generate} loading={generating}>
              Generate deck
            </Button>
          </div>
        }
      />

      <Card>
        <CardHeader
          title="Review"
          description={
            deck.length ? `Card ${index + 1} of ${deck.length}${subjectName ? ` · ${subjectName}` : ""}` : "Empty deck"
          }
        />
        <CardBody className="space-y-4">
          {!current ? (
            <p className="text-sm text-muted">Generate flashcards to start reviewing.</p>
          ) : (
            <>
              <div className="min-h-[10rem] rounded-xl border border-dashed border-slate-300 p-6 dark:border-slate-700">
                <p className="text-sm text-muted">Question</p>
                <p className="mt-2 font-serif text-xl">{current.question}</p>
                {revealed && (
                  <>
                    <p className="mt-6 text-sm text-muted">Answer</p>
                    <p className="mt-2 text-base">{current.answer}</p>
                  </>
                )}
              </div>
              {!revealed ? (
                <Button onClick={() => setRevealed(true)}>Reveal answer</Button>
              ) : (
                <div className="flex flex-wrap gap-2">
                  <Button variant="secondary" onClick={() => review("hard")}>
                    Hard
                  </Button>
                  <Button variant="secondary" onClick={() => review("medium")}>
                    Medium
                  </Button>
                  <Button onClick={() => review("easy")}>Easy</Button>
                </div>
              )}
            </>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
