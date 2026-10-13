import json
import statistics
import time
from app import find_books, shortest_path

QUERIES = ["machine learning", "database", "computer networks", "artificial intelligence", "algorithms", "AI", "DBMS", "computer vision"]
TARGETS = ["CS_SHELF", "AI_SHELF", "DB_SHELF", "NETWORK_SHELF"]

search_results=[]
for q in QUERIES:
    samples=[]
    results=None
    for _ in range(20):
        t=time.perf_counter(); results=find_books(q); samples.append((time.perf_counter()-t)*1000)
    search_results.append({"query":q,"avg_ms":round(statistics.mean(samples),3),"min_ms":round(min(samples),3),"max_ms":round(max(samples),3),"results":len(results),"top_result":results[0]["title"] if results else None})

route_results=[]
for target in TARGETS:
    samples=[]; path=[]; distance=0
    for _ in range(100):
        t=time.perf_counter(); path,distance=shortest_path("ENTRANCE",target); samples.append((time.perf_counter()-t)*1000)
    route_results.append({"target":target,"avg_ms":round(statistics.mean(samples),6),"distance_units":distance,"waypoints":len(path)})

print(json.dumps({"search_evaluation":search_results,"route_evaluation":route_results},indent=2))
