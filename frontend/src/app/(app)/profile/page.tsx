"use client";

import { FormEvent, useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { StudentProfile } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { LoadingState } from "@/components/ui/StateViews";
import { PageHeader } from "@/components/shared/PageHeader";

export default function ProfilePage() {
  const { user, loading, refreshUser } = useAuth();
  const profile = user?.profile;
  const [course, setCourse] = useState("");
  const [branch, setBranch] = useState("");
  const [semester, setSemester] = useState("");
  const [saving, setSaving] = useState(false);
  useEffect(() => {
    if (!profile) return;
    setCourse(profile.course || "");
    setBranch(profile.branch || "");
    setSemester(profile.semester ? String(profile.semester) : "");
  }, [profile]);

  async function saveProfile(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.patch<StudentProfile>("/users/me/profile", {
        course: course || null,
        branch: branch || null,
        semester: semester ? Number(semester) : null,
      });
      await refreshUser();
    } finally {
      setSaving(false);
    }
  }

  if (loading || !user) return <LoadingState />;

  return (
    <div className="space-y-6">
      <PageHeader title="Profile" description="Account and academic details." />

      <Card>
        <CardHeader title="Account" />
        <CardBody className="space-y-2 text-sm">
          <p>
            <span className="text-muted">Name:</span> {user.full_name}
          </p>
          <p>
            <span className="text-muted">Email:</span> {user.email}
          </p>
          <p>
            <span className="text-muted">Role:</span> {user.role}
          </p>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Student profile" />
        <CardBody>
          <form onSubmit={saveProfile} className="grid gap-4 md:grid-cols-2">
            <Input label="Course" value={course} onChange={(e) => setCourse(e.target.value)} />
            <Input label="Branch" value={branch} onChange={(e) => setBranch(e.target.value)} />
            <Input
              label="Semester"
              type="number"
              min={1}
              max={12}
              value={semester}
              onChange={(e) => setSemester(e.target.value)}
            />
            <div className="md:col-span-2">
              <Button type="submit" loading={saving}>
                Save profile
              </Button>
            </div>
          </form>
        </CardBody>
      </Card>
    </div>
  );
}
