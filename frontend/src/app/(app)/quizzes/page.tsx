"use client";

import { useCallback, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { useAsyncData } from "@/lib/hooks";
import { Quiz, QuizAttempt, Subject } from "@/lib/types";
import { parseQuizOptions } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ErrorState, LoadingState } from "@/components/ui/StateViews";
import { PageHeader } from "@/components/shared/PageHeader";

export default function QuizzesPage() {
  const quizLoader = useCallback(() => api.get<Quiz[]>("/quizzes"), []);
  const subjectLoader = useCallback(() => api.get<Subject[]>("/subjects"), []);
  const quizzes = useAsyncData(quizLoader, []);
  const subjects = useAsyncData(subjectLoader, []);
  const [subjectId, setSubjectId] = useState("");
  const [activeQuiz, setActiveQuiz] = useState<Quiz | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<QuizAttempt | null>(null);
  const [generating, setGenerating] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function generateQuiz() {
    setGenerating(true);
    setResult(null);
    try {
      const quiz = await api.post<Quiz>("/ai/quiz", {
        subject_id: subjectId || null,
        number_of_questions: 5,
        difficulty: "medium",
      });
      setActiveQuiz(quiz);
      setAnswers({});
      await quizzes.reload();
    } finally {
      setGenerating(false);
    }
  }

  async function openQuiz(id: string) {
    setResult(null);
    const list = quizzes.data || [];
    const found = list.find((q) => q.id === id);
    if (found && found.questions.length) {
      setActiveQuiz(found);
      return;
    }
    const all = await api.get<Quiz[]>("/quizzes");
    const q = all.find((x) => x.id === id);
    if (q) {
      const generated = await api.post<Quiz>("/ai/quiz", {
        subject_id: q.subject_id,
        number_of_questions: q.question_count,
        difficulty: q.difficulty,
      });
      setActiveQuiz(generated);
    }
  }

  async function submitQuiz() {
    if (!activeQuiz) return;
    setSubmitting(true);
    try {
      const attempt = await api.post<QuizAttempt>(`/quizzes/${activeQuiz.id}/submit`, {
        answers: activeQuiz.questions.map((q) => ({
          question_id: q.id,
          user_answer: answers[q.id] || "",
        })),
      });
      setResult(attempt);
    } finally {
      setSubmitting(false);
    }
  }

  const optionsByQuestion = useMemo(() => {
    if (!activeQuiz) return {};
    return Object.fromEntries(
      activeQuiz.questions.map((q) => [q.id, parseQuizOptions(q.options_json)])
    );
  }, [activeQuiz]);

  if (quizzes.loading) return <LoadingState />;
  if (quizzes.error) return <ErrorState message={quizzes.error} onRetry={quizzes.reload} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Quizzes"
        description="Adaptive practice quizzes with instant scoring."
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
            <Button onClick={generateQuiz} loading={generating}>
              Generate quiz
            </Button>
          </div>
        }
      />

      {activeQuiz && (
        <Card>
          <CardHeader title={activeQuiz.title} description={`${activeQuiz.question_count} questions`} />
          <CardBody className="space-y-4">
            {activeQuiz.questions.map((q, idx) => (
              <div key={q.id} className="space-y-2 rounded-lg border border-slate-200/80 p-3 dark:border-slate-800">
                <p className="text-sm font-medium">
                  {idx + 1}. {q.prompt}
                </p>
                {(optionsByQuestion[q.id]?.length ? optionsByQuestion[q.id] : ["A", "B", "C", "D"]).map(
                  (opt) => (
                    <label key={opt} className="flex items-center gap-2 text-sm">
                      <input
                        type="radio"
                        name={q.id}
                        checked={answers[q.id] === opt}
                        onChange={() => setAnswers((a) => ({ ...a, [q.id]: opt }))}
                      />
                      {opt}
                    </label>
                  )
                )}
              </div>
            ))}
            <Button onClick={submitQuiz} loading={submitting}>
              Submit answers
            </Button>
            {result && (
              <p className="text-sm font-medium text-teal-800 dark:text-teal-200">
                Score: {result.percentage.toFixed(0)}% ({result.score}/{result.max_score})
              </p>
            )}
          </CardBody>
        </Card>
      )}

      <Card>
        <CardHeader title="Recent quizzes" />
        <CardBody className="space-y-2">
          {!quizzes.data?.length ? (
            <p className="text-sm text-muted">No quizzes yet.</p>
          ) : (
            quizzes.data.map((q) => (
              <div
                key={q.id}
                className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-900/60"
              >
                <div>
                  <p className="font-medium">{q.title}</p>
                  <p className="text-xs text-muted">{q.question_count} questions</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge>{q.difficulty}</Badge>
                  <Button size="sm" variant="secondary" onClick={() => openQuiz(q.id)}>
                    Open
                  </Button>
                </div>
              </div>
            ))
          )}
        </CardBody>
      </Card>
    </div>
  );
}
