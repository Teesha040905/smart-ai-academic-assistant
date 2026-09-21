"use client";

import { useCallback } from "react";
import { api } from "@/lib/api";
import { useAsyncData } from "@/lib/hooks";
import { KnowledgeMap } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ErrorState, LoadingState } from "@/components/ui/StateViews";
import { PageHeader } from "@/components/shared/PageHeader";

export default function KnowledgeMapPage() {
  const loader = useCallback(() => api.get<KnowledgeMap>("/knowledge-map"), []);
  const { data, loading, error, reload } = useAsyncData(loader, []);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={reload} />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Knowledge map"
        description="Visual overview of mastery across subjects and topics."
      />

      {!data?.subjects?.length ? (
        <Card>
          <CardBody className="py-10 text-center text-sm text-muted">
            Add subjects and track topics to build your map.
          </CardBody>
        </Card>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {data.subjects.map((subject, idx) => {
            const topics = (subject.topics as Record<string, unknown>[] | undefined) || [];
            return (
              <Card key={String(subject.id ?? idx)}>
                <CardHeader
                  title={String(subject.name ?? "Subject")}
                  description={`${topics.length} topics`}
                />
                <CardBody className="space-y-2">
                  {topics.length === 0 ? (
                    <p className="text-sm text-muted">No topics mapped.</p>
                  ) : (
                    topics.map((t, i) => (
                      <div
                        key={String(t.id ?? i)}
                        className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm dark:bg-slate-900/60"
                      >
                        <span>{String(t.name ?? "Topic")}</span>
                        <Badge tone="teal">
                          {Math.round(Number(t.knowledge_level ?? 0))}%
                        </Badge>
                      </div>
                    ))
                  )}
                </CardBody>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
