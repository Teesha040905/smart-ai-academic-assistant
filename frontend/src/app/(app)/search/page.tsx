"use client";

import Link from "next/link";
import { FormEvent, useCallback, useState } from "react";
import { api } from "@/lib/api";
import { SearchResult } from "@/lib/types";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { ErrorState, LoadingState } from "@/components/ui/StateViews";
import { PageHeader } from "@/components/shared/PageHeader";

const typeLinks: Record<string, (id: string) => string> = {
  subject: (id) => `/subjects/${id}`,
  topic: () => `/subjects`,
  document: () => `/materials`,
  flashcard: () => `/flashcards`,
  assignment: () => `/planner`,
};

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  const search = useCallback(async (q: string) => {
    if (!q.trim()) return;
    setLoading(true);
    setError(null);
    setSearched(true);
    try {
      const data = await api.get<SearchResult[]>(
        `/search?q=${encodeURIComponent(q.trim())}`
      );
      setResults(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed");
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    search(query);
  }

  return (
    <div>
      <PageHeader title="Search" description="Find subjects, topics, materials, and more." />

      <form onSubmit={onSubmit} className="mb-6 flex gap-2">
        <Input
          placeholder="Search your library…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button type="submit" loading={loading}>
          Search
        </Button>
      </form>

      {loading && <LoadingState label="Searching…" />}
      {error && <ErrorState message={error} onRetry={() => search(query)} />}

      {!loading && !error && searched && (
        <Card>
          <CardBody className="space-y-2">
            {results.length === 0 ? (
              <p className="text-sm text-muted">No results for &ldquo;{query}&rdquo;.</p>
            ) : (
              results.map((r) => {
                const href = typeLinks[r.type]?.(r.id) ?? "/dashboard";
                return (
                  <Link
                    key={`${r.type}-${r.id}`}
                    href={href}
                    className="flex items-center justify-between rounded-lg px-3 py-2 hover:bg-slate-50 dark:hover:bg-slate-900/60"
                  >
                    <div>
                      <p className="font-medium">{r.title}</p>
                      {r.subtitle && <p className="text-xs text-muted">{r.subtitle}</p>}
                    </div>
                    <Badge tone="teal">{r.type}</Badge>
                  </Link>
                );
              })
            )}
          </CardBody>
        </Card>
      )}
    </div>
  );
}
