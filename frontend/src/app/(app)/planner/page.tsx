"use client";

import { useCallback, useState } from "react";
import { api } from "@/lib/api";
import { useAsyncData } from "@/lib/hooks";
import { StudyPlan, StudySession } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ErrorState, LoadingState } from "@/components/ui/StateViews";
import { PageHeader } from "@/components/shared/PageHeader";

export default function PlannerPage() {
  const planLoader = useCallback(() => api.get<StudyPlan | null>("/study-plans/active"), []);
  const todayLoader = useCallback(() => api.get<StudySession[]>("/study-sessions/today"), []);
  const plan = useAsyncData(planLoader, []);
  const today = useAsyncData(todayLoader, []);
  const [generating, setGenerating] = useState(false);

  async function generatePlan() {
    setGenerating(true);
    try {
      await api.post("/study-plans/generate", { days: 7, prefer_weak_topics: true });
      await Promise.all([plan.reload(), today.reload()]);
    } finally {
      setGenerating(false);
    }
  }

  async function completeSession(id: string) {
    await api.post(`/study-sessions/${id}/complete`);
    await Promise.all([plan.reload(), today.reload()]);
  }

  if (plan.loading || today.loading) return <LoadingState />;
  if (plan.error) return <ErrorState message={plan.error} onRetry={plan.reload} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Study planner"
        description="AI-generated schedule adapted to weak topics and exams."
        action={
          <Button onClick={generatePlan} loading={generating}>
            Generate 7-day plan
          </Button>
        }
      />

      <Card>
        <CardHeader title="Today" />
        <CardBody className="space-y-2">
          {!today.data?.length ? (
            <p className="text-sm text-muted">No sessions scheduled for today.</p>
          ) : (
            today.data.map((s) => (
              <div
                key={s.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-200/80 px-3 py-2 dark:border-slate-800"
              >
                <div>
                  <p className="font-medium">{s.title}</p>
                  <p className="text-xs text-muted">
                    {s.duration_minutes} min · {s.activity_type}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge tone={s.status === "completed" ? "green" : "teal"}>{s.status}</Badge>
                  {s.status !== "completed" && (
                    <Button size="sm" variant="secondary" onClick={() => completeSession(s.id)}>
                      Complete
                    </Button>
                  )}
                </div>
              </div>
            ))
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader
          title={plan.data?.title || "Active plan"}
          description={
            plan.data
              ? `${formatDate(plan.data.start_date)} – ${formatDate(plan.data.end_date)}`
              : "No active plan"
          }
        />
        <CardBody className="space-y-2">
          {!plan.data?.sessions?.length ? (
            <p className="text-sm text-muted">Generate a plan to see upcoming sessions.</p>
          ) : (
            plan.data.sessions.slice(0, 20).map((s) => (
              <div
                key={s.id}
                className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm dark:bg-slate-900/60"
              >
                <span>
                  {formatDate(s.scheduled_date)} · {s.title}
                </span>
                <Badge>{s.status}</Badge>
              </div>
            ))
          )}
        </CardBody>
      </Card>
    </div>
  );
}
