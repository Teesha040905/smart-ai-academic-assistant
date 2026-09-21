"use client";

import Link from "next/link";
import { useCallback } from "react";
import { api } from "@/lib/api";
import { useAsyncData } from "@/lib/hooks";
import { Dashboard } from "@/lib/types";
import { formatDate, statLabel } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "@/components/ui/StateViews";
import { PageHeader } from "@/components/shared/PageHeader";

export default function DashboardPage() {
  const loader = useCallback(() => api.get<Dashboard>("/dashboard"), []);
  const { data, loading, error, reload } = useAsyncData(loader, []);

  if (loading) return <LoadingState label="Loading dashboard…" />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!data) return <EmptyState title="No dashboard data" />;

  const stats = Object.entries(data.stats || {});

  return (
    <div className="space-y-6">
      <PageHeader
        title={`${data.greeting}, ${data.student_name}`}
        description="Your study overview for today."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.slice(0, 4).map(([key, value]) => (
          <Card key={key}>
            <CardBody>
              <p className="text-xs uppercase tracking-wide text-muted">
                {statLabel(key)}
              </p>
              <p className="mt-2 font-serif text-2xl font-semibold">
                {String(value)}
              </p>
            </CardBody>
          </Card>
        ))}
        {stats.length === 0 && (
          <Card className="sm:col-span-2 xl:col-span-4">
            <CardBody>
              <p className="text-sm text-muted">Stats will appear as you study.</p>
            </CardBody>
          </Card>
        )}
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader title="Today's plan" description="Scheduled study sessions" />
          <CardBody className="space-y-3">
            {data.today_plan.length === 0 ? (
              <EmptyState
                title="No sessions today"
                description="Generate a study plan to schedule focused blocks."
                action={
                  <Link href="/planner">
                    <Button size="sm">Open planner</Button>
                  </Link>
                }
              />
            ) : (
              data.today_plan.map((session) => (
                <div
                  key={session.id}
                  className="flex items-center justify-between rounded-lg border border-slate-200/80 px-3 py-2 dark:border-slate-800"
                >
                  <div>
                    <p className="font-medium">{session.title}</p>
                    <p className="text-xs text-muted">
                      {session.duration_minutes} min · {session.activity_type}
                    </p>
                  </div>
                  <Badge tone={session.status === "completed" ? "green" : "teal"}>
                    {session.status.replace("_", " ")}
                  </Badge>
                </div>
              ))
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Study streak" />
          <CardBody>
            <p className="font-serif text-3xl font-semibold">
              {String(data.streak?.current ?? data.streak?.days ?? "—")}
            </p>
            <p className="mt-1 text-sm text-muted">Consecutive study days</p>
          </CardBody>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Weak topics" />
          <CardBody className="space-y-2">
            {data.weak_topics.length === 0 ? (
              <p className="text-sm text-muted">No weak topics flagged yet.</p>
            ) : (
              data.weak_topics.slice(0, 6).map((topic, i) => (
                <div
                  key={String(topic.id ?? i)}
                  className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-900/60"
                >
                  <span className="text-sm font-medium">
                    {String(topic.name ?? topic.title ?? "Topic")}
                  </span>
                  {"knowledge_level" in topic && (
                    <Badge tone="amber">{String(topic.knowledge_level)}%</Badge>
                  )}
                </div>
              ))
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader
            title="AI recommendation"
            action={
              <Link href="/recommendations">
                <Button variant="ghost" size="sm">
                  View all
                </Button>
              </Link>
            }
          />
          <CardBody>
            {!data.recommendation ? (
              <EmptyState
                title="No recommendation yet"
                description="Complete quizzes or upload materials to get personalized tips."
              />
            ) : (
              <div className="space-y-2">
                <p className="font-medium">{data.recommendation.title}</p>
                <p className="text-sm text-muted">{data.recommendation.reason}</p>
                <Badge tone="teal">{data.recommendation.priority} priority</Badge>
              </div>
            )}
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader title="Upcoming exams" />
        <CardBody className="space-y-3">
          {data.upcoming_exams.length === 0 ? (
            <EmptyState title="No exams scheduled" description="Add exams from subjects or planner." />
          ) : (
            data.upcoming_exams.map((exam) => (
              <div
                key={exam.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-200/80 px-3 py-2 dark:border-slate-800"
              >
                <div>
                  <p className="font-medium">{exam.name}</p>
                  <p className="text-xs text-muted">{formatDate(exam.exam_date)}</p>
                </div>
                <div className="flex items-center gap-2">
                  {exam.days_remaining != null && (
                    <Badge tone="amber">{exam.days_remaining} days</Badge>
                  )}
                  <Badge>{exam.priority}</Badge>
                </div>
              </div>
            ))
          )}
        </CardBody>
      </Card>
    </div>
  );
}
