import json

with open('faq.json', encoding='utf-8') as f:
    data = json.load(f)

def fix(s):
    if isinstance(s, str):
        try:
            return s.encode('latin1').decode('utf-8')
        except Exception:
            return s
    return s

def walk(o):
    if isinstance(o, dict):
        return {k: walk(v) for k, v in o.items()}
    if isinstance(o, list):
        return [walk(v) for v in o]
    return fix(o)

data = walk(data)

with open('faq.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Corrige !")
