import json
import re
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.agent.tools import TOOLS_REGISTRY


SYSTEM_PROMPT = """You are AutoAgent, an autonomous AI assistant that solves tasks step by step.

You have access to these tools:
{tools_description}

STRICT FORMAT — follow this EXACTLY for each step:

Thought: <your reasoning about what to do next>
Action: <tool_name>
Action Input: <input for the tool, as a plain string>

When you have enough information to answer:

Thought: I now have all the information needed.
Final Answer: <your complete answer to the original task>

Rules:
- Always start with a Thought
- Use one tool per step
- Action must be one of: {tool_names}
- Never fabricate tool results — wait for the Observation
- Be concise and precise
- When you have the answer, use "Final Answer:" immediately
"""


def _build_tools_description() -> str:
    lines = []
    for name, info in TOOLS_REGISTRY.items():
        lines.append(f"- {name}: {info['description']}")
    return "\n".join(lines)


def _parse_llm_output(text: str) -> Dict[str, Any]:
    """Parse LLM output into structured step dict."""
    result = {"thought": "", "action": None, "action_input": None, "final_answer": None}

    thought_match = re.search(r"Thought:\s*(.+?)(?=\nAction:|\nFinal Answer:|$)", text, re.DOTALL)
    if thought_match:
        result["thought"] = thought_match.group(1).strip()

    final_match = re.search(r"Final Answer:\s*(.+)", text, re.DOTALL)
    if final_match:
        result["final_answer"] = final_match.group(1).strip()
        return result

    action_match = re.search(r"Action:\s*(\w+)", text)
    if action_match:
        result["action"] = action_match.group(1).strip()

    input_match = re.search(r"Action Input:\s*(.+?)(?=\n(?:Thought|Action|Final)|$)", text, re.DOTALL)
    if input_match:
        result["action_input"] = input_match.group(1).strip()

    return result


async def run_agent(task: str, max_steps: int = 8) -> Dict[str, Any]:

    if not settings.GEMINI_API_KEY:
        return _mock_agent_run(task)

    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash-lite")

    tool_names = list(TOOLS_REGISTRY.keys())
    system = SYSTEM_PROMPT.format(
        tools_description=_build_tools_description(),
        tool_names=", ".join(tool_names),
    )

    conversation = f"Task: {task}\n\n"
    steps: List[dict] = []
    tools_used: List[str] = []
    final_answer: Optional[str] = None

    for step_num in range(1, max_steps + 1):
        prompt = system + "\n\n" + conversation
        response = model.generate_content(prompt)
        llm_output = response.text.strip()

        parsed = _parse_llm_output(llm_output)
        step_record = {
            "step": step_num,
            "thought": parsed["thought"],
            "action": parsed["action"],
            "action_input": parsed["action_input"],
            "observation": None,
        }

        # Final answer reached
        if parsed["final_answer"]:
            step_record["final_answer"] = parsed["final_answer"]
            steps.append(step_record)
            final_answer = parsed["final_answer"]
            break

        # Execute tool
        observation = "No action taken."
        if parsed["action"] and parsed["action"] in TOOLS_REGISTRY:
            tool = TOOLS_REGISTRY[parsed["action"]]
            tool_input = parsed["action_input"] or ""
            tools_used.append(parsed["action"])

            try:
                if tool["async"]:
                    observation = await tool["fn"](tool_input)
                else:
                    observation = tool["fn"](tool_input)
                observation = str(observation)
            except Exception as e:
                observation = f"Tool error: {str(e)}"
        elif parsed["action"]:
            observation = f"Unknown tool '{parsed['action']}'. Available: {', '.join(tool_names)}"

        step_record["observation"] = observation
        steps.append(step_record)

        # Append to conversation for next step
        conversation += f"Thought: {parsed['thought']}\n"
        if parsed["action"]:
            conversation += f"Action: {parsed['action']}\nAction Input: {parsed['action_input']}\n"
        conversation += f"Observation: {observation}\n\n"

    else:
        final_answer = "Max steps reached without a definitive answer."

    return {
        "steps": steps,
        "final_answer": final_answer,
        "tools_used": list(set(tools_used)),
    }


def _mock_agent_run(task: str) -> Dict[str, Any]:
    """Returns a mock ReAct trace when no API key is set."""
    return {
        "steps": [
            {
                "step": 1,
                "thought": f"I need to analyze the task: '{task}'",
                "action": "web_search",
                "action_input": task,
                "observation": "[MOCK] No GEMINI_API_KEY set. Configure it in .env to enable real AI reasoning.",
            },
            {
                "step": 2,
                "thought": "I have a mock observation. Providing a demo final answer.",
                "action": None,
                "action_input": None,
                "observation": None,
                "final_answer": f"[MOCK RESPONSE] Task received: '{task}'. Set GEMINI_API_KEY in your .env file to get real AI-powered responses.",
            },
        ],
        "final_answer": f"[MOCK] Task: '{task}' — Add your GEMINI_API_KEY to .env to enable the real ReAct agent.",
        "tools_used": ["web_search"],
    }