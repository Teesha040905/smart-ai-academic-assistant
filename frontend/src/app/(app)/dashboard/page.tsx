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
import { DashboardChart } from "@/components/dashboard/DashboardChart";
import {
  EmptyState,
  ErrorState,
  LoadingState,
} from "@/components/ui/StateViews";
import { PageHeader } from "@/components/shared/PageHeader";

export default function DashboardPage() {
  const loader = useCallback(() => api.get<Dashboard>("/dashboard"), []);
  const { data, loading, error, reload } = useAsyncData(loader, []);

  if (loading) return <LoadingState label="Loading dashboard..." />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!data) return <EmptyState title="No dashboard data" />;

  const stats = Object.entries(data.stats || {});
  const streak = Number(data.streak?.streak_days ?? 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title={`${data.greeting}, ${data.student_name} 👋`}
        description="Here is your study overview for today."
      />

      {/* STATS & STREAK */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <Card className="sm:col-span-2 xl:col-span-1 bg-gradient-to-br from-orange-400 to-red-500 text-white border-none shadow-lg">
          <CardBody className="flex items-center justify-between h-full p-4">
            <div>
              <p className="text-sm font-medium opacity-90">Day Streak</p>
              <p className="font-serif text-3xl font-bold mt-0.5">{streak}</p>
            </div>
            <span className="text-4xl drop-shadow-md">🔥</span>
          </CardBody>
        </Card>
        
        {stats.slice(0, 4).map(([key, value]) => (
          <Card key={key}>
            <CardBody className="flex flex-col justify-center h-full p-4">
              <p className="text-xs uppercase tracking-wide text-muted">
                {statLabel(key)}
              </p>
              <p className="mt-0.5 font-serif text-2xl font-semibold">
                {String(value)}
              </p>
            </CardBody>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        {/* CHART & WEAK TOPICS PROGRESS */}
        <Card className="xl:col-span-2">
          <CardHeader title="Knowledge Progress" description="Your weakest topics needing review" />
          <CardBody>
            {data.weak_topics && data.weak_topics.length > 0 ? (
              <>
                <div className="space-y-4 mb-6">
                  {data.weak_topics.slice(0, 3).map((topic) => (
                    <div key={String(topic.id)} className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span className="font-medium">{String(topic.name)}</span>
                        <span className="font-semibold">{Number(topic.knowledge_level)}%</span>
                      </div>
                      <div className="h-2.5 w-full bg-slate-100 rounded-full overflow-hidden dark:bg-slate-800">
                        <div 
                          className={`h-full rounded-full ${Number(topic.knowledge_level) < 50 ? 'bg-red-500' : Number(topic.knowledge_level) < 75 ? 'bg-amber-500' : 'bg-emerald-500'}`} 
                          style={{ width: `${Math.max(5, Number(topic.knowledge_level))}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
                <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 border-t pt-4">Knowledge Chart</h4>
                <DashboardChart data={data.weak_topics} />
              </>
            ) : (
              <EmptyState title="No data yet" description="Start taking quizzes to see your knowledge progress." />
            )}
          </CardBody>
        </Card>

        {/* RECOMMENDATIONS & EXAMS */}
        <div className="space-y-4">
          <Card>
            <CardHeader title="AI Recommendation" />
            <CardBody>
              {!data.recommendation ? (
                <EmptyState
                  title="No recommendation"
                  description="Complete quizzes to get personalized tips."
                />
              ) : (
                <div className="space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <p className="font-medium">{data.recommendation.title}</p>
                    <Badge tone="teal">{data.recommendation.priority}</Badge>
                  </div>
                  <p className="text-sm text-muted">{data.recommendation.reason}</p>
                  <Link href="/planner">
                    <Button size="sm" className="w-full mt-2">Open Planner</Button>
                  </Link>
                </div>
              )}
            </CardBody>
          </Card>

          <Card>
            <CardHeader title="Upcoming exams" />
            <CardBody className="space-y-3">
              {data.upcoming_exams.length === 0 ? (
                <EmptyState title="No exams scheduled" />
              ) : (
                data.upcoming_exams.map((exam) => (
                  <div
                    key={exam.id}
                    className="flex flex-col gap-1 rounded-lg border border-slate-200/80 px-3 py-2 dark:border-slate-800"
                  >
                    <div className="flex justify-between">
                      <p className="font-medium text-sm">{exam.name}</p>
                      {exam.days_remaining != null && (
                        <Badge tone="amber">{exam.days_remaining}d</Badge>
                      )}
                    </div>
                    <p className="text-xs text-muted">{formatDate(exam.exam_date)}</p>
                  </div>
                ))
              )}
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}
