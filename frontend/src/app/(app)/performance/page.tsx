"use client";

import { useCallback } from "react";
import { api } from "@/lib/api";
import { useAsyncData } from "@/lib/hooks";
import { Analytics } from "@/lib/types";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ErrorState, LoadingState } from "@/components/ui/StateViews";
import { PageHeader } from "@/components/shared/PageHeader";

export default function PerformancePage() {
  const loader = useCallback(() => api.get<Analytics>("/performance"), []);
  const { data, loading, error, reload } = useAsyncData(loader, []);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!data) return null;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Performance"
        description="Progress, quiz averages, and study consistency."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          ["Overall progress", `${Math.round(data.overall_progress)}%`],
          ["Study hours", data.study_hours.toFixed(1)],
          ["Quiz average", `${Math.round(data.quiz_average)}%`],
          ["Consistency", `${Math.round(data.study_consistency)}%`],
        ].map(([label, value]) => (
          <Card key={label}>
            <CardBody>
              <p className="text-xs uppercase tracking-wide text-muted">{label}</p>
              <p className="mt-2 font-serif text-2xl font-semibold">{value}</p>
            </CardBody>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Subject performance" />
          <CardBody className="space-y-2">
            {data.subject_performance.length === 0 ? (
              <p className="text-sm text-muted">No subject data yet.</p>
            ) : (
              data.subject_performance.map((row, i) => (
                <div key={i} className="flex justify-between text-sm">
                  <span>{String(row.name ?? row.subject ?? "Subject")}</span>
                  <span className="font-medium">{String(row.progress ?? row.score ?? "—")}</span>
                </div>
              ))
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Topic performance" />
          <CardBody className="space-y-2 max-h-80 overflow-y-auto">
            {data.topic_performance.length === 0 ? (
              <p className="text-sm text-muted">Complete topics and quizzes to see breakdowns.</p>
            ) : (
              data.topic_performance.slice(0, 12).map((row, i) => (
                <div key={i} className="flex justify-between gap-3 text-sm">
                  <span className="truncate">{String(row.name ?? row.topic ?? "Topic")}</span>
                  <span className="shrink-0 font-medium">
                    {String(row.knowledge_level ?? row.score ?? "—")}
                  </span>
                </div>
              ))
            )}
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader title="Weekly progress" />
        <CardBody className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {data.weekly_progress.length === 0 ? (
            <p className="text-sm text-muted">No weekly history yet.</p>
          ) : (
            data.weekly_progress.map((w, i) => (
              <div key={i} className="rounded-lg bg-slate-50 p-3 text-sm dark:bg-slate-900/60">
                <p className="text-muted">{String(w.label ?? w.week ?? `Week ${i + 1}`)}</p>
                <p className="mt-1 font-medium">{String(w.value ?? w.hours ?? w.progress ?? "—")}</p>
              </div>
            ))
          )}
        </CardBody>
      </Card>
    </div>
  );
}
