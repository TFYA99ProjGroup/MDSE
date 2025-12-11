import json
good_lines = []
with open("/home/kpj/old_results/old.jsonl","r") as f:
    for line in f:
        d = json.loads(line)
        # print(line)
        # print(d.keys())
        # print(d.get("defect"))
        a=d.get("defect",{})
        if a is None:
            d.pop("defect")
            good_lines.append(d)
            continue
        defect_dict = {**a}
        if not defect_dict:
            continue
        new_dict = {}
        for key in defect_dict.keys():
            new_dict["defect_"+key] = str(defect_dict[key])

        d.pop("defect")
        for key, item in new_dict.items():
            d[key] = item

        good_lines.append(d)

with open("/home/kpj/all_results_v3.jsonl","w", encoding="utf-8") as f:
    for line in good_lines:
        json_str = json.dumps(
                    line,
                    default=lambda o: o.isoformat() if hasattr(o, "isoformat") else o
                )
        f.write(json_str + '\n')
