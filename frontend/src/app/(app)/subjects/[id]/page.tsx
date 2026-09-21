"use client";

import { FormEvent, useCallback, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { useAsyncData } from "@/lib/hooks";
import { Subject } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { ErrorState, LoadingState } from "@/components/ui/StateViews";
import { PageHeader } from "@/components/shared/PageHeader";

export default function SubjectDetailPage() {
  const params = useParams();
  const id = String(params.id);
  const loader = useCallback(() => api.get<Subject>(`/subjects/${id}`), [id]);
  const { data, loading, error, reload } = useAsyncData(loader, [id]);
  const [topicName, setTopicName] = useState("");
  const [unitName, setUnitName] = useState("");
  const [busy, setBusy] = useState(false);

  async function addTopic(e: FormEvent) {
    e.preventDefault();
    if (!topicName.trim()) return;
    setBusy(true);
    try {
      await api.post(`/subjects/${id}/topics`, { name: topicName.trim() });
      setTopicName("");
      await reload();
    } finally {
      setBusy(false);
    }
  }

  async function addUnit(e: FormEvent) {
    e.preventDefault();
    if (!unitName.trim()) return;
    setBusy(true);
    try {
      await api.post(`/subjects/${id}/units`, {
        name: unitName.trim(),
        order_index: data?.units.length ?? 0,
      });
      setUnitName("");
      await reload();
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!data) return null;

  const flatTopics = [
    ...data.topics,
    ...data.units.flatMap((u) => u.topics),
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title={data.name}
        description={data.description || "Subject details, units, and topics."}
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Units" />
          <CardBody className="space-y-3">
            <form onSubmit={addUnit} className="flex gap-2">
              <Input
                placeholder="Unit name"
                value={unitName}
                onChange={(e) => setUnitName(e.target.value)}
              />
              <Button type="submit" loading={busy}>
                Add
              </Button>
            </form>
            {data.units.length === 0 ? (
              <p className="text-sm text-muted">No units yet.</p>
            ) : (
              data.units.map((unit) => (
                <div key={unit.id} className="rounded-lg border border-slate-200/80 p-3 dark:border-slate-800">
                  <div className="flex items-center justify-between">
                    <p className="font-medium">{unit.name}</p>
                    <Badge tone="teal">{Math.round(unit.progress)}%</Badge>
                  </div>
                  <p className="mt-1 text-xs text-muted">{unit.topics.length} topics</p>
                </div>
              ))
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Topics" />
          <CardBody className="space-y-3">
            <form onSubmit={addTopic} className="flex gap-2">
              <Input
                placeholder="Topic name"
                value={topicName}
                onChange={(e) => setTopicName(e.target.value)}
              />
              <Button type="submit" loading={busy}>
                Add
              </Button>
            </form>
            {flatTopics.length === 0 ? (
              <p className="text-sm text-muted">No topics yet.</p>
            ) : (
              flatTopics.map((topic) => (
                <div
                  key={topic.id}
                  className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-900/60"
                >
                  <div>
                    <p className="text-sm font-medium">{topic.name}</p>
                    <p className="text-xs text-muted capitalize">{topic.status.replace("_", " ")}</p>
                  </div>
                  <Badge tone="amber">{Math.round(topic.knowledge_level)}%</Badge>
                </div>
              ))
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
