/**
 * DeepSeek Chat Completions TypeScript 最小调用。
 * 官方来源：https://api-docs.deepseek.com/guides/codex
 */

import OpenAI from "openai";

const apiKey = process.env.DEEPSEEK_API_KEY;
if (!apiKey) throw new Error("请先设置 DEEPSEEK_API_KEY");

const client = new OpenAI({
  apiKey,
  baseURL: "https://api.deepseek.com",
  timeout: 60_000,
});

const response = await client.chat.completions.create({
  model: "deepseek-flash",
  messages: [{ role: "user", content: "用一句话介绍你自己" }],
});

console.log(response.choices[0].message.content);
