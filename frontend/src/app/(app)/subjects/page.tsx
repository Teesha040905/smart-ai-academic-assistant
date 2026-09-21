"use client";

import Link from "next/link";
import { FormEvent, useCallback, useState } from "react";
import { api } from "@/lib/api";
import { useAsyncData } from "@/lib/hooks";
import { Subject } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { ErrorState, LoadingState } from "@/components/ui/StateViews";
import { PageHeader } from "@/components/shared/PageHeader";

export default function SubjectsPage() {
  const loader = useCallback(() => api.get<Subject[]>("/subjects"), []);
  const { data, loading, error, reload } = useAsyncData(loader, []);
  const [name, setName] = useState("");
  const [creating, setCreating] = useState(false);

  async function createSubject(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setCreating(true);
    try {
      await api.post("/subjects", { name: name.trim(), color: "#0f766e" });
      setName("");
      await reload();
    } finally {
      setCreating(false);
    }
  }

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={reload} />;

  return (
    <div>
      <PageHeader
        title="Subjects"
        description="Organize courses, units, and topics."
        action={
          <form onSubmit={createSubject} className="flex gap-2">
            <Input
              placeholder="New subject name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-48"
            />
            <Button type="submit" loading={creating}>
              Add
            </Button>
          </form>
        }
      />
      {!data?.length ? (
        <Card>
          <CardBody className="py-10 text-center text-sm text-muted">
            No subjects yet. Add your first course above.
          </CardBody>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {data.map((subject) => (
            <Link key={subject.id} href={`/subjects/${subject.id}`}>
              <Card className="h-full transition hover:border-teal-600/40">
                <CardBody className="space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h3 className="font-serif text-lg font-semibold">{subject.name}</h3>
                      {subject.code && (
                        <p className="text-xs text-muted">{subject.code}</p>
                      )}
                    </div>
                    <span
                      className="mt-1 h-3 w-3 rounded-full"
                      style={{ backgroundColor: subject.color }}
                    />
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Badge tone="teal">{Math.round(subject.progress)}% progress</Badge>
                    <Badge>{subject.priority}</Badge>
                  </div>
                  {subject.exam_date && (
                    <p className="text-xs text-muted">Exam {formatDate(subject.exam_date)}</p>
                  )}
                </CardBody>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
