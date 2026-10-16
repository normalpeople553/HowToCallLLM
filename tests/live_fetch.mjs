/** Real-fetch observer for the existing non-streaming TypeScript example.
 *
 * Usage: MODEL_MANUAL_TELEMETRY=/absolute/new.json \
 *   node --import ./tests/live_fetch.mjs ./models/.../07_typescript.ts
 *
 * No credentials, request messages, response text, IDs or original errors are saved.
 * Only a Response clone is read; the original fetch and original Response are used.
 * The observer additionally sets redirect: "error": redirects are refused rather
 * than forwarding a prompt/body outside the endpoint allowlist. Body and headers
 * are unchanged; this explicit transport restriction is not a model parameter.
 */

import { writeFileSync } from "node:fs";

export const OFFICIAL_ENDPOINTS = new Set([
  "https://api.deepseek.com/chat/completions",
]);

const MAX_JSON_BYTES = 8 * 1024 * 1024;
const FINISH_REASONS = new Set([
  "stop", "length", "tool_calls", "content_filter", "aborted",
  "insufficient_system_resource",
]);
export const MODELS = new Set([
  "deepseek-flash", "DeepSeek-V4.1-Flash", "deepseek-v4.1-flash",
  "deepseek-v4-flash", "deepseek-v4-pro", "DeepSeek-V4-Pro-0813", "MiniMax-M2.7",
]);

function object(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function integer(value) {
  return Number.isSafeInteger(value) && value >= 0;
}

export function safeParameters(payload) {
  const result = {};
  for (const name of ["stream", "reasoning_split", "enable_thinking"]) {
    if (typeof payload[name] === "boolean") result[name] = payload[name];
  }
  for (const name of ["max_tokens", "max_completion_tokens", "max_output_tokens"]) {
    if (integer(payload[name])) result[name] = payload[name];
  }
  for (const name of ["temperature", "top_p"]) {
    if (typeof payload[name] === "number" && Number.isFinite(payload[name])) {
      result[name] = payload[name];
    }
  }
  if (["none", "low", "medium", "high", "max", "xhigh"].includes(payload.reasoning_effort)) {
    result.reasoning_effort = payload.reasoning_effort;
  }
  if (["none", "auto", "required"].includes(payload.tool_choice)) {
    result.tool_choice = payload.tool_choice;
  } else if (object(payload.tool_choice)) {
    result.tool_choice = "named_function";
  }
  if (object(payload.thinking)) {
    const thinking = {};
    if (["enabled", "disabled", "adaptive"].includes(payload.thinking.type)) {
      thinking.type = payload.thinking.type;
    }
    if (["all", "none"].includes(payload.thinking.keep)) thinking.keep = payload.thinking.keep;
    result.thinking = thinking;
  }
  if (object(payload.stream_options) && typeof payload.stream_options.include_usage === "boolean") {
    result.stream_options = { include_usage: payload.stream_options.include_usage };
  }
  if (object(payload.reasoning) && ["none", "low", "medium", "high", "max", "xhigh"].includes(payload.reasoning.effort)) {
    result.reasoning = { effort: payload.reasoning.effort };
  }
  if (object(payload.response_format) && ["text", "json_object", "json_schema"].includes(payload.response_format.type)) {
    result.response_format = { type: payload.response_format.type };
  }
  return result;
}

export function observeJSON(record, data) {
  if (!object(data)) return;
  if (MODELS.has(data.model)) record.served_model = data.model;
  if (object(data.base_resp) && integer(data.base_resp.status_code)) {
    record.business_status = data.base_resp.status_code;
  }
  if (object(data.usage)) {
    const usage = {};
    for (const name of ["prompt_tokens", "completion_tokens", "total_tokens", "input_tokens", "output_tokens"]) {
      if (integer(data.usage[name])) usage[name] = data.usage[name];
    }
    for (const [name, field] of [
      ["prompt_tokens_details", "cached_tokens"],
      ["completion_tokens_details", "reasoning_tokens"],
      ["input_tokens_details", "cached_tokens"],
      ["output_tokens_details", "reasoning_tokens"],
    ]) {
      if (object(data.usage[name]) && integer(data.usage[name][field])) {
        usage[name] = { [field]: data.usage[name][field] };
      }
    }
    record.usage = usage;
  }
  for (const choice of Array.isArray(data.choices) ? data.choices : []) {
    if (!object(choice)) continue;
    if (FINISH_REASONS.has(choice.finish_reason)) {
      (record.finish_reasons ??= []).push(choice.finish_reason);
    }
    const content = object(choice.message) ? choice.message.content : undefined;
    if (typeof content === "string") {
      let count = 0;
      for (const _character of content) count += 1;
      record.content_chars = (record.content_chars ?? 0) + count;
    }
    if (object(choice.message) && Array.isArray(choice.message.tool_calls) && choice.message.tool_calls.length) {
      record.has_tool_calls = true;
    }
  }
}

async function readClone(response, record) {
  if (!response.headers.get("content-type")?.toLowerCase().includes("application/json")) {
    record.observation_status = "not_json";
    return;
  }
  const reader = response.clone().body?.getReader();
  if (!reader) {
    record.observation_status = "empty_body";
    return;
  }
  const chunks = [];
  let bytes = 0;
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      bytes += value.byteLength;
      if (bytes > MAX_JSON_BYTES) {
        record.observation_status = "response_too_large";
        // Never await cancellation of a tee: its original consumer must stay independent.
        void reader.cancel().catch(() => {});
        return;
      }
      chunks.push(value);
    }
    const body = new Uint8Array(bytes);
    let offset = 0;
    for (const chunk of chunks) {
      body.set(chunk, offset);
      offset += chunk.byteLength;
    }
    try {
      observeJSON(record, JSON.parse(new TextDecoder().decode(body)));
      record.observation_status = "json_observed";
    } catch {
      record.observation_status = "invalid_json";
    }
  } catch {
    record.observation_status = "body_read_failed";
  } finally {
    reader.releaseLock();
  }
}

