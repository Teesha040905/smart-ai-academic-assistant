"use client";

import { useCallback, useState } from "react";
import { api } from "@/lib/api";
import { useAsyncData } from "@/lib/hooks";
import { Recommendation } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { ErrorState, LoadingState } from "@/components/ui/StateViews";
import { PageHeader } from "@/components/shared/PageHeader";

export default function RecommendationsPage() {
  const loader = useCallback(() => api.get<Recommendation[]>("/recommendations"), []);
  const { data, loading, error, reload } = useAsyncData(loader, []);
  const [refreshing, setRefreshing] = useState(false);

  async function refresh() {
    setRefreshing(true);
    try {
      await api.get<Recommendation[]>("/recommendations?refresh=true");
      await reload();
    } finally {
      setRefreshing(false);
    }
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={reload} />;

  return (
    <div>
      <PageHeader
        title="Recommendations"
        description="Personalized next steps based on weak topics and deadlines."
        action={
          <Button variant="secondary" onClick={refresh} loading={refreshing}>
            Refresh
          </Button>
        }
      />

      {!data?.length ? (
        <Card>
          <CardBody className="py-10 text-center text-sm text-muted">
            No recommendations yet. Upload materials or take a quiz.
          </CardBody>
        </Card>
      ) : (
        <div className="space-y-3">
          {data.map((rec) => (
            <Card key={rec.id}>
              <CardBody className="space-y-2">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <h3 className="font-serif text-lg font-semibold">{rec.title}</h3>
                  <Badge tone="teal">{rec.priority} · {rec.score.toFixed(0)}</Badge>
                </div>
                <p className="text-sm text-muted">{rec.reason}</p>
                {rec.suggested_actions?.length > 0 && (
                  <ul className="list-disc space-y-1 pl-5 text-sm">
                    {rec.suggested_actions.map((action, i) => (
                      <li key={i}>{String(action.label ?? action.action ?? JSON.stringify(action))}</li>
                    ))}
                  </ul>
                )}
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
