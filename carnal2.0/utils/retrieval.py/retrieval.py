import os, re, glob

def search_notes(query, top_k=3):
    hits = []
    for path in glob.glob("knowledge/docs/**/*", recursive=True):
        if os.path.isdir(path): 
            continue
        try:
            text = open(path, "r", encoding="utf-8", errors="ignore").read()
        except:
            continue
        score = len(re.findall(query, text, flags=re.I))
        if score:
            hits.append((score, path, text[:300]))
    return [dict(path=p, snippet=t) for _, p, t in sorted(hits, reverse=True)[:top_k]]