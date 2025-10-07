import os, re, glob, json
from collections import Counter

LOG_DIR = "logs"
MIRROR_BUDGET_WORDS = 120
EMOTION_LEXICON = {
    "anger","angry","fear","afraid","anxious","anxiety","sad","grief","guilt",
    "shame","envy","jealous","fatigue","tired","overwhelm","panic","stress",
    "frustration","confusion","lonely","isolation","numb"
}

def read_file(p):
    with open(p, "r", encoding="utf-8") as f:
        return f.read()

def extract_field(text, field):
    pat = rf"^{field}\s*(.*)$"
    m = re.search(pat, text, flags=re.IGNORECASE | re.MULTILINE)
    return (m.group(1).strip() if m else "")

def extract_block(text, header):
    pat = rf"^{header}\s*(.*?)(?:\n\s*\n|$)"
    m = re.search(pat, text, flags=re.IGNORECASE | re.DOTALL | re.MULTILINE)
    return (m.group(1).strip() if m else "")

def word_count(s):
    return len(re.findall(r"\b\w+\b", s))

def affective_scatter(signal_line):
    tokens = {w.lower().strip(",.;:!?") for w in signal_line.split()}
    return len(tokens & EMOTION_LEXICON)

def compute_metrics(log_text):
    signal = extract_field(log_text, "Signal:")
    mirror = extract_block(log_text, "Mirror_Summary")
    audit  = extract_block(log_text, "Audit_Pass")
    synth  = extract_block(log_text, "Synthesis")

    mirror_wc = word_count(mirror)
    tlr = max(0, mirror_wc - MIRROR_BUDGET_WORDS)
    sa = affective_scatter(signal)
    has_all = all([mirror.strip(), audit.strip(), synth.strip()])

    return {
        "TLR": tlr,
        "Sa": sa,
        "has_all_sections": has_all
    }

def main():
    files = sorted(glob.glob(os.path.join(LOG_DIR, "*.md")))
    if not files:
        print("No logs found in ./logs/")
        return

    results = []
    complete = 0
    for p in files:
        text = read_file(p)
        metrics = compute_metrics(text)
        metrics["file"] = os.path.basename(p)
        results.append(metrics)
        if metrics["has_all_sections"]:
            complete += 1

    rci = complete / len(files)
    avg_tlr = sum(r["TLR"] for r in results) / len(files)
    avg_sa  = sum(r["Sa"] for r in results) / len(files)

    summary = {
        "files_count": len(files),
        "RCI": round(rci, 3),
        "avg_TLR": round(avg_tlr, 2),
        "avg_Sa": round(avg_sa, 2),
        "targets": {
            "RCI": "≥0.70",
            "avg_TLR": "→0",
            "avg_Sa": "<2"
        },
        "per_file": results
    }

    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
