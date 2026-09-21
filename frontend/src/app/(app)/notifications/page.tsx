"use client";

import { useCallback } from "react";
import { api } from "@/lib/api";
import { useAsyncData } from "@/lib/hooks";
import { Notification } from "@/lib/types";
import { formatDateTime } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { ErrorState, LoadingState } from "@/components/ui/StateViews";
import { PageHeader } from "@/components/shared/PageHeader";

export default function NotificationsPage() {
  const loader = useCallback(() => api.get<Notification[]>("/notifications"), []);
  const { data, loading, error, reload } = useAsyncData(loader, []);

  async function markRead(id: string) {
    await api.post(`/notifications/${id}/read`);
    reload();
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={reload} />;

  return (
    <div>
      <PageHeader title="Notifications" description="Reminders, deadlines, and study nudges." />

      {!data?.length ? (
        <Card>
          <CardBody className="py-10 text-center text-sm text-muted">You&apos;re all caught up.</CardBody>
        </Card>
      ) : (
        <div className="space-y-2">
          {data.map((n) => (
            <Card key={n.id} className={!n.is_read ? "border-teal-600/30" : undefined}>
              <CardBody className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium">{n.title}</h3>
                    <Badge tone="neutral">{n.category}</Badge>
                  </div>
                  <p className="mt-1 text-sm text-muted">{n.body}</p>
                  <p className="mt-2 text-xs text-muted">{formatDateTime(n.created_at)}</p>
                </div>
                {!n.is_read && (
                  <Button size="sm" variant="secondary" onClick={() => markRead(n.id)}>
                    Mark read
                  </Button>
                )}
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
