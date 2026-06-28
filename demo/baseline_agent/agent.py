"""A tiny stand-in 'agent under test' for the demo.

It does a 'tool call' (lookup) and an 'LLM step' (phrasing), then prints a final answer.
Controlled by SCENARIO env var so we can produce three capsules from one file:

  (unset)     -> baseline
  SCENARIO=flaky       -> same tool result + output, different model phrasing (non-deterministic)
  SCENARIO=regression  -> tool result changed -> different final output (real behavior change)

Day-1 TODO: replace the simulated steps with a real LLM/tool agent so NovaFabric captures
genuine model-calls.jsonl / tool-calls.jsonl. The simulation here just guarantees the demo
has clear flaky vs regression signal without needing API keys.
"""
import os
import random


def lookup_tax_rate(country: str) -> float:
    """The 'tool'. In the regression scenario its result changes."""
    base = {"IT": 0.22, "DE": 0.19, "FR": 0.20}[country]
    if os.environ.get("SCENARIO") == "regression":
        return base + 0.01  # a real behavior change -> regression
    return base


def phrase_answer(rate: float) -> str:
    """The 'LLM step'. In the flaky scenario only the wording varies."""
    templates = [
        "The applicable VAT rate is {p:.0%}.",
        "VAT comes out to {p:.0%} for this order.",
        "You should apply a {p:.0%} VAT.",
    ]
    if os.environ.get("SCENARIO") == "flaky":
        return random.choice(templates).format(p=rate)  # different text, same meaning
    return templates[0].format(p=rate)


def main() -> None:
    country = "IT"
    rate = lookup_tax_rate(country)        # tool call
    answer = phrase_answer(rate)           # model step
    # final output: in baseline+flaky the NUMBER is identical; in regression it changes
    print(f"FINAL: country={country} rate={rate:.2f} :: {answer}")


if __name__ == "__main__":
    main()
