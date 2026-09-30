import urllib.request, json

queries = ['Patna', 'Bengaluru', 'London']
for q in queries:
    url = f'http://127.0.0.1:8000/api/location/search?q={q}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())
            print(f'Search query [{q}]: results = {len(data.get("results", []))}')
            for item in data.get('results', []):
                print(f'   -> {item.get("title")} ({item.get("lat")}, {item.get("lon")})')
    except Exception as e:
        print(f'Error for {q}:', e)

# Test reverse geocode guard
for coords in [(25.61, 85.14), (52.96, 110.39)]:
    rev_url = f'http://127.0.0.1:8000/api/location/reverse?lat={coords[0]}&lon={coords[1]}'
    with urllib.request.urlopen(rev_url) as r:
        rev_data = json.loads(r.read())
        print(f'Reverse geocode {coords}: status={rev_data.get("status")} city={rev_data.get("city")}')
