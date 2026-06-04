"use client";

import {
  Bot,
  CheckCircle2,
  ChevronDown,
  Copy,
  Loader2,
  PanelRight,
  Send,
  ShieldAlert,
  Wrench,
  FileText,
  ShieldCheck,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import day05SlideSources from "@/data/day05_ai_tutor_slide_sources.json";
import { traces, type AgentTrace } from "@/lib/mock-traces";
import type { ChatMessage, SimulatedStep } from "@/lib/types";

type BackendTraceStep = Omit<SimulatedStep, "status"> & {
  status?: "success" | "failed" | "timeout";
};

type DiagnoseResponse = {
  summary: string;
  steps?: BackendTraceStep[];
};

const stepIcons = {
  thought: Bot,
  tool: Wrench,
  observation: CheckCircle2,
  final: CheckCircle2,
  error: ShieldAlert,
};

export function ChatPanelInteractive({
  activeSessionId,
  onTraceUpdate,
  onSelectSlidePage,
  activeSlidePage,
  checkpointPage,
  setCheckpointPage,
}: {
  activeSessionId: string;
  onTraceUpdate?: (trace: any) => void;
  onSelectSlidePage?: (page: number) => void;
  activeSlidePage: number;
  checkpointPage: number | null;
  setCheckpointPage: (page: number | null) => void;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isMockMode, setIsMockMode] = useState(true); // Default to mock mode for hackathon sandbox
  const [isBackendConnected, setIsBackendConnected] = useState(true);
  const [isFallbackModeActive, setIsFallbackModeActive] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const currentSessionIdRef = useRef(activeSessionId);

  // Load initial session messages or restore from localStorage/backend transcripts
  useEffect(() => {
    let isMounted = true;

    async function loadTranscriptAndMessages() {
      // 1. Fallback to localStorage first to check active session
      if (typeof window !== "undefined") {
        const saved = localStorage.getItem("gaptutor_messages_" + activeSessionId);
        if (saved) {
          try {
            const parsed = JSON.parse(saved) as ChatMessage[];
            if (parsed && parsed.length > 0) {
              if (isMounted) {
                setMessages(parsed);
                currentSessionIdRef.current = activeSessionId;
                return;
              }
            }
          } catch (e) {
            console.error("Failed to parse saved messages", e);
          }
        }
      }

      // 2. Fallback to default presets matching the new Day 5 spec
      let initialMsg: ChatMessage[] = [];
      if (activeSessionId === "session-cohort") {
        const trace = traces[0]; // success-cohort-diagnostic (Slide 9 RAG)
        initialMsg = [
          {
            id: "msg-user-1",
            role: "user",
            content: trace.query,
            timestamp: Date.now() - 1000 * 60 * 5,
          },
          {
            id: "msg-assistant-1",
            role: "assistant",
            content: trace.steps.find((s) => s.kind === "final")?.content ?? trace.summary,
            timestamp: Date.now() - 1000 * 60 * 4,
            slidePage: trace.slidePage,
            slidePages: trace.slidePages,
            citationLabel: "Day 05 Batch 02, slide 9, Ba lớp bất định",
            thinkingSteps: trace.steps.map((s) => ({
              id: s.id,
              title: s.title,
              kind: s.kind as SimulatedStep["kind"],
              content: s.content,
              toolName: s.toolName,
              status: "completed",
              durationMs: s.durationMs,
            })),
          },
        ];
      } else if (activeSessionId === "session-student") {
        const trace = traces[2]; // timeout-fallback (Slide 30 Graceful Refusal)
        initialMsg = [
          {
            id: "msg-user-2",
            role: "user",
            content: trace.query,
            timestamp: Date.now() - 1000 * 60 * 30,
          },
          {
            id: "msg-assistant-2",
            role: "assistant",
            content: trace.steps.find((s) => s.kind === "final")?.content ?? trace.summary,
            timestamp: Date.now() - 1000 * 60 * 29,
            slidePage: trace.slidePage,
            slidePages: trace.slidePages,
            citationLabel: "Day 05 Batch 02, slide 30, Graceful Failure",
            thinkingSteps: trace.steps.map((s) => ({
              id: s.id,
              title: s.title,
              kind: s.kind as SimulatedStep["kind"],
              content: s.content,
              toolName: s.toolName,
              status: "completed",
              durationMs: s.durationMs,
            })),
          },
        ];
      } else if (activeSessionId === "session-security") {
        const trace = traces[1]; // security-blocked
        initialMsg = [
          {
            id: "msg-user-3",
            role: "user",
            content: trace.query,
            timestamp: Date.now() - 1000 * 60 * 60,
          },
          {
            id: "msg-assistant-3",
            role: "assistant",
            content: trace.summary,
            timestamp: Date.now() - 1000 * 60 * 59,
            thinkingSteps: trace.steps.map((s) => ({
              id: s.id,
              title: s.title,
              kind: s.kind as SimulatedStep["kind"],
              content: s.content,
              toolName: s.toolName,
              status: "completed",
              durationMs: s.durationMs,
            })),
          },
        ];
      } else {
        initialMsg = [
          {
            id: "msg-welcome",
            role: "assistant",
            content: "Xin chào! Tôi là GapTutor AI Student Assistant. Hãy hỏi tôi về nội dung kiến thức của slide bài giảng Day 5 nhé (ví dụ: *Ba lớp bất định là gì?*, *Thiết kế UX cho AI ra sao?*).",
            timestamp: Date.now(),
          },
        ];
      }

      if (isMounted) {
        setMessages(initialMsg);
        currentSessionIdRef.current = activeSessionId;
      }
    }

    loadTranscriptAndMessages();

    return () => {
      isMounted = false;
    };
  }, [activeSessionId]);

  // Save messages to localStorage isolated by activeSessionId
  useEffect(() => {
    if (
      typeof window !== "undefined" &&
      messages.length > 0 &&
      currentSessionIdRef.current === activeSessionId
    ) {
      localStorage.setItem("gaptutor_messages_" + activeSessionId, JSON.stringify(messages));
    }
  }, [messages, activeSessionId]);

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  // Check slide_sources to match query
  const findMatchingSlide = (queryText: string) => {
    const q = queryText.toLowerCase();
    
    // Clean text helper for better matching
    const clean = (str: string) => 
      str.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
    
    const cleanQuery = clean(q);

    for (const record of day05SlideSources.records) {
      const titleMatch = clean(record.section_title).includes(cleanQuery);
      const tagMatch = record.skill_tags.some(tag => clean(tag).includes(cleanQuery));
      const questionMatch = record.example_student_questions.some(eq => 
        clean(eq).includes(cleanQuery) || cleanQuery.includes(clean(eq))
      );
      
      let keywordMatch = false;
      if (cleanQuery.includes("bat dinh") || cleanQuery.includes("uncertainty") || cleanQuery.includes("phuong sai")) {
        if (record.source_id === "DAY05-S009" || record.source_id === "DAY05-S008") keywordMatch = true;
      }
      if (cleanQuery.includes("routing") || cleanQuery.includes("error") || cleanQuery.includes("dinh tuyen")) {
        if (record.source_id === "DAY05-S012") keywordMatch = true;
      }
      if (cleanQuery.includes("automation") || cleanQuery.includes("augmentation") || cleanQuery.includes("tang nang luc")) {
        if (record.source_id === "DAY05-S014") keywordMatch = true;
      }
      if (cleanQuery.includes("boundary") || cleanQuery.includes("workflow") || cleanQuery.includes("tach task")) {
        if (record.source_id === "DAY05-S015") keywordMatch = true;
      }
      if (cleanQuery.includes("failure mode") || cleanQuery.includes("cach sai") || cleanQuery.includes("loi truoc khi")) {
        if (record.source_id === "DAY05-S022") keywordMatch = true;
      }
      if (cleanQuery.includes("vibe coding") || cleanQuery.includes("code bang spec")) {
        if (record.source_id === "DAY05-S045") keywordMatch = true;
      }
      if (cleanQuery.includes("graceful") || cleanQuery.includes("failure") || cleanQuery.includes("giam thiet hai") || cleanQuery.includes("xin dap an") || cleanQuery.includes("code ho")) {
        if (record.source_id === "DAY05-S030") keywordMatch = true;
      }
      if (cleanQuery.includes("canvas") || cleanQuery.includes("ba tru")) {
        if (record.source_id === "DAY05-S020" || record.source_id === "DAY05-S003") keywordMatch = true;
      }

      if (titleMatch || tagMatch || questionMatch || keywordMatch) {
        return record;
      }
    }
    return null;
  };

  const runLocalTraceSimulation = (userText: string, assistantMsgId: string, isOfflineFallback = false) => {
    // 1. Security Check
    if (userText.toLowerCase().includes("ignore") || userText.toLowerCase().includes("system prompt")) {
      const securityTrace = traces.find(t => t.id === "security-blocked")!;
      const steps = securityTrace.steps.map(s => ({ ...s, status: "completed" as const }));
      
      setTimeout(() => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  content: securityTrace.summary,
                  thinkingSteps: steps,
                  isSimulating: false,
                  isOfflineFallback,
                }
              : msg
          )
        );
        if (onTraceUpdate) onTraceUpdate(securityTrace);
      }, 1000);
      return;
    }

    // 2. Matching Slides RAG lookup
    const matchedSlide = findMatchingSlide(userText);
    
    if (matchedSlide) {
      // Determine if this query should trigger multi-citation simulation
      const clean = (str: string) => 
        str.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
      const cleanQ = clean(userText);
      
      const isMultiCitation = cleanQ.includes("so sanh") || 
                              cleanQ.includes("tong hop") || 
                              cleanQ.includes("va") || 
                              matchedSlide.slide_no === 9 || 
                              matchedSlide.slide_no === 20;

      // Define slidePages array based on RAG results
      const simulatedSlidePages = isMultiCitation 
        ? [matchedSlide.slide_no, matchedSlide.slide_no === 9 ? 8 : (matchedSlide.slide_no === 20 ? 9 : matchedSlide.slide_no - 1)].filter((v, i, a) => a.indexOf(v) === i)
        : [matchedSlide.slide_no];

      const allSteps: SimulatedStep[] = [
        {
          id: `thought-init-${Date.now()}`,
          title: "Intention & Query Analysis",
          kind: "thought",
          content: `Học viên hỏi về '${matchedSlide.section_title}'. Tiến hành truy xuất (Retrieval) nội dung bài học Day 5.`,
          status: "completed",
        },
        {
          id: `tool-retrieve-${Date.now()}`,
          title: "Retrieve Slide Database",
          kind: "tool",
          toolName: "retrieve_lecture_context",
          status: "completed",
          durationMs: 110,
          content: `Truy vấn thành công slide bài giảng Day 5. Khớp các slide trích dẫn: ${simulatedSlidePages.join(", ")}.`,
          input: { query: userText, day: 5 },
          output: { matched_slides: simulatedSlidePages.map(page => ({ slide_no: page })) },
        },
        {
          id: `thought-model-${Date.now()}`,
          title: "Formulate grounded answer",
          kind: "thought",
          content: `Phát hiện slide ${simulatedSlidePages.join(" & ")} phù hợp. Chọn mode 'Giải thích' (Explain) đa nguồn. Soạn thảo phản hồi kèm trích dẫn nguồn.`,
          status: "completed",
        }
      ];

      let stepIndex = 0;
      const runSteps = () => {
        if (stepIndex < allSteps.length) {
          const currentStep = allSteps[stepIndex];
          setMessages((prev) =>
            prev.map((msg) => {
              if (msg.id !== assistantMsgId) return msg;
              const updatedSteps = [...(msg.thinkingSteps || [])];
              updatedSteps.push(currentStep);
              return { ...msg, thinkingSteps: updatedSteps };
            })
          );
          stepIndex++;
          setTimeout(runSteps, 600);
        } else {
          // Finish simulation
          const citationSuffix = isMultiCitation 
            ? `slide ${simulatedSlidePages.join(" & ")}` 
            : `slide ${matchedSlide.slide_no}`;
          const finalAnswerText = `${matchedSlide.summary}\n\n**Chi tiết bài học:**\n${matchedSlide.source_excerpt}\n\n*Nguồn trích dẫn: Day 05 Batch 02, ${citationSuffix}.*`;
          
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    content: finalAnswerText,
                    isSimulating: false,
                    slidePage: matchedSlide.slide_no,
                    slidePages: simulatedSlidePages,
                    citationLabel: matchedSlide.citation_label,
                    isOfflineFallback,
                  }
                : msg
            )
          );

          // Update parent trace panel
          const newTrace: AgentTrace = {
            id: `trace-${Date.now()}`,
            title: `RAG: Slide ${simulatedSlidePages.join(" & ")}`,
            query: userText,
            status: "completed",
            latencyMs: 1250,
            promptTokens: 810,
            completionTokens: 250,
            costUsd: 0.0021,
            isFallbackTriggered: false,
            summary: `Đã tìm thấy Slide ${simulatedSlidePages.join(" & ")} giải thích về ${matchedSlide.section_title} trong bài học Day 5.`,
            slidePage: matchedSlide.slide_no,
            slidePages: simulatedSlidePages,
            steps: allSteps,
          };
          if (onTraceUpdate) onTraceUpdate(newTrace);
          
          // Save current page as checkpoint and auto scroll slide iframe to that page
          if (activeSlidePage !== matchedSlide.slide_no) {
            setCheckpointPage(activeSlidePage);
          }
          if (onSelectSlidePage) onSelectSlidePage(matchedSlide.slide_no);
        }
      };

      setTimeout(runSteps, 300);
    } else {
      // 3. Fallback low-confidence path (Slide 30 Refusal)
      const fallbackTrace = traces.find(t => t.id === "timeout-fallback")!;
      const allSteps: SimulatedStep[] = [
        {
          id: `thought-fb-1-${Date.now()}`,
          title: "Analyze student query",
          kind: "thought",
          content: "Không tìm thấy nội dung khớp trực tiếp trong slide bài giảng Day 5. Áp dụng chính sách Graceful Refusal.",
          status: "completed",
        },
        {
          id: `tool-fb-2-${Date.now()}`,
          title: "Intention integrity check",
          kind: "tool",
          toolName: "verify_academic_integrity",
          status: "completed",
          durationMs: 40,
          content: "Kiểm tra xem câu hỏi có thuộc phạm vi giải hộ bài hay hỏi ngoài lề không.",
          input: { query: userText },
          output: { is_violation: true, action: "refuse_and_hint" },
        }
      ];

      let stepIndex = 0;
      const runSteps = () => {
        if (stepIndex < allSteps.length) {
          const currentStep = allSteps[stepIndex];
          setMessages((prev) =>
            prev.map((msg) => {
              if (msg.id !== assistantMsgId) return msg;
              const updatedSteps = [...(msg.thinkingSteps || [])];
              updatedSteps.push(currentStep);
              return { ...msg, thinkingSteps: updatedSteps };
            })
          );
          stepIndex++;
          setTimeout(runSteps, 600);
        } else {
          const fallbackText = `Tôi không tìm thấy câu trả lời trực tiếp trong tài liệu Day 5 bài học. Bạn hãy thử hỏi lại cụ thể hơn về các khái niệm có trong slide bài học như: *Bất định (Uncertainty)*, *Error Routing*, *Augmentation*, hay *Failure Modes*.\n\n*Nguồn trích dẫn: Day 05 Batch 02, slide 30, Graceful Failure.*`;
          
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    content: fallbackText,
                    isSimulating: false,
                    slidePage: 30,
                    slidePages: [30, 12],
                    citationLabel: "Day 05 Batch 02, slide 30, Graceful Failure",
                    isOfflineFallback,
                  }
                : msg
            )
          );

          if (onTraceUpdate) onTraceUpdate(fallbackTrace);
          // Save current page as checkpoint and auto scroll slide iframe to that page
          if (activeSlidePage !== 30) {
            setCheckpointPage(activeSlidePage);
          }
          if (onSelectSlidePage) onSelectSlidePage(30);
        }
      };

      setTimeout(runSteps, 300);
    }
  };

  const handleSend = async () => {
    if (!inputValue.trim() || isTyping) return;

    const userText = inputValue;
    setInputValue("");

    const userMessage: ChatMessage = {
      id: `msg-user-${Date.now()}`,
      role: "user",
      content: userText,
      timestamp: Date.now(),
    };
    const assistantMsgId = `msg-assistant-${Date.now()}`;
    const initialAssistantMsg: ChatMessage = {
      id: assistantMsgId,
      role: "assistant",
      content: "",
      timestamp: Date.now(),
      thinkingSteps: [],
      isSimulating: true,
    };

    setMessages((prev) => [...prev, userMessage, initialAssistantMsg]);
    setIsTyping(true);

    if (isMockMode) {
      runLocalTraceSimulation(userText, assistantMsgId);
      setIsTyping(false);
      return;
    }

    // Live API mode (fallback to mock if request fails)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, 5000);

    try {
      const history = messages.slice(-10).map((message) => ({
        role: message.role,
        content: message.content,
      }));
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({ session_id: activeSessionId, query: userText, history }),
      });
      
      clearTimeout(timeoutId);

      const data = await response.json() as DiagnoseResponse & {
        error_code?: string;
        message?: string;
        task_id?: string;
        telemetry?: {
          total_execution_time_ms?: number;
          prompt_tokens?: number;
          completion_tokens?: number;
          estimated_cost_usd?: number;
        };
      };

      if (!response.ok) {
        setIsBackendConnected(false);
        setIsFallbackModeActive(true);
        runLocalTraceSimulation(userText, assistantMsgId, true);
        return;
      }

      const backendSteps: SimulatedStep[] = (data.steps ?? []).map((step) => ({
        id: step.id,
        title: step.title,
        kind: step.kind,
        content: step.content,
        toolName: step.toolName,
        status: "completed",
        durationMs: step.durationMs,
        input: step.input,
        output: step.output,
        errorCode: step.errorCode,
      }));

      setIsBackendConnected(true);
      setIsFallbackModeActive(false);

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId
            ? {
                ...msg,
                content: data.summary,
                thinkingSteps: backendSteps,
                isSimulating: false,
                isOfflineFallback: false,
              }
            : msg
        )
      );
    } catch {
      clearTimeout(timeoutId);
      setIsBackendConnected(false);
      setIsFallbackModeActive(true);
      runLocalTraceSimulation(userText, assistantMsgId, true);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Trigger feedback report (Correction Path)
  const handleLogFeedback = (msgId: string) => {
    setMessages((prev) =>
      prev.map((msg) => {
        if (msg.id !== msgId) return msg;
        if (msg.feedbackLogged) return msg;

        // Log correction block into telemetry steps
        const updatedSteps = [...(msg.thinkingSteps || [])];
        updatedSteps.push({
          id: `correction-${Date.now()}`,
          title: "Observation Correction Logged",
          kind: "error",
          content: "Học viên báo cáo Citation bị sai hoặc không rõ ngữ cảnh. Lỗi đã được ghi nhận thành golden test case.",
          status: "completed",
          errorCode: "USER_CITATION_CORRECTION",
        });

        // Trigger parent telemetry trace update
        if (onTraceUpdate) {
          onTraceUpdate((currTrace: any) => {
            if (!currTrace) return currTrace;
            return {
              ...currTrace,
              steps: [...(currTrace.steps || []), {
                id: `correction-${Date.now()}`,
                title: "Correction Logged",
                kind: "error",
                content: "Feedback học viên báo lỗi citation. Chuyển sang golden test suite.",
                errorCode: "USER_CITATION_CORRECTION"
              }]
            };
          });
        }

        return {
          ...msg,
          feedbackLogged: true,
          thinkingSteps: updatedSteps,
        };
      })
    );
  };

  return (
    <section className="flex flex-col h-full rounded-2xl border border-[rgba(11,9,7,0.12)] bg-[#fffcf6] shadow-sm overflow-hidden">
      {/* Header bar */}
      <div className="flex items-center justify-between border-b border-[rgba(11,9,7,0.12)] px-5 py-4 bg-[#f7f7f5]/40 shrink-0">
        <div>
          <h2 className="text-sm font-bold text-[#3c3a39]">GapTutor Student AI Assistant</h2>
          <p className="font-mono text-xs text-[#2677ff] font-semibold">
            /classroom-tutor-agent
          </p>
        </div>
        <div className="flex items-center gap-2">
          {!isBackendConnected && (
            <span className="flex items-center gap-1 rounded-full border border-red-500/30 bg-red-500/10 px-2 py-0.5 font-mono text-[8px] font-bold text-red-600 animate-pulse">
              ⚠️ Off-line
            </span>
          )}
          <button
            onClick={() => {
              setIsMockMode(!isMockMode);
              if (isMockMode) {
                // Reset connection states when switching to Live API
                setIsBackendConnected(true);
                setIsFallbackModeActive(false);
              }
            }}
            className={`flex items-center gap-1.5 rounded-full border px-3 py-1.5 font-mono text-[9px] font-bold shadow-sm transition-all cursor-pointer ${
              isMockMode
                ? "border-amber-500/30 bg-amber-500/10 text-amber-600 hover:bg-amber-500/20"
                : !isBackendConnected
                ? "border-red-500/30 bg-red-500/5 text-red-500 hover:bg-red-500/10"
                : "border-emerald-500/30 bg-emerald-500/10 text-emerald-600 hover:bg-emerald-500/20"
            }`}
            type="button"
          >
            <span className={`size-1 rounded-full ${
              isMockMode
                ? "bg-amber-500 animate-pulse"
                : !isBackendConnected
                ? "bg-red-500 animate-ping"
                : "bg-emerald-500 animate-pulse"
            }`} />
            {isMockMode ? "Sandbox Mock" : !isBackendConnected ? "Offline Fallback" : "Live API"}
          </button>
        </div>
      </div>

      {/* Fallback mode alert banner */}
      {isFallbackModeActive && (
        <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-2 text-[10px] text-amber-700 flex items-start gap-1.5 font-mono select-none">
          <span className="shrink-0 font-bold">⚠️ [Chế độ Dự phòng]:</span>
          <span>Mất kết nối với AI Engine. Đang phản hồi ngoại tuyến bằng Cơ sở tri thức Slide Day 5.</span>
        </div>
      )}

      {/* Message logs */}
      <div className="flex-1 space-y-3 overflow-auto p-3.5 scrollbar-thin">
        {messages.map((msg) => (
          <div key={msg.id} className="space-y-2">
            {msg.role === "user" ? (
              <div className="flex justify-end">
                <div className="max-w-[85%] rounded-2xl rounded-br-none border border-transparent bg-[#3c3a39] px-4 py-2.5 text-xs leading-5 text-[#fefcf5] shadow-xs font-semibold">
                  {msg.content}
                </div>
              </div>
            ) : (
              <div className="flex items-start gap-2.5">
                <div className="flex size-8 shrink-0 items-center justify-center rounded-xl bg-[#f7f7f5] border border-[rgba(11,9,7,0.1)] mt-0.5">
                  <Bot className="size-3.5 text-[rgba(11,9,7,0.7)]" />
                </div>
                <div className="min-w-0 flex-1">
                  {/* Unified Assistant Bubble */}
                  <div className="max-w-full rounded-2xl rounded-tl-none border border-[rgba(11,9,7,0.08)] bg-[#f7f7f5] px-4 py-3 text-xs leading-5 text-[#3c3a39] space-y-2.5 shadow-3xs">
                    {msg.thinkingSteps && msg.thinkingSteps.length > 0 && (
                      <ThinkingBlock steps={msg.thinkingSteps} />
                    )}
                    {msg.isSimulating ? (
                      <div className="flex items-center gap-2 text-[rgba(11,9,7,0.6)] py-0.5">
                        <Loader2 className="size-3.5 animate-spin text-[#ff272d]" />
                        <span>Retrieving slides & thinking...</span>
                      </div>
                    ) : (
                      msg.content && (
                        <div className="prose max-w-none text-xs text-[#3c3a39] space-y-2">
                          <ReactMarkdown>{msg.content}</ReactMarkdown>
                          {msg.isOfflineFallback && (
                            <p className="text-[9px] font-mono text-neutral-400 select-none pt-1 border-t border-[rgba(11,9,7,0.06)]">
                              ℹ️ Câu trả lời được trích xuất ngoại tuyến từ Slide bài học do mất kết nối tới AI Engine.
                            </p>
                          )}
                        </div>
                      )
                    )}
                  </div>

                  {/* Render slide citation chips & feedback button */}
                  {!msg.isSimulating && (msg.slidePages || msg.slidePage) && (
                    (() => {
                      const slidePages = msg.slidePages || (msg.slidePage ? [msg.slidePage] : []);
                      if (slidePages.length === 0) return null;

                      return (
                        <div className="flex flex-wrap items-center gap-1.5 mt-1.5">
                          <span className="font-mono text-[9px] font-bold text-[rgba(11,9,7,0.4)]">
                            /sources:
                          </span>
                          
                          {slidePages.map((pageNum) => {
                            const isCurrent = activeSlidePage === pageNum;
                            return (
                              <button
                                key={pageNum}
                                onClick={() => {
                                  if (onSelectSlidePage) {
                                    if (activeSlidePage !== pageNum) {
                                      setCheckpointPage(activeSlidePage);
                                    }
                                    onSelectSlidePage(pageNum);
                                  }
                                }}
                                className={`flex items-center gap-1 rounded-md px-2 py-0.5 text-[9px] font-mono font-bold transition-all border cursor-pointer ${
                                  isCurrent
                                    ? "bg-[#3c3a39] text-[#fefcf5] border-[#3c3a39] shadow-2xs"
                                    : "bg-[#fffcf6] text-[#2677ff] border-[#2677ff]/20 hover:bg-[#2677ff]/5"
                                }`}
                                type="button"
                                title={`Xem Slide ${pageNum}`}
                              >
                                <FileText className="size-3" />
                                Slide {pageNum}
                              </button>
                            );
                          })}
                          
                          <div className="h-3 w-[1px] bg-[rgba(11,9,7,0.1)] mx-0.5" />

                          <button
                            onClick={() => handleLogFeedback(msg.id)}
                            disabled={msg.feedbackLogged}
                            className={`rounded-md p-1 text-[9px] font-mono font-bold transition-all border cursor-pointer ${
                              msg.feedbackLogged
                                ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-600 cursor-default"
                                : "border-red-500/10 bg-red-500/5 text-red-400 hover:text-red-500 hover:bg-red-500/10"
                            }`}
                            type="button"
                            title={msg.feedbackLogged ? "Đã báo cáo trích dẫn lỗi" : "Báo trích dẫn sai"}
                          >
                            <ShieldAlert className="size-3" />
                          </button>
                        </div>
                      );
                    })()
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
        {isTyping && messages[messages.length - 1]?.role === "user" && (
          <div className="flex items-start gap-2.5">
            <div className="flex size-8 shrink-0 items-center justify-center rounded-xl bg-[#f7f7f5] border border-[rgba(11,9,7,0.1)] mt-0.5">
              <Bot className="size-3.5 text-[rgba(11,9,7,0.7)]" />
            </div>
            <div className="max-w-full rounded-2xl rounded-tl-none border border-[rgba(11,9,7,0.08)] bg-[#f7f7f5] px-4 py-3 text-xs leading-5 text-[rgba(11,9,7,0.6)] flex items-center gap-2 shadow-3xs">
              <Loader2 className="size-3.5 animate-spin text-[#ff272d]" />
              <span>Contacting knowledge engine...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input textbox */}
      <div className="border-t border-[rgba(11,9,7,0.1)] p-4 bg-[#fffcf6] shrink-0 space-y-2">
        {isFallbackModeActive && (
          <div className="text-[9px] font-mono text-amber-700 bg-amber-500/10 border border-amber-500/20 rounded-lg px-2.5 py-1.5 select-none leading-relaxed">
            <span className="font-bold">💡 Gợi ý câu hỏi ngoại tuyến:</span> Ba lớp bất định, Trụ cột thiết kế, Error routing, Vibe coding, Cắt lát nhỏ...
          </div>
        )}
        <div className="flex items-end gap-2.5 rounded-2xl border border-[rgba(11,9,7,0.1)] bg-[#fefcf5] p-2.5 focus-within:border-[rgba(11,9,7,0.25)] transition-colors">
          <textarea
            className="min-h-10 flex-1 resize-none bg-transparent text-xs leading-5 text-[#3c3a39] outline-none placeholder:text-[rgba(11,9,7,0.4)]"
            placeholder="Hỏi về Slide Day 5 (ví dụ: ba lớp bất định, error routing...)"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isTyping}
          />
          <button
            aria-label="Send message"
            className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-[#3c3a39] text-[#fefcf5] hover:opacity-90 transition-opacity disabled:opacity-40"
            onClick={handleSend}
            disabled={!inputValue.trim() || isTyping}
            type="button"
          >
            <Send className="size-3.5" />
          </button>
        </div>
      </div>
    </section>
  );
}

function ThinkingBlock({ steps }: { steps: SimulatedStep[] }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="w-full border-b border-[rgba(11,9,7,0.06)] pb-2 mb-2">
      <button
        aria-expanded={open}
        className="flex items-center justify-between w-full py-1 text-left text-[10px] font-mono text-[rgba(11,9,7,0.5)] hover:text-[#3c3a39] transition-colors"
        onClick={() => setOpen((current) => !current)}
        type="button"
      >
        <span className="flex items-center gap-1.5">
          <Bot className="size-3 text-[rgba(11,9,7,0.4)]" />
          <span>/reasoning-trail</span>
          <span className="rounded-full bg-[rgba(11,9,7,0.06)] px-1.5 py-0.2 text-[8px] font-semibold text-[rgba(11,9,7,0.5)]">
            {steps.length} blocks
          </span>
        </span>
        <ChevronDown
          className={`size-3 text-[rgba(11,9,7,0.4)] transition-transform duration-200 ${
            open ? "rotate-180" : ""
          }`}
        />
      </button>
      {open && (
        <div className="mt-2 pl-2 border-l border-[rgba(11,9,7,0.08)] space-y-2 ml-1.5">
          {steps.map((step) =>
            step.kind === "tool" ? (
              <InlineToolCallBlock key={step.id} step={step} />
            ) : (
              <InlineThinkingLine key={step.id} step={step} />
            )
          )}
        </div>
      )}
    </div>
  );
}

function InlineThinkingLine({ step }: { step: SimulatedStep }) {
  const Icon = stepIcons[step.kind] || Bot;

  return (
    <div className="flex items-start gap-2 text-[10px] leading-relaxed">
      <Icon className="mt-0.5 size-3 shrink-0 text-[rgba(11,9,7,0.4)]" />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <span className="font-semibold text-[#3c3a39]">{step.title}</span>
        </div>
        {step.content && (
          <div className="text-[rgba(11,9,7,0.55)] mt-0.5 italic prose max-w-none text-[9.5px]">
            <ReactMarkdown>{step.content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}

function InlineToolCallBlock({ step }: { step: SimulatedStep }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="overflow-hidden rounded-lg border border-[rgba(11,9,7,0.06)] bg-[#fffcf6] shadow-3xs">
      <button
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-2 px-2 py-1.5 text-left transition-colors hover:bg-[rgba(11,9,7,0.02)]"
        onClick={() => setOpen((current) => !current)}
        type="button"
      >
        <span className="flex min-w-0 items-center gap-2">
          <Wrench className="size-3 text-[#2677ff] shrink-0" />
          <span className="min-w-0">
            <span className="block truncate text-[10px] font-bold text-[#3c3a39] font-mono">
              {step.toolName ?? step.title}
            </span>
            {step.content && (
              <span className="block truncate text-[9px] text-[rgba(11,9,7,0.5)]">
                {step.content}
              </span>
            )}
          </span>
        </span>
        <span className="flex shrink-0 items-center gap-1.5">
          <span className="rounded-full bg-emerald-500/10 px-1.5 py-0.2 text-[8px] font-mono uppercase font-bold text-emerald-600">
            call
          </span>
          <ChevronDown
            className={`size-3 text-[rgba(11,9,7,0.4)] transition-transform duration-200 ${
              open ? "rotate-180" : ""
            }`}
          />
        </span>
      </button>
      {open && (
        <div className="grid gap-2 border-t border-[rgba(11,9,7,0.06)] p-2 bg-[#fefcf5] text-[9px] font-mono">
          {step.input !== undefined && (
            <JsonBlock label="Parameters" value={step.input} />
          )}
          {step.output !== undefined && (
            <JsonBlock label="Observation" value={step.output} />
          )}
        </div>
      )}
    </div>
  );
}

function JsonBlock({ label, value }: { label: string; value: unknown }) {
  return (
    <div className="overflow-hidden rounded-lg border border-[rgba(11,9,7,0.08)] bg-[#fffcf6]">
      <div className="flex items-center justify-between border-b border-[rgba(11,9,7,0.06)] px-2 py-1 font-mono text-[8px] uppercase tracking-wider text-[rgba(11,9,7,0.5)] bg-[#f7f7f5]">
        {label}
      </div>
      <pre className="max-h-32 overflow-auto p-1.5 text-[8.5px] leading-3 text-[rgba(11,9,7,0.7)]">
        <code>{JSON.stringify(value, null, 2)}</code>
      </pre>
    </div>
  );
}
