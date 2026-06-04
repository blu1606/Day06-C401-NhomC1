import { NextResponse } from "next/server";

const FASTAPI_BASE_URL = process.env.FASTAPI_BASE_URL ?? "http://127.0.0.1:8000";

export async function POST(request: Request) {
  try {
    const payload = await request.json();

    const response = await fetch(`${FASTAPI_BASE_URL}/api/v1/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const contentType = response.headers.get("content-type") ?? "";
    const data = contentType.includes("application/json")
      ? await response.json()
      : {
          error_code: "CHAT_BACKEND_NON_JSON_RESPONSE",
          message: await response.text(),
        };

    return NextResponse.json(data, { status: response.status });
  } catch (error: any) {
    console.error("Failed to forward chat request to backend:", error);
    return NextResponse.json(
      {
        error_code: "CHAT_BACKEND_UNAVAILABLE",
        message: "Backend chat service is unavailable (Simulating).",
      },
      { status: 502 }
    );
  }
}
