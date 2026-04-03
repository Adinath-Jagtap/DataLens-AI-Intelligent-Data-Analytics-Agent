// src/lib/groq.js
// Groq API — called directly from browser (free tier, rate-limited)

const GROQ_API_KEY = process.env.REACT_APP_GROQ_API_KEY;
const GROQ_BASE    = "https://api.groq.com/openai/v1/chat/completions";
const MODEL        = "llama-3.3-70b-versatile";

/**
 * Core chat completion
 * @param {Array} messages - [{role, content}]
 * @param {Object} options  - { temperature, max_tokens, onChunk }
 */
export async function groqChat(messages, options = {}) {
  const { temperature = 0.3, max_tokens = 2048, onChunk } = options;

  const res = await fetch(GROQ_BASE, {
    method: "POST",
    headers: {
      "Content-Type":  "application/json",
      "Authorization": `Bearer ${GROQ_API_KEY}`,
    },
    body: JSON.stringify({
      model:       MODEL,
      messages,
      temperature,
      max_tokens,
      stream:      !!onChunk,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || `Groq error ${res.status}`);
  }

  // Streaming mode
  if (onChunk) {
    const reader  = res.body.getReader();
    const decoder = new TextDecoder();
    let full = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value);
      const lines = chunk.split("\n").filter(l => l.startsWith("data:") && !l.includes("[DONE]"));
      for (const line of lines) {
        try {
          const delta = JSON.parse(line.slice(5))?.choices?.[0]?.delta?.content;
          if (delta) { full += delta; onChunk(delta, full); }
        } catch {}
      }
    }
    return full;
  }

  // Non-streaming
  const data = await res.json();
  return data.choices[0].message.content;
}

/** Analyse dataset and return cleaning instructions + insights */
export async function analyseDataset(datasetSummary) {
  return groqChat([
    {
      role: "system",
      content: `You are a senior data scientist. Given a dataset summary, return a JSON object with:
{
  "quality_score": 0-100,
  "issues": ["list of data quality issues"],
  "cleaning_steps": ["ordered list of cleaning operations to perform"],
  "key_insights": ["3-5 most important observations"],
  "recommended_charts": [
    { "type": "bar|line|scatter|pie|heatmap|histogram|box|violin", "x": "column", "y": "column", "title": "chart title", "reason": "why this chart" }
  ],
  "dataset_type": "sales|financial|scientific|survey|timeseries|other"
}
Return ONLY valid JSON, no markdown.`,
    },
    { role: "user", content: `Dataset summary:\n${JSON.stringify(datasetSummary, null, 2)}` },
  ], { temperature: 0.2, max_tokens: 2000 });
}

/** Chat with AI about the dataset */
export async function chatWithData(messages, datasetContext, onChunk) {
  const systemPrompt = `You are DataLens AI, an expert data analyst assistant. You have access to the user's dataset.

Dataset context:
${JSON.stringify(datasetContext, null, 2)}

Help the user understand their data, answer questions, suggest analyses, explain patterns, and assist with decision-making. Be concise, insightful, and use specific numbers from the data when relevant.`;

  return groqChat(
    [{ role: "system", content: systemPrompt }, ...messages],
    { temperature: 0.5, max_tokens: 1500, onChunk }
  );
}

/** Generate chart config from column info */
export async function generateChartConfigs(columns, sampleData, datasetType) {
  const result = await groqChat([
    {
      role: "system",
      content: `You are a data visualisation expert. Given column info and sample data, return an array of 8-12 chart configurations.
Return ONLY a JSON array like:
[
  { "id": "chart1", "type": "bar", "title": "Sales by Region", "xCol": "region", "yCol": "sales", "color": "#22d3ee", "description": "why this chart matters" },
  ...
]
Types allowed: bar, line, scatter, pie, histogram, box, heatmap, area
Return ONLY valid JSON array, no markdown.`,
    },
    {
      role: "user",
      content: `Columns: ${JSON.stringify(columns)}\nDataset type: ${datasetType}\nSample (5 rows): ${JSON.stringify(sampleData)}`,
    },
  ], { temperature: 0.3, max_tokens: 2000 });

  try {
    return JSON.parse(result.replace(/```json|```/g, "").trim());
  } catch {
    return [];
  }
}
