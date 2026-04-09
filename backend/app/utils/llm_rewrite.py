import json
import re
from backend.llm import llm


def _extract_json(text: str):
    """Extract JSON object even if LLM adds extra text/code blocks."""
    if not text:
        return None

    text = text.strip()

    # 1) Direct JSON
    try:
        return json.loads(text)
    except:
        pass

    # 2) If inside ```json ... ```
    codeblock = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if codeblock:
        try:
            return json.loads(codeblock.group(1))
        except:
            pass

    # 3) Extract first {...} from output
    obj = re.search(r"(\{.*\})", text, re.DOTALL)
    if obj:
        try:
            return json.loads(obj.group(1))
        except:
            pass

    return None


def llm_rewrite(query: str) -> str:
    prompt = f"""
Rewrite the query to maximize retrieval accuracy.
Do NOT answer the question.

Respond ONLY in JSON:
{{
  "rewritten_query": "..."
}}

Query:
{query}
""".strip()

    output = llm.invoke(prompt)

    data = _extract_json(output)

    # ✅ Fallback: return raw output or original query if JSON fails
    if not data or "rewritten_query" not in data:
        cleaned = (output or "").strip()
        return cleaned if cleaned else query

    rewritten = str(data["rewritten_query"]).strip()
    return rewritten if rewritten else query
