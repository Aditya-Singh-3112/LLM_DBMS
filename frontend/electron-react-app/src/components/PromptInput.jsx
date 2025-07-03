import { useState } from "react";
import axios from "axios";

export default function PromptInput({ onResults }) {
  const [prompt, setPrompt] = useState("");

  const runQuery = () => {
    if (!prompt.trim()) return;
    axios.post("http://localhost:8000/query", { prompt })
      .then(res => onResults(res.data))
      .catch(err => onResults({ status: "error", error: err.message }));
  };

  return (
    <div className="p-4 border-b flex">
      <input
        className="flex-grow p-2 border rounded"
        placeholder="Type your natural-language query..."
        value={prompt}
        onChange={e => setPrompt(e.target.value)}
        onKeyDown={e => e.key === 'Enter' && runQuery()}
      />
      <button
        onClick={runQuery}
        className="ml-2 px-4 py-2 bg-blue-600 text-white rounded"
      >
        Run
      </button>
    </div>
  );
}
