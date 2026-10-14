/** Offline transport integration checks: native fetch against loopback HTTP only.
 * No SDK response is mocked and no provider API or real credential is used.
 */

import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import http from "node:http";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createFetchObserver } from "./live_fetch.mjs";

const secret = "offline-private-key-fixture";
const prompt = "offline-private-prompt-fixture";
const answer = "offline-private-answer-fixture";
const reasoning = "offline-private-reasoning-fixture";
const rawError = "offline-private-error-fixture";
const responseId = "offline-private-response-id-fixture";
const payload = JSON.stringify({
  model: "deepseek-flash", messages: [{ role: "user", content: prompt }],
  thinking: { type: "disabled", private: secret },
  response_format: { type: "json_object", private: prompt },
});
const responses = {
  success: {
    id: responseId, model: "deepseek-flash",
    choices: [{ finish_reason: "stop", message: { content: answer, reasoning_content: reasoning } }],
    usage: { prompt_tokens: 2, completion_tokens: 3, total_tokens: 5, private: secret },
  },
  failure: { error: { message: rawError, request_id: responseId, api_key: secret } },
};

let originRequests = 0;
let destinationRequests = 0;
let serverFailure;
const received = [];
const destination = http.createServer(async (request, response) => {
  destinationRequests += 1;
  for await (const _chunk of request) { /* A redirected prompt must never arrive. */ }
  response.writeHead(200, { "content-type": "application/json" });
  response.end(JSON.stringify(responses.success));
});
await new Promise((resolve) => destination.listen(0, "127.0.0.1", resolve));
const destinationURL = `http://127.0.0.1:${destination.address().port}/not-allowlisted`;
const origin = http.createServer(async (request, response) => {
  originRequests += 1;
  let body = "";
  for await (const chunk of request) body += chunk;
  try {
    assert.equal(body, payload);
    assert.equal(request.headers.authorization, `Bearer ${secret}`);
    assert.equal(request.headers["content-type"], "application/json");
    received.push({ bodyMatches: true, headersMatch: true });
  } catch (error) {
    serverFailure = error;
    response.writeHead(400).end();
    return;
  }
  if (request.url === "/redirect") {
    response.writeHead(307, { location: destinationURL }).end();
  } else {
    response.writeHead(request.url === "/rate" ? 429 : 200, { "content-type": "application/json" });
    response.end(JSON.stringify(request.url === "/rate" ? responses.failure : responses.success));
  }
});
await new Promise((resolve) => origin.listen(0, "127.0.0.1", resolve));
const base = `http://127.0.0.1:${origin.address().port}`;
const directory = mkdtempSync(join(tmpdir(), "model-manual-fetch-offline-"));
const telemetryPath = join(directory, "telemetry.json");

try {
  const nativeFetch = globalThis.fetch;
  const actualResponses = [];
  const actualInits = [];
  const observer = createFetchObserver(async (input, init) => {
    actualInits.push(init);
    const response = await nativeFetch(input, init);
    actualResponses.push(response);
    return response;
  }, { telemetryPath, endpoints: new Set([`${base}/ok`, `${base}/rate`, `${base}/redirect`]) });
  const init = {
    method: "POST", headers: { "content-type": "application/json", authorization: `Bearer ${secret}` },
    body: payload, redirect: "follow",
  };
  const response = await observer.fetch(`${base}/ok`, init);
  assert.equal(response, actualResponses[0], "the original Response object must be returned");
  assert.equal((await response.json()).choices[0].message.content, answer);
  await observer.settled();
  assert.equal(init.redirect, "follow", "do not mutate caller options in place");
  assert.equal(actualInits[0].redirect, "error");
  assert.equal(actualInits[0].body, init.body);
  assert.equal(actualInits[0].headers, init.headers);
  assert.equal(observer.records[0].observation_status, "json_observed");
  assert.equal(observer.records[0].http_status, 200);
  assert.equal(observer.records[0].content_chars, [...answer].length);
  assert.deepEqual(observer.records[0].finish_reasons, ["stop"]);
  assert.deepEqual(observer.records[0].usage, { prompt_tokens: 2, completion_tokens: 3, total_tokens: 5 });

  const limited = await observer.fetch(`${base}/rate`, init);
  assert.equal(limited, actualResponses[1]);
  assert.equal(limited.status, 429);
  assert.equal((await limited.json()).error.message, rawError, "the real error body remains available to the SDK");
  await observer.settled();
  assert.equal(observer.records[1].http_status, 429);
  assert.equal(observer.records[1].observation_status, "json_observed");
  assert.equal(observer.records[1].content_chars, undefined);

  await assert.rejects(observer.fetch(`${base}/redirect`, init));
  await observer.settled();
  assert.equal(originRequests, 3);
  assert.equal(destinationRequests, 0, "307 must not forward the body to a second server");
  assert.equal(observer.records[2].observation_status, "transport_failed");
  assert.equal(observer.records[2].http_status, undefined);
  assert.equal(observer.records[2].content_chars, undefined);
  assert.equal(actualInits[2].redirect, "error");

  await assert.rejects(observer.fetch(destinationURL, init));
  assert.equal(destinationRequests, 0);
  assert.equal(originRequests, 3);
  assert.equal(serverFailure, undefined);
  assert.equal(received.length, 3);
  observer.flush(0);
  const saved = readFileSync(telemetryPath, "utf8");
  assert.deepEqual(JSON.parse(saved).requests, observer.records);
  const metadata = saved + JSON.stringify(observer.records);
  for (const value of [secret, prompt, answer, reasoning, rawError, responseId]) {
    assert(!metadata.includes(value), "telemetry must not contain private fixture material");
  }
  console.log(JSON.stringify({
    checks: ["original_response", "original_body_and_headers", "privacy", "http_429", "redirect_307_rejected", "unallowlisted_url_rejected"],
    origin_requests: originRequests, redirected_requests: destinationRequests,
  }));
} finally {
  await Promise.all([
    new Promise((resolve) => origin.close(resolve)),
    new Promise((resolve) => destination.close(resolve)),
  ]);
  rmSync(directory, { recursive: true, force: true });
}
