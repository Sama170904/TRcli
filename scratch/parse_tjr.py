import re

with open(r'C:\Users\rsama\Documents\proyecto-geminicli\trading-journal\scratch\raw_transcript.txt', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

# We will search for keywords and print matching lines
keywords = ["welcome", "day ", "what's good", "today we", "chapter", "module", "lesson", "liquidity", "fair value", "order block", "market structure", "risk management"]

for i, line in enumerate(lines):
    m = re.match(r'^\[([\d:]+)\]\s+(.*)', line)
    if m:
        ts = m.group(1)
        text = m.group(2)
        if any(w in text.lower() for w in keywords):
            print(f"Line {i+1} [{ts}]: {text}")