/** Tests may pass a loopback-only allowlist, while the production preloader cannot.
 * The fetch implementation must perform the real transport; no response is substituted.
 */
export function createFetchObserver(originalFetch, { telemetryPath, endpoints = OFFICIAL_ENDPOINTS } = {}) {
  const records = [];
  const pending = new Set();
  function flush(exitCode = process.exitCode ?? 0) {
    if (!telemetryPath) return;
    try {
      const code = typeof exitCode === "number" && Number.isInteger(exitCode) ? exitCode : 1;
      writeFileSync(telemetryPath, JSON.stringify({ exit_code: code, requests: records }), { encoding: "utf8", mode: 0o600 });
    } catch {
      // Never print paths, errors, request bodies or responses from the observer.
    }
  }
  async function fetchObserved(input, init) {
    let url;
    try {
      url = new URL(typeof input === "string" || input instanceof URL ? input : input.url);
    } catch {
      throw new Error("example_endpoint_not_allowlisted");
    }
    if (!endpoints.has(url.href)) throw new Error("example_endpoint_not_allowlisted");
    const method = String(init?.method ?? (typeof input === "object" ? input.method : undefined) ?? "GET").toUpperCase();
    // The checked-in TypeScript example uses the SDK's JSON-string POST body.
    if (method !== "POST" || typeof init?.body !== "string" || Buffer.byteLength(init.body) > MAX_JSON_BYTES) {
      throw new Error("unsupported_observation_request_body");
    }
    let payload;
    try {
      payload = JSON.parse(init.body);
    } catch {
      throw new Error("unsupported_observation_request_body");
    }
    if (!object(payload) || payload.stream === true) throw new Error("observer_requires_nonstream_json");
    const record = { method, endpoint: url.href, transport: "real_fetch", parameters: safeParameters(payload) };
    if (MODELS.has(payload.model)) record.requested_model = payload.model;
    records.push(record);
    flush();
    let response;
    try {
      // Native fetch follows redirects internally, beyond this wrapper's initial
      // URL check. Refuse redirects before any unallowlisted destination receives
      // the body, while preserving the caller's actual body/headers and Response.
      response = await originalFetch.call(globalThis, input, { ...init, redirect: "error" });
    } catch (error) {
      record.observation_status = "transport_failed";
      flush();
      throw error; // SDK retains its real error; the telemetry never stores it.
    }
    record.http_status = response.status;
    const observation = readClone(response, record).catch(() => {
      record.observation_status = "observer_failed";
    }).finally(() => {
      pending.delete(observation);
      flush();
    });
    pending.add(observation);
    return response; // Same object, not a reconstructed or replacement Response.
  }
  return {
    fetch: fetchObserved,
    records,
    flush,
    async settled() {
      while (pending.size) await Promise.allSettled([...pending]);
    },
  };
}

const telemetryPath = process.env.MODEL_MANUAL_TELEMETRY;
if (telemetryPath) {
  const observer = createFetchObserver(globalThis.fetch, { telemetryPath });
  globalThis.fetch = observer.fetch;
  process.on("exit", (code) => observer.flush(code));
}
