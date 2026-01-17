"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, ProjectListItem } from "@/lib/api";
import { Plus, Folder, LogOut, Settings } from "lucide-react";

export default function DashboardPage() {
  const router = useRouter();
  const [projects, set_projects] = useState<ProjectListItem[]>([]);
  const [loading, set_loading] = useState(true);
  const [creating, set_creating] = useState(false);
  const [new_project_name, set_new_project_name] = useState("");
  const [show_create_modal, set_show_create_modal] = useState(false);

  useEffect(() => {
    load_projects();
  }, []);

  const load_projects = async () => {
    try {
      const data = await api.list_projects();
      set_projects(data);
    } catch (err: any) {
      console.error("Failed to load projects:", err);
      if (err.status === 401) {
        router.push("/login");
      }
    } finally {
      set_loading(false);
    }
  };

  const handle_create_project = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!new_project_name.trim()) return;

    set_creating(true);
    try {
      const project = await api.create_project(new_project_name.trim());
      router.push(`/project/${project.id}`);
    } catch (err) {
      console.error("Failed to create project:", err);
    } finally {
      set_creating(false);
    }
  };

  const handle_logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    router.push("/login");
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-secondary">
      {/* Header */}
      <header className="bg-card border-b">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/dashboard" className="font-bold text-xl">
            finLine
          </Link>
          <div className="flex items-center gap-4">
            <Link
              href="/settings"
              className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
            >
              <Settings className="h-4 w-4" />
              Settings
            </Link>
            <button
              onClick={handle_logout}
              className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
            >
              <LogOut className="h-4 w-4" />
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-bold">Your Projects</h1>
          <button
            onClick={() => set_show_create_modal(true)}
            className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" />
            New Project
          </button>
        </div>

        {projects.length === 0 ? (
          <div className="bg-card rounded-lg p-12 text-center">
            <Folder className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h2 className="text-lg font-medium mb-2">No projects yet</h2>
            <p className="text-muted-foreground mb-4">
              Create your first LBO model to get started.
            </p>
            <button
              onClick={() => set_show_create_modal(true)}
              className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90"
            >
              Create Project
            </button>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((project) => (
              <Link
                key={project.id}
                href={`/project/${project.id}`}
                className="bg-card p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow"
              >
                <h3 className="font-medium mb-2">{project.name}</h3>
                <p className="text-sm text-muted-foreground">
                  Updated{" "}
                  {new Date(project.updated_at).toLocaleDateString()}
                </p>
              </Link>
            ))}
          </div>
        )}
      </main>

      {/* Create Modal */}
      {show_create_modal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-card p-6 rounded-lg shadow-lg w-full max-w-md">
            <h2 className="text-lg font-bold mb-4">Create New Project</h2>
            <form onSubmit={handle_create_project}>
              <input
                type="text"
                value={new_project_name}
                onChange={(e) => set_new_project_name(e.target.value)}
                placeholder="Project name"
                className="w-full px-3 py-2 border rounded-md bg-background mb-4 focus:outline-none focus:ring-2 focus:ring-primary"
                autoFocus
              />
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => set_show_create_modal(false)}
                  className="px-4 py-2 rounded-md hover:bg-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating || !new_project_name.trim()}
                  className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 disabled:opacity-50"
                >
                  {creating ? "Creating..." : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
