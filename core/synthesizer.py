"""
MoE Synthesizer — Mixture of Experts Judge.

Takes N candidate responses from N independent Gemini sessions,
uses the Leader cookie (slot #1) to call Gemini one final time
and produce a synthesized, superior answer.

This is the component that turns a simple multiplexer into a
quality amplifier: more sessions = better answers, not just faster.
"""

from gemini import Gemini


MOE_JUDGE_PROMPT = """You are a Mixture of Experts (MoE) Judge.

You have received {count} candidate responses to the SAME task from {count} independent AI sessions. Each session had its own context and may have produced a different answer.

YOUR MISSION:
1. Read and evaluate ALL candidate responses below.
2. Assess each for: correctness, completeness, code quality (if applicable), clarity, and depth.
3. Either SELECT the single best response OR SYNTHESIZE a superior answer by combining the strongest elements from multiple candidates.
4. Return ONLY the final, definitive answer. Do NOT include meta-commentary about the selection process.

=== ORIGINAL TASK ===
{task}

=== CANDIDATE RESPONSES ===
{candidates}

=== YOUR SYNTHESIZED ANSWER ==="""


class Synthesizer:
    """Uses the Leader's Gemini session to judge and merge worker responses."""

    def __init__(self, leader_cookies):
        """
        Args:
            leader_cookies: dict of cookies for the leader account (slot #1)
        """
        if not leader_cookies:
            raise ValueError("Synthesizer requires leader cookies (slot #1)")
        self._client = Gemini(cookies=leader_cookies)

    def synthesize(self, task_instruction, candidate_responses):
        """
        Judge N candidate responses and return the best/synthesized answer.

        Args:
            task_instruction: The original task/prompt that was sent to workers
            candidate_responses: list of dicts [{worker_id, response, duration_s}]

        Returns:
            str: The synthesized best answer
        """
        if not candidate_responses:
            return "ERROR: No candidate responses to synthesize."

        # If only one response, return it directly (no need to judge)
        if len(candidate_responses) == 1:
            return candidate_responses[0]["response"]

        # Build the candidates block
        candidates_text = ""
        for i, candidate in enumerate(candidate_responses, 1):
            worker_id = candidate.get("worker_id", f"W{i}")
            response = candidate.get("response", "")
            duration = candidate.get("duration_s", "?")
            candidates_text += (
                f"\n--- [Worker {worker_id}] "
                f"(completed in {duration}s) ---\n"
                f"{response}\n"
            )

        prompt = MOE_JUDGE_PROMPT.format(
            count=len(candidate_responses),
            task=task_instruction,
            candidates=candidates_text,
        )

        try:
            response = self._client.generate_content(prompt)
            return response.text
        except Exception as e:
            # Fallback: return the longest response (heuristic for most complete)
            print(f"\u26a0\ufe0f  [SYNTHESIZER] Gemini call failed: {e}")
            print("    Falling back to longest-response heuristic...")
            best = max(candidate_responses, key=lambda c: len(c.get("response", "")))
            return best["response"]

    def judge_quality(self, candidate_responses):
        """
        Returns a quick ranking of candidates without full synthesis.
        Useful for debugging/logging.
        """
        ranked = sorted(
            candidate_responses,
            key=lambda c: len(c.get("response", "")),
            reverse=True,
        )
        return [
            {
                "worker_id": c.get("worker_id"),
                "response_length": len(c.get("response", "")),
                "duration_s": c.get("duration_s", "?"),
            }
            for c in ranked
        ]
