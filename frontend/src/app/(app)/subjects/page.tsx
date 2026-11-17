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
import { Icon } from "@/components/ui/Icon";
import { Input } from "@/components/ui/Input";
import { ErrorState, LoadingState } from "@/components/ui/StateViews";
import { PageHeader } from "@/components/shared/PageHeader";

// Mirrors validate_subject_name in backend/app/schemas
function subjectNameError(value: string): string | null {
  const name = value.trim().replace(/\s+/g, " ");
  if (name.length < 2 || name.length > 100) return "Subject name must be between 2 and 100 characters";
  if (!/^[A-Za-z0-9 &()+#.,'/:-]+$/.test(name)) return "Subject name contains invalid characters";
  if (!/[A-Za-z]/.test(name)) return "Subject name must contain letters, not just numbers or symbols";
  if (new Set(name.toLowerCase().replace(/ /g, "")).size === 1) return "Please enter a valid subject name";
  return null;
}

export default function SubjectsPage() {
  const loader = useCallback(() => api.get<Subject[]>("/subjects"), []);
  const { data, loading, error, reload } = useAsyncData(loader, []);
  const [name, setName] = useState("");
  const [creating, setCreating] = useState(false);
  const [nameError, setNameError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function createSubject(e: FormEvent) {
    e.preventDefault();
    const validationError = subjectNameError(name);
    if (validationError) {
      setNameError(validationError);
      return;
    }
    setCreating(true);
    try {
      await api.post("/subjects", { name: name.trim().replace(/\s+/g, " "), color: "#0f766e" });
      setName("");
      await reload();
    } catch (err) {
      setNameError(err instanceof Error ? err.message : "Failed to create subject");
    } finally {
      setCreating(false);
    }
  }

  async function deleteSubject(subject: Subject) {
    if (!confirm(`Delete "${subject.name}"? All of its units and topics will be removed too. This can't be undone.`)) {
      return;
    }
    setDeletingId(subject.id);
    try {
      await api.delete(`/subjects/${subject.id}`);
      await reload();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete subject");
    } finally {
      setDeletingId(null);
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
          <form onSubmit={createSubject} className="flex items-start gap-2">
            <Input
              placeholder="New subject name"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setNameError(null);
              }}
              error={nameError ?? undefined}
              className="w-48"
              required
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
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        aria-label={`Delete ${subject.name}`}
                        title="Delete subject"
                        disabled={deletingId === subject.id}
                        onClick={(e) => {
                          // The card is a link; don't navigate when deleting
                          e.preventDefault();
                          e.stopPropagation();
                          deleteSubject(subject);
                        }}
                        className="rounded-md p-1.5 text-slate-400 transition hover:bg-red-50 hover:text-red-600 disabled:opacity-50 dark:hover:bg-red-950/40"
                      >
                        <Icon name="trash" className="h-4 w-4" />
                      </button>
                      <span
                        className="h-3 w-3 rounded-full"
                        style={{ backgroundColor: subject.color }}
                      />
                    </div>
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
