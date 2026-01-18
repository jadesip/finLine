"use client";

import { WizardProvider } from "@/contexts/wizard-context";
import { WizardSidebar } from "@/components/layout/wizard-sidebar";

export default function WizardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <WizardProvider>
      <div className="flex min-h-screen bg-background">
        <WizardSidebar />
        <main className="flex-1 p-8 overflow-auto">
          <div className="max-w-4xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </WizardProvider>
  );
}
