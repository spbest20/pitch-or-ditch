"""A simple terminal chatbot for the Qwen3-4B model hosted on Akamai Cloud.

The model runs on Akamai Cloud Kubernetes (served by vLLM) and is reached through
a kubectl port-forward on localhost:8000. vLLM speaks the OpenAI API, so the
official `openai` package works as the client.
"""

import os

import openai
from openai import OpenAI

# --- Connection settings ---------------------------------------------------
BASE_URL = "http://localhost:8000/v1"
API_KEY = "not-needed"  # vLLM does not check the key, but the client requires one
# The name must match what the server reports at /v1/models. Override it with
# the QWEN_MODEL environment variable if the deployment changes.
MODEL = os.environ.get("QWEN_MODEL", "Qwen/Qwen3-4B")

# --- Create the client -----------------------------------------------------
# timeout: give up after 60 seconds instead of waiting forever.
# max_retries=0: report a failure right away rather than silently retrying.
client = OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=60, max_retries=0)


def ask(question: str) -> str:
    """Send one question to the model and return its answer."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": question}],
        max_tokens=512,
        # Qwen3 "thinks out loud" by default. This vLLM option turns that off
        # so we get a short, direct answer.
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
    return response.choices[0].message.content.strip()


def main() -> None:
    print(f"Chatting with {MODEL} at {BASE_URL}")
    print("Type your question and press Enter. Type 'exit' to quit.\n")

    # Keep asking questions until the user types 'exit'.
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if question.lower() == "exit":
            break
        if not question:
            continue

        # Send the question and print the answer, handling common failures.
        try:
            print(f"\nQwen: {ask(question)}\n")
        except openai.APITimeoutError:
            print("\n[Error] The model took too long to answer. Try again.\n")
        except openai.APIConnectionError:
            print(
                f"\n[Error] Could not connect to {BASE_URL}. "
                "Is the kubectl port-forward still running?\n"
            )
        except openai.APIStatusError as err:
            print(f"\n[Error] The API returned status {err.status_code}: {err.message}\n")

    print("Goodbye!")


if __name__ == "__main__":
    main()
