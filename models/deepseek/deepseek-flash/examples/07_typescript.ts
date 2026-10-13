/**
 * DeepSeek Chat Completions TypeScript 最小调用，检查完整回答。
 * 官方来源：https://api-docs.deepseek.com/api/create-chat-completion/
 */

import OpenAI from "openai";

const apiKey = process.env.DEEPSEEK_API_KEY;
if (!apiKey) throw new Error("请先设置 DEEPSEEK_API_KEY");

const client = new OpenAI({
  apiKey,
  baseURL: "https://api.deepseek.com",
  timeout: 120_000,
});

const response = await client.chat.completions.create({
  model: "deepseek-flash",
  messages: [{ role: "user", content: "用一句话介绍你自己" }],
});

const choice = response.choices[0];
if (!choice || choice.finish_reason !== "stop") {
  throw new Error(`回答未正常完成：${choice?.finish_reason ?? "没有 choices"}；请检查输出和思考预算`);
}
if (choice.message.tool_calls?.length) throw new Error("收到未处理的工具调用");
const answer = choice.message.content;
if (!answer?.trim()) throw new Error("没有最终正文");
console.log(answer);
console.log(response.usage);
