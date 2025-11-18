from typing import Dict, Any, Optional
import os
from bs4 import BeautifulSoup

from .knowledge_base import KnowledgeBase
from .llm import LLMProvider


SYSTEM_PROMPT_SELENIUM = (
    "You are a Selenium (Python) expert. Generate clean, runnable code. "
    "Use IDs, names, or CSS selectors present in the actual HTML provided. "
)


def _get_checkout_file_url() -> str:
    # Construct local file URL for assets/checkout.html
    here = os.path.dirname(os.path.dirname(__file__))
    path = os.path.abspath(os.path.join(here, "assets", "checkout.html"))
    return f"file:///{path.replace('\\', '/')}"


def _extract_ids(html: str):
    soup = BeautifulSoup(html, "lxml")
    ids = [e.get("id") for e in soup.find_all(attrs={"id": True})]
    return [i for i in ids if i]


def generate_selenium_script(test_case: Dict[str, Any], html_text: str, kb: KnowledgeBase, llm: LLMProvider) -> str:
    # Compose context for LLM (or fallback) including available IDs
    ids = _extract_ids(html_text)
    url = _get_checkout_file_url()
    scenario = test_case.get("Test_Scenario") or test_case.get("Test_Scenario".lower()) or "Run selected test scenario."
    feature = test_case.get("Feature", "Checkout")

    context = (
        f"HTML IDs available: {', '.join(ids)}\n"
        f"Open URL: {url}\n"
        f"Feature: {feature}\n"
        f"Scenario: {scenario}\n"
    )
    prompt = (
        f"Generate a Python Selenium script that: \n"
        f"- Opens {url}\n"
        f"- Executes scenario: {scenario}\n"
        f"- Uses present HTML selectors (IDs above)\n"
        f"- Asserts expected results based on docs\n"
        f"Context:\n{context}"
    )

    # Fallback script if no LLM: deterministic generation for common features
    base_script = f"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()
driver.get("{url}")

wait = WebDriverWait(driver, 10)

# Example actions: add items, apply discount, fill form, choose shipping/payment, pay
driver.find_element(By.ID, "add-item-1").click()
driver.find_element(By.ID, "add-item-2").click()

# Apply discount SAVE15 if scenario mentions discount
try:
    discount_input = driver.find_element(By.ID, "discount_code")
    discount_input.clear()
    discount_input.send_keys("SAVE15")
    driver.find_element(By.ID, "apply_coupon").click()
except Exception:
    pass

# Choose express shipping if present
try:
    driver.find_element(By.ID, "shipping_express").click()
except Exception:
    pass

# Fill required fields
driver.find_element(By.ID, "name").send_keys("John Tester")
driver.find_element(By.ID, "email").send_keys("john.tester@example.com")
driver.find_element(By.ID, "address").send_keys("123 Test Lane")

# Pay now
driver.find_element(By.ID, "pay_now").click()

# Assert success message
status = wait.until(EC.presence_of_element_located((By.ID, "payment_status")))
assert "Payment Successful!" in status.text

driver.quit()
"""

    llm_out = llm.generate(prompt, system=SYSTEM_PROMPT_SELENIUM)
    # If the LLM returned only commentary fallback, return base_script
    if llm_out.strip().startswith("# Fallback") or len(llm_out.strip()) < 40:
        return base_script

    # If LLM returns code fenced blocks, try to extract python
    code = llm_out
    if "```" in code:
        parts = code.split("```")
        # try to find python block
        for i in range(len(parts)-1):
            if parts[i].strip().lower().startswith("python"):
                return parts[i+1]
        # otherwise take the last fence content
        return parts[-2] if len(parts) >= 2 else base_script
    return code