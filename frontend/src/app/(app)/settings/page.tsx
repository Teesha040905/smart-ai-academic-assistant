"use client";

import { FormEvent, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { useTheme, ThemeMode } from "@/lib/theme";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { PageHeader } from "@/components/shared/PageHeader";

export default function SettingsPage() {
  const { user, refreshUser, logout } = useAuth();
  const { mode, setMode } = useTheme();
  const [fullName, setFullName] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (user) setFullName(user.full_name);
  }, [user]);

  async function saveAccount(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.patch("/users/me", { full_name: fullName });
      await refreshUser();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Settings" description="Appearance and account preferences." />

      <Card>
        <CardHeader title="Appearance" />
        <CardBody>
          <label className="block text-sm font-medium">Theme</label>
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value as ThemeMode)}
            className="mt-2 h-10 w-full max-w-xs rounded-lg border border-slate-200 bg-white px-3 text-sm dark:border-slate-700 dark:bg-slate-900"
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
            <option value="system">System</option>
          </select>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Account" />
        <CardBody>
          <form onSubmit={saveAccount} className="max-w-md space-y-4">
            <Input
              label="Display name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
            <Button type="submit" loading={saving}>
              Save changes
            </Button>
          </form>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Danger zone" />
        <CardBody>
          <Button variant="danger" onClick={() => logout()}>
            Sign out
          </Button>
        </CardBody>
      </Card>
    </div>
  );
}
