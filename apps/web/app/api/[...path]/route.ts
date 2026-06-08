import { NextRequest, NextResponse } from "next/server";

const DEFAULT_BACKEND = "http://127.0.0.1:8000";
const EXPECTED_SERVICE = "alpha-sim-api";

type RouteContext = {
  params: Promise<{ path: string[] }> | { path: string[] };
};

async function resolvePath(params: RouteContext["params"]) {
  const value = await Promise.resolve(params);
  return value.path.join("/");
}

function resolveBackend() {
  return process.env.NEXT_PUBLIC_API_BASE_URL || process.env.API_BASE_URL || DEFAULT_BACKEND;
}

async function proxy(request: NextRequest, context: RouteContext) {
  const backend = resolveBackend();
  const path = await resolvePath(context.params);
  const method = request.method.toUpperCase();
  const body = method === "GET" || method === "HEAD" ? undefined : await request.text();
  const upstream = new URL(`/api/${path}${request.nextUrl.search}`, backend);

  try {
    const response = await fetch(upstream, {
      method,
      headers: {
        "content-type": request.headers.get("content-type") || "application/json"
      },
      body,
      cache: "no-store"
    });
    const text = await response.text();

    if (path === "v1/health" && response.ok) {
      try {
        const payload = JSON.parse(text) as { service?: string };
        if (payload.service && payload.service !== EXPECTED_SERVICE) {
          return NextResponse.json(
            {
              error: "wrong_backend",
              message: `期望 ${EXPECTED_SERVICE}，当前为 ${payload.service}`,
              backend,
              hint: "py -3 -m uvicorn apps.api.alpha_sim.main:app --reload --port 8000"
            },
            { status: 502 }
          );
        }
      } catch {
        // keep original health payload
      }
    }

    return new NextResponse(text, {
      status: response.status,
      headers: {
        "content-type": response.headers.get("content-type") || "application/json",
        "x-alpha-backend": backend
      }
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown backend error";
    return NextResponse.json(
      {
        error: "backend_unreachable",
        message,
        backend,
        hint: "py -3 -m uvicorn apps.api.alpha_sim.main:app --reload --port 8000"
      },
      { status: 502 }
    );
  }
}

export async function GET(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

export async function POST(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}
