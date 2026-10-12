# Pitch or Ditch

An AI investor that roasts the most ridiculous startup ideas from a live audience, then lets the room decide whether to fund them.

Three people pitch a ridiculous startup idea. For each one, the AI investor **Victoria Vault** gives a first reaction, pokes holes in the idea, proposes a pivot, and asks the audience whether they would fund it. The room votes by show of hands, and a scoreboard crowns the most fundable bad idea.

It runs on **Qwen3-4B, self-hosted with vLLM on Akamai Cloud Kubernetes (LKE)**. Each pitch is one LLM call.

## How it works

```
 Founder pitch (text)
        │
        ▼
 pitch_or_ditch.py ──── one chat completion ────▶  vLLM on Akamai LKE (GPU node)
        │               (OpenAI-compatible API)      model: Qwen/Qwen3-4B
        ▼
 FIRST REACTION · THE CHALLENGE · THE PIVOT · ASK THE AUDIENCE
        │
        ▼
 Audience votes (fund / ditch)  ──▶  Final scoreboard
```

- **One LLM call per pitch.** A system prompt gives the investor a personality and forces a fixed four-section answer, so the output is always readable on stage.
- **Thinking off.** Qwen3 reasons out loud by default. The app turns that off (`enable_thinking: false`) so answers come back in a few seconds.
- **Audience in the loop.** The host types the show-of-hands counts. Ties are called as ties.
- **Plain Python.** Only the official `openai` package. No web framework, no LangChain.

## Example

```
----- PITCH 3 of 3 -----
Founder name: Leo
Your startup idea: Blockchain-verified socks so you never lose one again

FIRST REACTION:
That's a sock in the eye to forgetfulness.

THE CHALLENGE:
- Market: People already lose socks, but few care about blockchain.
- Money: Socks are cheap, but blockchain infrastructure is expensive.
- Risk: Socks can't be divided into tokens, so the model is flawed.

THE PIVOT:
We'll turn socks into NFTs, each with a unique story and QR code. Call it "SockChain."

ASK THE AUDIENCE:
Would you fund SockChain for $50k in equity?

Hands up to FUND it! How many? 2
Hands up to DITCH it! How many? 18

>>> The audience has spoken: DITCHED! (2 fund / 18 ditch)

============================================================
  FINAL SCOREBOARD
============================================================
   15 fund / 4   ditch  |  Jordan: LinkedIn for dogs: professional networking for good boys
    6 fund / 6   ditch  |  Maya: An app that tells you when your toast is done by screaming
    2 fund / 18  ditch  |  Leo: Blockchain-verified socks so you never lose one again
```

## Run it

You need Python 3.10+ and access to the model endpoint.

1. Forward the vLLM service from your Akamai LKE cluster to `localhost:8000`. For the hackathon it ran in the `workshop-s38` namespace; use your own kubeconfig, namespace and service name:

   ```bash
   export KUBECONFIG=/path/to/your-kubeconfig.yaml
   kubectl port-forward -n workshop-s38 svc/vllm 8000:8000
   ```

2. Check that the model is up:

   ```bash
   curl http://localhost:8000/v1/models
   ```

3. Install and run:

   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   .venv/bin/python pitch_or_ditch.py
   ```

If your deployment serves the model under a different name, set it with `QWEN_MODEL=<name from /v1/models>`.

## Customize

At the top of `pitch_or_ditch.py`:

- `SYSTEM_PROMPT` sets the investor's name, personality and the four output sections.
- `NUM_PITCHES` sets how many founders play (default 3).
- `temperature=0.9` in `judge_pitch()` controls how wild the answers get.

## Files

| File | Purpose |
|---|---|
| `pitch_or_ditch.py` | The Pitch or Ditch game |
| `app.py` | A minimal chatbot used to test the model connection |
| `requirements.txt` | Python dependencies (`openai`) |

## Built on Akamai Cloud

- **Model serving:** vLLM on a GPU node pool in Akamai Cloud Kubernetes (LKE).
- **Model:** Qwen3-4B, open weights, no third-party AI API.
- **Access:** OpenAI-compatible `/v1/chat/completions`, so any OpenAI client works by changing the base URL.

The model server was provided by the Akamai Cloud AI workshop's LKE cluster. All code in this repository was written for this project.
