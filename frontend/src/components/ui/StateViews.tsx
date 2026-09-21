import { Button } from "./Button";

export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex min-h-[12rem] flex-col items-center justify-center gap-3 text-muted">
      <span className="h-8 w-8 animate-spin rounded-full border-2 border-teal-600 border-t-transparent" />
      <p className="text-sm">{label}</p>
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex min-h-[12rem] flex-col items-center justify-center gap-2 px-4 text-center">
      <h3 className="font-serif text-lg font-semibold text-slate-900 dark:text-slate-50">
        {title}
      </h3>
      {description && <p className="max-w-md text-sm text-muted">{description}</p>}
      {action}
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex min-h-[12rem] flex-col items-center justify-center gap-3 px-4 text-center">
      <p className="text-sm text-red-600 dark:text-red-400">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}
