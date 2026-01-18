"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, ProjectListItem } from "@/lib/api";
import { Plus, Folder, LogOut, Settings, Trash2 } from "lucide-react";

export default function DashboardPage() {
  const router = useRouter();
  const [projects, set_projects] = useState<ProjectListItem[]>([]);
  const [loading, set_loading] = useState(true);
  const [deleting_id, set_deleting_id] = useState<string | null>(null);

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

  const handle_new_project = () => {
    router.push("/project-wizard/type");
  };

  const handle_delete_project = async (e: React.MouseEvent, project_id: string) => {
    e.preventDefault();
    e.stopPropagation();

    if (!confirm("Are you sure you want to delete this project?")) {
      return;
    }

    set_deleting_id(project_id);
    try {
      await api.delete_project(project_id);
      set_projects(projects.filter(p => p.id !== project_id));
    } catch (err) {
      console.error("Failed to delete project:", err);
    } finally {
      set_deleting_id(null);
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
            onClick={handle_new_project}
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
              onClick={handle_new_project}
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
                className="bg-card p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow relative group"
              >
                <h3 className="font-medium mb-2">{project.name}</h3>
                <p className="text-sm text-muted-foreground">
                  Updated{" "}
                  {new Date(project.updated_at).toLocaleDateString()}
                </p>
                <button
                  onClick={(e) => handle_delete_project(e, project.id)}
                  disabled={deleting_id === project.id}
                  className="absolute top-4 right-4 p-2 rounded-md opacity-0 group-hover:opacity-100 hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-all"
                  title="Delete project"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
