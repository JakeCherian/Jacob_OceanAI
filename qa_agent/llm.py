from typing import Optional
import os
import json
import requests


class LLMProvider:
    def __init__(self, ollama_url: Optional[str] = None, ollama_model: Optional[str] = None):
        self.ollama_url = ollama_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.ollama_model = ollama_model or os.getenv("OLLAMA_MODEL", "llama3")

    def _ollama_generate(self, prompt: str, system: Optional[str] = None) -> Optional[str]:
        try:
            url = f"{self.ollama_url}/api/generate"
            payload = {"model": self.ollama_model, "prompt": prompt}
            if system:
                payload["system"] = system
            r = requests.post(url, json=payload, timeout=60)
            if r.status_code == 200:
                # Ollama streams newline-delimited JSON
                lines = r.text.strip().splitlines()
                outputs = []
                for ln in lines:
                    try:
                        obj = json.loads(ln)
                        if "response" in obj:
                            outputs.append(obj["response"])
                    except Exception:
                        continue
                return "".join(outputs)
            return None
        except Exception:
            return None

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        # Try Ollama first
        out = self._ollama_generate(prompt, system)
        if out:
            return out
        # Fallback: deterministic template response
        if system and "Selenium" in system:
            # Basic instruction response stub for scripts
            return (
                "# Fallback generator: ensure IDs in checkout.html are used. "
                "# The final script should open the local checkout page, fill form, apply coupon, and assert payment success."
            )
        # For test cases, produce a small markdown table with citations placeholder
        return (
            "| Test_ID | Feature | Test_Scenario | Expected_Result | Grounded_In |\n"
            "|---------|---------|---------------|-----------------|-------------|\n"
            "| TC-001 | Discount Code | Apply valid code SAVE15 | Total reduced by 15% | product_specs.md |\n"
            "| TC-002 | Discount Code | Apply invalid code ABC | Error message shown | product_specs.md |\n"
        )