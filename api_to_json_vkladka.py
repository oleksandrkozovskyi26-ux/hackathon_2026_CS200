import csv
import io
import requests
import json

url = "https://docs.google.com/spreadsheets/d/14Ut2S5x_pPFM8SxMU1VqFv81zIDf86npEUKRPVhDSzk/export?format=csv&gid=0"
response = requests.get(url)
response.raise_for_status()
response.encoding = "utf-8"
reader = csv.reader(io.StringIO(response.text))

rows = []
for i, row in enumerate(reader):
    if i >= 14:
        break
    rows.append(row)

raw_dict = {row[0]: row[1:] for row in rows if row}
months = raw_dict.get("Місяць", [])
done_data = {}
for category, values in raw_dict.items():
    if category == "Місяць":
        continue

    for i, value in enumerate(values):
        if value == "":
            if i > 0 and i - 1 < len(months):
                done_data[category] = months[i - 1]
            break

with open("api_to_json_vkladka.json", "w", encoding="utf-8") as f:
    json.dump(done_data, f, ensure_ascii=False, indent=2)