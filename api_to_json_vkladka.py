import csv
import io
import requests
import json
url = "https://docs.google.com/spreadsheets/d/14Ut2S5x_pPFM8SxMU1VqFv81zIDf86npEUKRPVhDSzk/export?format=csv&gid=0"

response = requests.get(url)
response.raise_for_status()
response.encoding = "utf-8"

reader = csv.reader(io.StringIO(response.text))
i = 0
rows = []
for row in reader:
    rows.append(row[0:])
    i = i + 1
    if i == 14:
        break
dict_raw = {}
for i in range(len(rows)):
    dict_raw[rows[i][0]] = rows[i][1:]
rare_dict = {}
for key, value in dict_raw.items():
    if key == "Місяць":
        continue
    for i in range(len(value)):
        if value[i] == "":
            rare_dict[key] = dict_raw["Місяць"][i-1]
            break
with open("api_to_json_vkladka.json", "w", encoding="utf-8") as f:
    json.dump(rare_dict, f, ensure_ascii=False, indent=2)