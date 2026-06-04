"use client";

import { ChevronLeft, ChevronRight, FileText, Maximize2, Loader2, RotateCcw } from "lucide-react";
import { useEffect, useState, useRef } from "react";

export function PdfViewerCentral({
  activePage,
  onChangePage,
  checkpointPage,
  onRestoreCheckpoint,
}: {
  activePage: number;
  onChangePage: (page: number) => void;
  checkpointPage: number | null;
  onRestoreCheckpoint: () => void;
}) {
  const totalPages = 53; // Based on the max slide_no in day05_ai_tutor_slide_sources.json
  const [pdfDoc, setPdfDoc] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [renderedPages, setRenderedPages] = useState<Record<number, boolean>>({});
  const containerRef = useRef<HTMLDivElement>(null);
  const isScrollingRef = useRef(false);

  // Load PDF.js from CDN dynamically
  useEffect(() => {
    const pdfjsLib = (window as any).pdfjsLib;
    if (pdfjsLib) {
      initPdf(pdfjsLib);
      return;
    }

    const script = document.createElement("script");
    script.src = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.min.js";
    script.async = true;
    script.onload = () => {
      const loadedLib = (window as any).pdfjsLib;
      if (loadedLib) {
        initPdf(loadedLib);
      }
    };
    document.body.appendChild(script);
  }, []);

  const initPdf = async (pdfjs: any) => {
    pdfjs.GlobalWorkerOptions.workerSrc = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js";
    try {
      const doc = await pdfjs.getDocument("/day05-lecture-slides-batch02.pdf").promise;
      setPdfDoc(doc);
      setLoading(false);
    } catch (err) {
      console.error("Error loading PDF:", err);
      setLoading(false);
    }
  };

  const renderPage = async (pageNum: number) => {
    if (!pdfDoc || renderedPages[pageNum]) return;

    try {
      setRenderedPages((prev) => ({ ...prev, [pageNum]: true }));
      const page = await pdfDoc.getPage(pageNum);
      
      const canvas = document.getElementById(`canvas-page-${pageNum}`) as HTMLCanvasElement;
      if (!canvas) {
        setRenderedPages((prev) => ({ ...prev, [pageNum]: false }));
        return;
      }

      const context = canvas.getContext("2d");
      if (!context) return;

      const viewport = page.getViewport({ scale: 1.5 });
      canvas.height = viewport.height;
      canvas.width = viewport.width;

      const renderContext = {
        canvasContext: context,
        viewport: viewport,
      };

      await page.render(renderContext).promise;
    } catch (err) {
      console.error(`Error rendering page ${pageNum}:`, err);
      setRenderedPages((prev) => ({ ...prev, [pageNum]: false }));
    }
  };

  // IntersectionObserver to lazy-render canvas nodes and update page indices on scroll
  useEffect(() => {
    if (!pdfDoc || !containerRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const pageNum = parseInt(entry.target.getAttribute("data-page") || "1");
          
          if (entry.isIntersecting) {
            renderPage(pageNum);
            
            // Trigger navigation updates if scrolling is manual
            if (!isScrollingRef.current && entry.intersectionRatio > 0.4) {
              onChangePage(pageNum);
            }
          }
        });
      },
      {
        root: containerRef.current,
        rootMargin: "-10% 0px -40% 0px",
        threshold: [0, 0.1, 0.5],
      }
    );

    const childNodes = containerRef.current.querySelectorAll(".pdf-page-slot");
    childNodes.forEach((node) => observer.observe(node));

    return () => {
      observer.disconnect();
    };
  }, [pdfDoc, renderedPages]);

  // Smooth scroll container to match activePage updates from external events
  useEffect(() => {
    if (!pdfDoc || !containerRef.current) return;

    const targetElement = document.getElementById(`page-slot-${activePage}`);
    if (targetElement) {
      isScrollingRef.current = true;
      targetElement.scrollIntoView({ behavior: "smooth", block: "start" });
      
      const timer = setTimeout(() => {
        isScrollingRef.current = false;
      }, 800);
      
      return () => clearTimeout(timer);
    }
  }, [activePage, pdfDoc]);

  const handlePrev = () => {
    if (activePage > 1) {
      onChangePage(activePage - 1);
    }
  };

  const handleNext = () => {
    if (activePage < totalPages) {
      onChangePage(activePage + 1);
    }
  };

  return (
    <section className="flex flex-col h-full rounded-2xl border border-[rgba(11,9,7,0.12)] bg-[#fffcf6] shadow-sm overflow-hidden">
      {/* Top Bar for PDF Navigation */}
      <div className="flex items-center justify-between border-b border-[rgba(11,9,7,0.12)] px-5 py-3.5 bg-[#f7f7f5]/40 shrink-0">
        <div className="flex items-center gap-2">
          <FileText className="size-4 text-[#ff7300]" />
          <span className="font-mono text-xs text-[#3c3a39] font-bold">
            /lecture-slides-day05.pdf
          </span>
        </div>

        {/* Page Nav controls */}
        <div className="flex items-center gap-4">
          <button
            onClick={handlePrev}
            disabled={activePage <= 1}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg border border-[rgba(11,9,7,0.1)] bg-[#fefcf5] text-xs font-semibold text-[#3c3a39] hover:bg-[#eaeae2] disabled:opacity-30 disabled:pointer-events-none transition-colors"
            type="button"
          >
            <ChevronLeft className="size-3.5" />
            previous
          </button>
          
          <span className="font-mono text-xs font-bold text-[#3c3a39]">
            {activePage} / {totalPages}
          </span>

          <button
            onClick={handleNext}
            disabled={activePage >= totalPages}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg border border-[rgba(11,9,7,0.1)] bg-[#fefcf5] text-xs font-semibold text-[#3c3a39] hover:bg-[#eaeae2] disabled:opacity-30 disabled:pointer-events-none transition-colors"
            type="button"
          >
            next
            <ChevronRight className="size-3.5" />
          </button>

          {/* Checkpoint Return Button */}
          {checkpointPage !== null && checkpointPage !== activePage && (
            <button
              onClick={onRestoreCheckpoint}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg border border-amber-500/30 bg-amber-500/10 text-xs font-bold text-amber-700 hover:bg-amber-500/20 transition-colors cursor-pointer shadow-2xs animate-pulse"
              type="button"
              title={`Quay lại Slide ${checkpointPage} (trước khi nhảy)`}
            >
              <RotateCcw className="size-3 text-amber-600" />
              <span>Slide {checkpointPage}</span>
            </button>
          )}
        </div>

        <div className="flex items-center gap-2 rounded-full border border-[rgba(11,9,7,0.12)] bg-[#fefcf5] px-3 py-1 font-mono text-[9px] text-[rgba(11,9,7,0.5)] font-semibold">
          <Maximize2 className="size-3 text-[#2677ff]" />
          /interactive-viewer
        </div>
      </div>

      {/* PDF list render view */}
      <div className="flex-1 bg-[#eaeae2]/30 p-4 relative overflow-y-auto">
        {loading ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
            <Loader2 className="size-6 animate-spin text-[#ff7300]" />
            <p className="text-xs font-mono text-[#ff7300] font-semibold">/loading-lecture-slides...</p>
          </div>
        ) : (
          <div
            ref={containerRef}
            className="h-full overflow-y-auto flex flex-col items-center gap-4 scrollbar-thin scroll-smooth pr-1"
          >
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((pageNum) => (
              <div
                id={`page-slot-${pageNum}`}
                key={pageNum}
                data-page={pageNum}
                className="pdf-page-slot w-full max-w-[800px] bg-white shadow-md border border-[rgba(11,9,7,0.1)] rounded-xl overflow-hidden flex flex-col items-center justify-center min-h-[450px] relative transition-shadow hover:shadow-lg shrink-0"
              >
                <div className="absolute top-2.5 left-2.5 bg-[#3c3a39]/80 text-[#fefcf5] font-mono text-[9px] font-bold px-2.5 py-1 rounded-full select-none z-10 shadow-sm">
                  Slide {pageNum}
                </div>
                <canvas
                  id={`canvas-page-${pageNum}`}
                  className="w-full h-auto object-contain max-h-[600px] bg-white"
                />
                {!renderedPages[pageNum] && (
                  <div className="absolute inset-0 flex items-center justify-center bg-[#fffcf6]/90 gap-2">
                    <Loader2 className="size-4 animate-spin text-[#ff7300]" />
                    <span className="text-xs text-[rgba(11,9,7,0.5)] font-mono font-semibold">
                      Rendering Slide {pageNum}...
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
