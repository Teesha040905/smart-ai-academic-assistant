"use client";

import { ChangeEvent, useCallback, useState } from "react";
import { API_BASE, api, getToken } from "@/lib/api";
import { useAsyncData } from "@/lib/hooks";
import { Document, Subject } from "@/lib/types";
import { formatBytes, formatDateTime } from "@/lib/utils";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ErrorState, LoadingState } from "@/components/ui/StateViews";
import { PageHeader } from "@/components/shared/PageHeader";

export default function MaterialsPage() {
  const docsLoader = useCallback(() => api.get<Document[]>("/documents"), []);
  const subjectsLoader = useCallback(() => api.get<Subject[]>("/subjects"), []);
  const docs = useAsyncData(docsLoader, []);
  const subjects = useAsyncData(subjectsLoader, []);
  const [subjectId, setSubjectId] = useState("");
  const [uploading, setUploading] = useState(false);

  async function onUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("title", file.name);
      if (subjectId) form.append("subject_id", subjectId);
      await fetch(`${API_BASE}/documents`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` },
        body: form,
      }).then(async (res) => {
        if (!res.ok) throw new Error(await res.text());
      });
      await docs.reload();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  if (docs.loading || subjects.loading) return <LoadingState />;
  if (docs.error) return <ErrorState message={docs.error} onRetry={docs.reload} />;

  return (
    <div>
      <PageHeader
        title="Materials"
        description="Upload PDFs, slides, and notes for RAG-powered tutoring."
        action={
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={subjectId}
              onChange={(e) => setSubjectId(e.target.value)}
              className="h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm dark:border-slate-700 dark:bg-slate-900"
            >
              <option value="">No subject</option>
              {subjects.data?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
            <label className="cursor-pointer">
              <span className="inline-flex h-10 items-center rounded-lg bg-teal-700 px-4 text-sm font-medium text-white hover:bg-teal-800">
                {uploading ? "Uploading…" : "Choose file"}
              </span>
              <input type="file" className="hidden" onChange={onUpload} disabled={uploading} />
            </label>
          </div>
        }
      />

      <Card>
        <CardHeader title="Library" />
        <CardBody className="space-y-3">
          {!docs.data?.length ? (
            <p className="text-sm text-muted">No documents uploaded yet.</p>
          ) : (
            docs.data.map((doc) => (
              <div
                key={doc.id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-200/80 px-3 py-2 dark:border-slate-800"
              >
                <div>
                  <p className="font-medium">{doc.title}</p>
                  <p className="text-xs text-muted">
                    {formatBytes(doc.file_size)} · {formatDateTime(doc.created_at)}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge tone={doc.status === "ready" ? "green" : doc.status === "failed" ? "red" : "amber"}>
                    {doc.status}
                  </Badge>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={async () => {
                      const res = await fetch(`${API_BASE}/documents/${doc.id}/download`, {
                        headers: { Authorization: `Bearer ${getToken()}` },
                      });
                      if (!res.ok) return;
                      const blob = await res.blob();
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = doc.original_filename;
                      a.click();
                      URL.revokeObjectURL(url);
                    }}
                  >
                    Download
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={async () => {
                      await api.delete(`/documents/${doc.id}`);
                      docs.reload();
                    }}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            ))
          )}
        </CardBody>
      </Card>
    </div>
  );
}
