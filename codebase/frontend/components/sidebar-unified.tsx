"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  ChevronLeft,
  ChevronRight,
  Lock,
  Check,
  FileText,
  HelpCircle,
  Settings,
  GraduationCap,
  Sparkles,
} from "lucide-react";

export function SidebarUnified({
  activeSessionId,
  onSelectSession,
  onNewChat,
  isCollapsed: controlledIsCollapsed,
  onToggleCollapse: controlledOnToggleCollapse,
}: {
  activeSessionId?: string;
  onSelectSession?: (id: string) => void;
  onNewChat?: () => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}) {
  const pathname = usePathname() || "";
  const [localIsCollapsed, setLocalIsCollapsed] = useState(false);
  const [day5Open, setDay5Open] = useState(true);

  const isCollapsed = controlledIsCollapsed !== undefined ? controlledIsCollapsed : localIsCollapsed;
  const toggleCollapse = controlledOnToggleCollapse || (() => setLocalIsCollapsed(!localIsCollapsed));

  const daysList = [
    { id: 1, label: "1. Attendance", isLocked: true },
    { id: 2, label: "2. Day 1 (28/05): AI & LLM Foundation", isLocked: true },
    { id: 3, label: "3. Day 2 (29/05): Xác định Bài toán cho AI", isLocked: true },
    { id: 4, label: "4. Day 3 (01/06): Design Pattern ReAct (Kiến...", isLocked: true },
    { id: 5, label: "5. Day 4 (02/06): Prompt Engineering & Too...", isLocked: true },
    {
      id: 6,
      label: "6. Day 5 (03/06): AI Product Thinking & Req...",
      isLocked: false,
      isActive: true,
      subItems: [
        { id: "slides", label: "Day 05 - Lecture Slides", isCompleted: true, type: "file" },
        { id: "submit", label: "Day 05 - Nộp bài Nhóm (deadline: 23:59...)", isCompleted: false, type: "exercise" },
      ],
    },
    { id: 7, label: "7. Day 6 (04/06): AI Product Prototype & De...", isLocked: true },
    { id: 8, label: "8. Day 7: Data Foundations (Embedding, C...", isLocked: true, isSoon: true },
    { id: 9, label: "9. Day 8: RAG Pipeline - Truy xuất & Sinh C...", isLocked: true, isSoon: true },
  ];

  if (isCollapsed) {
    return (
      <aside className="flex flex-col bg-[#fffcf6] text-[#3c3a39] shadow-sm h-full w-full items-center py-4 shrink-0 transition-all duration-300 rounded-2xl border border-[rgba(11,9,7,0.12)]">
        <button
          onClick={toggleCollapse}
          className="flex size-8 items-center justify-center rounded-xl bg-[rgba(11,9,7,0.06)] hover:bg-[rgba(11,9,7,0.12)] transition-colors mb-6"
          title="Expand sidebar"
          type="button"
        >
          <ChevronRight className="size-4 text-[#3c3a39]" />
        </button>

        <div className="flex-1 flex flex-col items-center gap-4 w-full px-1 overflow-auto scrollbar-none">
          {daysList.map((day) => (
            <div
              key={day.id}
              className={`flex size-8 shrink-0 items-center justify-center rounded-full text-xs font-mono font-bold ${
                day.isActive
                  ? "bg-[#2677ff] text-[#fefcf5] shadow"
                  : day.isSoon
                  ? "bg-[rgba(11,9,7,0.03)] text-[rgba(11,9,7,0.3)]"
                  : "bg-[rgba(11,9,7,0.06)] text-[rgba(11,9,7,0.5)]"
              }`}
              title={day.label}
            >
              {day.id - 1 || "A"}
            </div>
          ))}
        </div>

        <div className="mt-auto border-t border-[rgba(11,9,7,0.12)] pt-4 w-full flex flex-col items-center gap-4">
          <Link href="/u/0/students?tab=student-analytics" title="Mentor Dashboard">
            <GraduationCap className="size-5 text-[#2677ff] hover:text-[#3c3a39] transition-colors" />
          </Link>
        </div>
      </aside>
    );
  }

  return (
    <aside className="flex flex-col bg-[#fffcf6] text-[#3c3a39] shadow-sm h-full w-full overflow-hidden transition-all duration-300 rounded-2xl border border-[rgba(11,9,7,0.12)]">
      {/* Top action links */}
      <div className="flex items-center justify-between p-4 border-b border-[rgba(11,9,7,0.12)] bg-[#f7f7f5]/40 shrink-0">
        <span className="flex items-center gap-1.5 text-[10px] text-[rgba(11,9,7,0.6)] hover:text-[#3c3a39] transition-colors cursor-pointer font-sans select-none font-semibold">
          <ChevronLeft className="size-3.5" /> Back to course page
        </span>
        <button
          onClick={toggleCollapse}
          className="flex size-7 items-center justify-center rounded-lg bg-[rgba(11,9,7,0.06)] hover:bg-[rgba(11,9,7,0.12)] text-[#3c3a39] transition-colors"
          title="Collapse sidebar"
          type="button"
        >
          <ChevronLeft className="size-4" />
        </button>
      </div>

      {/* Main Title & Progress */}
      <div className="p-4 shrink-0">
        <h2 className="text-sm font-bold text-[#3c3a39] tracking-wide">
          AI.20K - Cohort 2
        </h2>
        {/* Progress Fill bar */}
        <div className="mt-3">
          <div className="h-1.5 w-full bg-[rgba(11,9,7,0.08)] rounded-full overflow-hidden">
            <div className="h-full bg-[#2677ff] rounded-full" style={{ width: "11%" }} />
          </div>
          <div className="flex justify-between items-center mt-1 text-[9px] text-[rgba(11,9,7,0.4)] font-mono tracking-wider font-semibold">
            <span>PROGRESS</span>
            <span>11%</span>
          </div>
        </div>
      </div>

      {/* Secondary tab group */}
      <div className="grid grid-cols-3 border-b border-[rgba(11,9,7,0.12)] text-center text-[10px] uppercase font-bold tracking-wider text-[rgba(11,9,7,0.5)] shrink-0">
        <button className="py-2 border-b-2 border-[#3c3a39] text-[#3c3a39] font-extrabold" type="button">
          Path
        </button>
        <button className="py-2 hover:text-[#3c3a39]" type="button" disabled>
          Learners
        </button>
        <button className="py-2 hover:text-[#3c3a39]" type="button" disabled>
          Discuss
        </button>
      </div>

      {/* Dynamic day list */}
      <div className="flex-1 overflow-auto p-3 space-y-1 scrollbar-none">
        {daysList.map((day) => {
          const isSelected = day.isActive;
          return (
            <div key={day.id} className="space-y-1">
              <div
                className={`w-full flex items-center justify-between rounded-xl px-3 py-2.5 text-left transition-all ${
                  day.isLocked
                    ? "text-[rgba(11,9,7,0.35)] cursor-not-allowed select-none bg-transparent"
                    : isSelected
                    ? "bg-[rgba(11,9,7,0.05)] text-[#3c3a39] border border-[rgba(11,9,7,0.12)] shadow-2xs font-bold"
                    : "hover:bg-[rgba(11,9,7,0.03)] text-[rgba(11,9,7,0.8)] cursor-pointer"
                }`}
                onClick={() => {
                  if (!day.isLocked && day.id === 6) {
                    setDay5Open(!day5Open);
                  }
                }}
              >
                <div className="min-w-0 flex-1 pr-2">
                  <p className="text-[11px] font-semibold truncate leading-5">
                    {day.label}
                  </p>
                </div>
                <div className="shrink-0 flex items-center">
                  {day.isSoon ? (
                    <span className="bg-[rgba(11,9,7,0.08)] text-[rgba(11,9,7,0.5)] text-[7px] font-mono font-bold px-1 py-0.5 rounded tracking-wide uppercase">
                      soon
                    </span>
                  ) : day.isLocked ? (
                    <Lock className="size-3 text-[rgba(11,9,7,0.25)]" />
                  ) : (
                    <ChevronRight
                      className={`size-3 text-[rgba(11,9,7,0.6)] transition-transform ${
                        day5Open ? "rotate-90" : ""
                      }`}
                    />
                  )}
                </div>
              </div>

              {/* Sub-items (Day 5 lecture slides, submits) */}
              {!day.isLocked && isSelected && day5Open && day.subItems && (
                <div className="pl-4 pr-1 py-1 space-y-1 border-l border-[rgba(11,9,7,0.12)] ml-3">
                  {day.subItems.map((sub) => {
                    const isSlide = sub.id === "slides";
                    return (
                      <button
                        key={sub.id}
                        type="button"
                        className={`w-full flex items-center justify-between rounded-lg px-2.5 py-1.5 text-left transition-all ${
                          isSlide
                            ? "bg-[#2677ff]/10 text-[#2677ff] font-bold border border-[#2677ff]/20 shadow-2xs"
                            : "hover:bg-[rgba(11,9,7,0.03)] text-[rgba(11,9,7,0.6)] text-[10px]"
                        }`}
                        disabled={!isSlide}
                      >
                        <span className="text-[10px] truncate flex items-center gap-1.5">
                          <FileText className={`size-3 shrink-0 ${isSlide ? "text-[#2677ff]" : "text-[rgba(11,9,7,0.35)]"}`} />
                          {sub.label}
                        </span>
                        {sub.isCompleted && <Check className="size-3 text-emerald-600 shrink-0" />}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Subtle Mentor link in footer */}
      <div className="p-3 border-t border-[rgba(11,9,7,0.12)] bg-[#f7f7f5]/40 shrink-0 flex items-center justify-between font-sans">
        <div className="flex items-center gap-2">
          <div className="size-6 rounded-full bg-[rgba(11,9,7,0.08)] flex items-center justify-center text-[10px] font-bold text-[#3c3a39] shadow-xs">
            M
          </div>
          <span className="text-[10px] font-bold text-[rgba(11,9,7,0.8)]">Mentor Pro</span>
        </div>
        <Link
          href="/u/0/students?tab=student-analytics"
          className="text-[9px] font-mono font-bold text-[#2677ff] hover:text-[#2677ff]/80 transition-colors"
          title="Open Admin Analytics"
        >
          /mentor-dashboard
        </Link>
      </div>
    </aside>
  );
}
