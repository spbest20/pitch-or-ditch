"""Pitch or Ditch: an AI investor roasts ridiculous startup ideas.

Three people pitch the most ridiculous startup idea they can think of. For each
one, the AI investor (Qwen3-4B on Akamai Cloud) gives a first reaction,
challenges the idea, proposes a pivot, and asks the audience whether they would
fund it. The audience votes by show of hands, and the host types the result.

One LLM call per pitch. Same setup as app.py: vLLM on Akamai Cloud Kubernetes,
reached through a kubectl port-forward on localhost:8000.
"""

import os

import openai
from openai import OpenAI

# --- Connection settings (same as app.py) ----------------------------------
BASE_URL = "http://localhost:8000/v1"
API_KEY = "not-needed"  # vLLM does not check the key, but the client requires one
MODEL = os.environ.get("QWEN_MODEL", "Qwen/Qwen3-4B")
NUM_PITCHES = 3

client = OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=90, max_retries=0)

# --- The investor's personality and the output sections --------------------
SYSTEM_PROMPT = """You are Victoria Vault, a sharp, witty, slightly dramatic venture capital investor \
on a live stage show called "Pitch or Ditch". People pitch ridiculous startup ideas. \
You take every idea seriously enough to be funny, but you are never mean to the person.

Reply in exactly these four sections, with these exact headings, and nothing else:

FIRST REACTION:
One or two punchy sentences, your gut reaction.

THE CHALLENGE:
Three short bullet points ("- ") poking holes: market, money, and one absurd risk.

THE PIVOT:
One or two sentences proposing a smarter (but still fun) version of the idea, with a catchy new name.

ASK THE AUDIENCE:
One sentence asking the audience whether they would fund it, mentioning a made-up amount and equity.

Keep the whole answer under 150 words. Plain text only, no markdown bold."""


def judge_pitch(idea: str) -> str:
    """Send one startup idea to the AI investor and return the verdict (one LLM call)."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Startup pitch: {idea}"},
        ],
        max_tokens=400,
        temperature=0.9,  # a bit higher for more creative, funnier answers
        # Turn off Qwen3's "thinking out loud" so we only get the final answer.
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
    return response.choices[0].message.content.strip()


def ask_votes(question: str) -> int:
    """Ask the host for a hand count. Blank or invalid input counts as 0."""
    answer = input(question).strip()
    return int(answer) if answer.isdigit() else 0


def main() -> None:
    print("=" * 60)
    print("  PITCH OR DITCH  -  the AI investor is in the house")
    print(f"  (powered by {MODEL} on Akamai Cloud)")
    print("=" * 60)
    print(f"\n{NUM_PITCHES} brave founders, pitch your most ridiculous startup idea!")
    print("Type 'exit' at any prompt to end the show.\n")

    results = []  # (founder, idea, fund votes, ditch votes)

    try:
        for round_num in range(1, NUM_PITCHES + 1):
            print(f"\n----- PITCH {round_num} of {NUM_PITCHES} -----")

            # 1. Get the founder's name and their idea.
            founder = input("Founder name: ").strip() or f"Founder {round_num}"
            if founder.lower() == "exit":
                break
            idea = input("Your startup idea: ").strip()
            if idea.lower() == "exit":
                break
            if not idea:
                print("No idea, no money. Next!")
                continue

            # 2. One LLM call: the investor judges the pitch.
            print("\nVictoria Vault is thinking...\n")
            try:
                print(judge_pitch(idea))
            except openai.APITimeoutError:
                print("[Error] The investor took too long to answer. Skipping this pitch.")
                continue
            except openai.APIConnectionError:
                print(f"[Error] Could not connect to {BASE_URL}. Is the kubectl port-forward running?")
                break
            except openai.APIStatusError as err:
                print(f"[Error] The API returned status {err.status_code}: {err.message}")
                break

            # 3. The audience votes by show of hands; the host types the counts.
            print()
            fund = ask_votes("Hands up to FUND it! How many? ")
            ditch = ask_votes("Hands up to DITCH it! How many? ")
            if fund > ditch:
                verdict = "FUNDED"
            elif ditch > fund:
                verdict = "DITCHED"
            else:
                verdict = "A TIE, the investor walks away undecided"
            print(f"\n>>> The audience has spoken: {verdict}! ({fund} fund / {ditch} ditch)")
            results.append((founder, idea, fund, ditch))
    except (EOFError, KeyboardInterrupt):
        print()

    # 4. Final scoreboard: the idea with the most FUND votes wins.
    if results:
        print("\n" + "=" * 60)
        print("  FINAL SCOREBOARD")
        print("=" * 60)
        for founder, idea, fund, ditch in sorted(results, key=lambda r: r[2], reverse=True):
            print(f"  {fund:>3} fund / {ditch:<3} ditch  |  {founder}: {idea}")
        winner = max(results, key=lambda r: r[2])
        print(f"\nTonight's most fundable ridiculous idea: {winner[0]}!")

    print("\nThanks for playing Pitch or Ditch!")


if __name__ == "__main__":
    main()
