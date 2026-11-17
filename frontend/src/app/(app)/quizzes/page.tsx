"use client";

import { useCallback, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { useAsyncData } from "@/lib/hooks";
import { Quiz, QuizAnswerReview, QuizAttempt, Subject } from "@/lib/types";
import { cn, parseQuizOptions } from "@/lib/utils";
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

  const reviewByQuestion = useMemo(
    () =>
      Object.fromEntries((result?.review ?? []).map((r) => [r.question_id, r])) as Record<
        string,
        QuizAnswerReview
      >,
    [result]
  );

  function retake() {
    setResult(null);
    setAnswers({});
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
            {result && (
              <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg bg-teal-50 px-4 py-3 dark:bg-teal-950/40">
                <p className="text-sm font-semibold text-teal-900 dark:text-teal-100">
                  Score: {result.percentage.toFixed(0)}% ({result.score}/{result.max_score} correct)
                </p>
                <Button size="sm" variant="secondary" onClick={retake}>
                  Retake
                </Button>
              </div>
            )}
            {activeQuiz.questions.map((q, idx) => {
              const review = reviewByQuestion[q.id];
              const answered = !!review?.user_answer;
              return (
                <div
                  key={q.id}
                  className={cn(
                    "space-y-2 rounded-lg border p-3",
                    !review && "border-slate-200/80 dark:border-slate-800",
                    review?.is_correct && "border-green-300 dark:border-green-800",
                    review && !review.is_correct && "border-red-300 dark:border-red-800"
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-medium">
                      {idx + 1}. {q.prompt}
                    </p>
                    {review && (
                      <Badge tone={review.is_correct ? "green" : "red"}>
                        {review.is_correct ? "Correct" : answered ? "Incorrect" : "Not answered"}
                      </Badge>
                    )}
                  </div>
                  {(optionsByQuestion[q.id]?.length ? optionsByQuestion[q.id] : ["A", "B", "C", "D"]).map(
                    (opt) => {
                      const isCorrectOption = review && opt === review.correct_answer;
                      const isWrongPick = review && !review.is_correct && opt === review.user_answer;
                      return (
                        <label
                          key={opt}
                          className={cn(
                            "flex items-center gap-2 rounded-md px-2 py-1 text-sm",
                            isCorrectOption && "bg-green-50 font-medium text-green-800 dark:bg-green-950/40 dark:text-green-300",
                            isWrongPick && "bg-red-50 text-red-700 line-through dark:bg-red-950/40 dark:text-red-300"
                          )}
                        >
                          <input
                            type="radio"
                            name={q.id}
                            checked={answers[q.id] === opt}
                            disabled={!!result}
                            onChange={() => setAnswers((a) => ({ ...a, [q.id]: opt }))}
                          />
                          <span className="flex-1">{opt}</span>
                          {isCorrectOption && <span aria-label="Correct answer">✓</span>}
                          {isWrongPick && <span aria-label="Your answer">✗</span>}
                        </label>
                      );
                    }
                  )}
                  {review && !optionsByQuestion[q.id]?.length && !review.is_correct && (
                    <p className="text-sm text-green-800 dark:text-green-300">
                      Correct answer: {review.correct_answer}
                    </p>
                  )}
                  {review?.explanation && (
                    <p className="rounded-md bg-slate-50 px-3 py-2 text-xs text-slate-600 dark:bg-slate-900/60 dark:text-slate-300">
                      {review.explanation}
                    </p>
                  )}
                </div>
              );
            })}
            {!result && (
              <Button onClick={submitQuiz} loading={submitting}>
                Submit answers
              </Button>
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
