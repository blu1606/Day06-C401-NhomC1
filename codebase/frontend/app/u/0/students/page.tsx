"use client";

import { useEffect, useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { MessageSquare } from "lucide-react";
import { SidebarUnified } from "@/components/sidebar-unified";
import { VersionLogViewer } from "@/components/version-log-viewer";
import { EvalCasesViewer } from "@/components/eval-cases-viewer";
import { PromptToolsViewer } from "@/components/prompt-tools-viewer";
import { RunsViewer } from "@/components/runs-viewer";
import { StudentDashboard } from "@/components/student-dashboard";

export function StudentsPageContent() {
  const searchParams = useSearchParams();
  const [tab, setTab] = useState<string>("student-analytics");
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState(280);
  const [isResizingSidebar, setIsResizingSidebar] = useState(false);

  const startResizeSidebar = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizingSidebar(true);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isResizingSidebar) {
        const newWidth = Math.max(180, Math.min(450, e.clientX - 16));
        setSidebarWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizingSidebar(false);
    };

    if (isResizingSidebar) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
    }

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isResizingSidebar]);

  useEffect(() => {
    const tabParam = searchParams.get("tab");
    if (tabParam === "version-logs") {
      setTab("version-logs");
    } else if (tabParam === "eval-cases") {
      setTab("eval-cases");
    } else if (tabParam === "prompt-tools") {
      setTab("prompt-tools");
    } else if (tabParam === "runs") {
      setTab("runs");
    } else if (tabParam === "student-analytics") {
      setTab("student-analytics");
    } else {
      setTab("student-analytics");
    }
  }, [searchParams]);

  const renderActiveView = () => {
    switch (tab) {
      case "student-analytics":
        return <StudentDashboard activeSessionId="session-cohort" />;
      case "version-logs":
        return <VersionLogViewer />;
      case "eval-cases":
        return <EvalCasesViewer />;
      case "prompt-tools":
        return <PromptToolsViewer />;
      case "runs":
        return <RunsViewer />;
      default:
        return <StudentDashboard activeSessionId="session-cohort" />;
    }
  };

  return (
    <main
      className={`mx-auto flex min-h-dvh w-full max-w-[1600px] flex-col gap-4 px-4 py-4 lg:h-dvh lg:overflow-hidden bg-[#f2efe4] ${
        isResizingSidebar ? "select-none" : ""
      }`}
    >
      {/* Main Collapsible Layout */}
      <section className="flex min-h-0 flex-1 gap-1 transition-all duration-300">
        {/* COLUMN 1: COLLAPSIBLE UNIFIED SIDEBAR */}
        <div style={{ width: isCollapsed ? 72 : sidebarWidth }} className="flex shrink-0 h-full">
          <SidebarUnified
            isCollapsed={isCollapsed}
            onToggleCollapse={() => setIsCollapsed(!isCollapsed)}
            onNewChat={() => {
              window.location.href = "/u/0/app";
            }}
          />
        </div>

        {/* Resizer for Left Sidebar */}
        {!isCollapsed && (
          <div
            onMouseDown={startResizeSidebar}
            className={`w-2 hover:bg-[#ff7300]/20 active:bg-[#ff7300]/40 cursor-col-resize transition-colors flex items-center justify-center shrink-0 rounded-md ${
              isResizingSidebar ? "bg-[#ff7300]/30" : ""
            }`}
            title="Drag to resize sidebar"
          >
            <div className="w-[1px] h-8 bg-[rgba(11,9,7,0.12)]" />
          </div>
        )}

        {/* Center Panel (Modular Viewer) */}
        <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden gap-4">
          {/* Tab Navigation Bar */}
          <div className="flex items-center justify-between bg-[#fffcf6] border border-[rgba(11,9,7,0.12)] p-2 rounded-2xl shadow-sm shrink-0">
            <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-none font-mono text-[10px] uppercase font-bold">
              {[
                { id: "student-analytics", label: "Student Analytics" },
                { id: "version-logs", label: "Version Logs" },
                { id: "eval-cases", label: "Evaluation Cases" },
                { id: "prompt-tools", label: "Prompt & Tools" },
                { id: "runs", label: "Test Runs" },
              ].map((item) => (
                <Link
                  key={item.id}
                  href={`/u/0/students?tab=${item.id}`}
                  onClick={() => setTab(item.id)}
                  className={`rounded-xl px-4 py-2 transition-all text-center whitespace-nowrap cursor-pointer ${
                    tab === item.id
                      ? "bg-[#3c3a39] text-[#fefcf5] shadow-xs"
                      : "text-[rgba(11,9,7,0.5)] hover:text-[#3c3a39] hover:bg-[#eaeae2]/30"
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </div>
            
            <Link
              href="/u/0/app"
              className="flex items-center gap-1.5 rounded-xl border border-[rgba(11,9,7,0.15)] bg-[#fffcf6] px-4 py-2 font-mono text-[10px] uppercase font-bold text-[#3c3a39] hover:bg-[#eaeae2]/30 transition-all shadow-xs shrink-0"
            >
              <MessageSquare className="size-3.5 text-[#ff7300]" />
              Back to Chat
            </Link>
          </div>

          <div className="flex-1 overflow-auto">
            {renderActiveView()}
          </div>
        </div>
      </section>
    </main>
  );
}

export default function StudentsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen w-screen items-center justify-center bg-[#f2efe4] font-mono text-sm text-[#3c3a39]">
          /loading-optimization-terminal...
        </div>
      }
    >
      <StudentsPageContent />
    </Suspense>
  );
}
