"use client";

import { useState, useEffect } from "react";
import { SidebarUnified } from "./sidebar-unified";
import { PdfViewerCentral } from "./pdf-viewer-central";
import { ChatPanelInteractive } from "./chat-panel-interactive";
import { TraceRailInteractive } from "./trace-rail-interactive";

export function AgentTraceViewer() {
  const [activeSessionId, setActiveSessionId] = useState("session-cohort");
  const [showRightPanel, setShowRightPanel] = useState(true);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [customTrace, setCustomTrace] = useState<any>(null);
  const [activeSlidePage, setActiveSlidePage] = useState<number>(1);
  const [checkpointPage, setCheckpointPage] = useState<number | null>(null);
  const [rightTab, setRightTab] = useState<"chat" | "telemetry">("chat");

  // Reset custom trace when changing sessions
  useEffect(() => {
    setCustomTrace(null);
  }, [activeSessionId]);

  // Resize states
  const [sidebarWidth, setSidebarWidth] = useState(280);
  const [rightPanelWidth, setRightPanelWidth] = useState(420);
  const [isResizingSidebar, setIsResizingSidebar] = useState(false);
  const [isResizingRight, setIsResizingRight] = useState(false);

  const handleNewChat = () => {
    setActiveSessionId(`session-new-${Date.now()}`);
  };

  const startResizeSidebar = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizingSidebar(true);
  };

  const startResizeRight = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizingRight(true);
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isResizingSidebar) {
        const newWidth = Math.max(180, Math.min(450, e.clientX - 16));
        setSidebarWidth(newWidth);
      }
      if (isResizingRight) {
        const newWidth = Math.max(280, Math.min(600, window.innerWidth - e.clientX - 16));
        setRightPanelWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizingSidebar(false);
      setIsResizingRight(false);
    };

    if (isResizingSidebar || isResizingRight) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
    }

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isResizingSidebar, isResizingRight]);

  return (
    <main className={`mx-auto flex h-dvh w-full max-w-[1600px] flex-col gap-3 px-3 py-3 lg:overflow-hidden bg-[#f2efe4] ${
      isResizingSidebar || isResizingRight ? "select-none" : ""
    }`}>
      <section className="flex min-h-0 flex-1 gap-1 transition-all duration-300">
        {/* COLUMN 1: LMS sidebar */}
        <div style={{ width: isCollapsed ? 72 : sidebarWidth }} className="flex shrink-0 h-full">
          <SidebarUnified
            activeSessionId={activeSessionId}
            onSelectSession={setActiveSessionId}
            onNewChat={handleNewChat}
            isCollapsed={isCollapsed}
            onToggleCollapse={() => setIsCollapsed(!isCollapsed)}
          />
        </div>

        {/* Resizer for Left Sidebar */}
        {!isCollapsed && (
          <div
            onMouseDown={startResizeSidebar}
            className={`w-2 hover:bg-blue-500/20 active:bg-blue-500/40 cursor-col-resize transition-colors flex items-center justify-center shrink-0 rounded-md ${
              isResizingSidebar ? "bg-blue-500/10" : ""
            }`}
            title="Drag to resize sidebar"
          >
            <div className="w-[1px] h-8 bg-[rgba(11,9,7,0.12)]" />
          </div>
        )}

        {/* COLUMN 2: PDF Central Viewer */}
        <div className="flex-1 min-w-0 h-full">
          <PdfViewerCentral
            activePage={activeSlidePage}
            onChangePage={setActiveSlidePage}
            checkpointPage={checkpointPage}
            onRestoreCheckpoint={() => {
              if (checkpointPage !== null) {
                setActiveSlidePage(checkpointPage);
                setCheckpointPage(null);
              }
            }}
          />
        </div>

        {/* Resizer for Right Panel */}
        {showRightPanel && (
          <div
            onMouseDown={startResizeRight}
            className={`w-2 hover:bg-blue-500/20 active:bg-blue-500/40 cursor-col-resize transition-colors flex items-center justify-center shrink-0 rounded-md ${
              isResizingRight ? "bg-blue-500/10" : ""
            }`}
            title="Drag to resize chat panel"
          >
            <div className="w-[1px] h-8 bg-[rgba(11,9,7,0.12)]" />
          </div>
        )}

        {/* COLUMN 3: Right Panel - Toggled Chat/Telemetry */}
        {showRightPanel && (
          <div
            style={{ width: rightPanelWidth }}
            className="flex flex-col shrink-0 h-full rounded-2xl border border-[rgba(11,9,7,0.12)] bg-[#fffcf6] shadow-sm overflow-hidden"
          >
            {/* Toggle header tabs */}
            <div className="flex border-b border-[rgba(11,9,7,0.1)] bg-[#f7f7f5]/40 p-1 font-mono text-[9px] uppercase font-bold shrink-0">
              <button
                onClick={() => setRightTab("chat")}
                className={`flex-1 rounded-xl py-2 text-center transition-all cursor-pointer ${
                  rightTab === "chat"
                    ? "bg-[#3c3a39] text-[#fefcf5] shadow-xs"
                    : "text-[rgba(11,9,7,0.5)] hover:text-[#3c3a39]"
                }`}
                type="button"
              >
                AI Tutor Chat
              </button>
              <button
                onClick={() => setRightTab("telemetry")}
                className={`flex-1 rounded-xl py-2 text-center transition-all cursor-pointer ${
                  rightTab === "telemetry"
                    ? "bg-[#3c3a39] text-[#fefcf5] shadow-xs"
                    : "text-[rgba(11,9,7,0.5)] hover:text-[#3c3a39]"
                }`}
                type="button"
              >
                Trace Telemetry
              </button>
            </div>

            {/* Panel Tab View content */}
            <div className="flex-1 min-h-0">
              {rightTab === "chat" ? (
                <ChatPanelInteractive
                  activeSessionId={activeSessionId}
                  onTraceUpdate={setCustomTrace}
                  onSelectSlidePage={setActiveSlidePage}
                  activeSlidePage={activeSlidePage}
                  checkpointPage={checkpointPage}
                  setCheckpointPage={setCheckpointPage}
                />
              ) : (
                <TraceRailInteractive activeSessionId={activeSessionId} customTrace={customTrace} />
              )}
            </div>
          </div>
        )}
      </section>
    </main>
  );
}
