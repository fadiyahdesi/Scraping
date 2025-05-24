from fastapi import FastAPI, Query, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime
from collections import Counter
import json

load_dotenv()
app = FastAPI()

# Mount static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja templates
templates = Jinja2Templates(directory="templates")

# Mongo connection
MONGO_URI = os.getenv("ATLAS_MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["fafa"]
collection = db["scraping"]

STOPWORDS = set([
    'dan', 'yang', 'di', 'ke', 'dari', 'pada', 'untuk', 'dengan', 'atau', 'itu', 'dalam', 'adalah', 'ini', 'sebagai','tersebut'
])

@app.get("/")
def redirect_to_dashboard():
    return RedirectResponse(url="/dashboard")

@app.get("/dashboard")
def dashboard(request: Request, source: list[str] = Query(default=['Haibunda', 'Wikipedia', 'Hellosehat'])):
    query = {"source": {"$in": source}} if source else {}
    articles = list(collection.find(query))

    # Keyword analysis
    all_keywords = []
    for a in articles:
        kws = a.get("keywords", [])
        filtered = [kw.lower() for kw in kws if kw.lower() not in STOPWORDS]
        all_keywords.extend(filtered)

    keyword_counts = dict(Counter(all_keywords).most_common(10))
    wordcloud_data = [[k, v] for k, v in keyword_counts.items()]
    article_counts = dict(Counter([a.get("source", "Unknown") for a in articles]))

    last_update = max([a["_id"].generation_time for a in articles]).isoformat() if articles else datetime.now().isoformat()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "last_update": last_update,
        "keywords": keyword_counts,
        "wordcloud_data": wordcloud_data,
        "article_counts": article_counts,
        "selected_sources": source
    })
