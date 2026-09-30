import yaml

with open("config/committees.yaml") as f:
    comms = yaml.safe_load(f)["committees"]

with open("config/resources.yaml") as f:
    res = yaml.safe_load(f)["resources"]

res_ids = set(r["id"] for r in res)
missing = []
for c in comms:
    for r in c["wanted_resources"]:
        if r not in res_ids:
            missing.append(f"{c['id']} wants missing resource: {r}")
    for k, v_list in c.get("substitutes", {}).items():
        if k not in res_ids:
            missing.append(f"{c['id']} substitute key missing: {k}")
        for v in v_list:
            if v not in res_ids:
                missing.append(f"{c['id']} substitute value missing: {v}")

if missing:
    for m in missing: print(m)
else:
    print("All resources referenced in committees exist in resources.yaml")
