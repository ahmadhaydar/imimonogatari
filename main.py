import requests as request
from fastapi import FastAPI

app = FastAPI()


@app.get("/ping")
def read_root():
    return "pong"


def get_query(query):
    # result set in JSON using Accept headers, Accept:application/sparql-results+json
    # do GET request blazegraph endpoint
    response = request.get(
        "http://localhost:9999/blazegraph/namespace/kb/sparql",
        params={"query": query},
        headers={"Accept": "application/sparql-results+json"},
    )
    return response

# How to run
# http://localhost:8000/search?search_label=boku


@app.get("/search")
def search(search_label: str):
    # Set the query
    query = """
    PREFIX imir:  <http://imimonogatari.org/resource/>
PREFIX imip: <http://imimonogatari.org/property/>
PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?s ?label (group_concat(DISTINCT ?title;separator=", ") as ?titles) (group_concat(DISTINCT ?genre;separator=", ") as ?genres) ?comment ?malUrl (group_concat(DISTINCT ?author;separator=", ") as ?authors) ?publisherLabel WHERE {
  ?s rdf:type imir:Works;
    rdfs:label ?label;
    rdfs:comment ?comment;
    imip:title ?title;
    imip:genre ?genreId;
    imip:malUrl ?malUrl.
  
  ?s ?subProperty ?authorId .
  ?subProperty rdfs:subPropertyOf imip:author .
  ?authorId rdfs:label ?author .
  
  ?genreId rdfs:label ?genre .
  
  OPTIONAL {
    ?s imip:publishedBy ?publisher .
    ?publisher rdfs:label ?publisherLabel .
  }
  
  FILTER(REGEX(?title, "%s", "i"))
} GROUP BY ?s ?label ?comment ?malUrl ?publisherLabel
""" % search_label
    # Get the response
    response = get_query(query)
    return {"data": [dict((k, v["value"]) for k, v in item.items()) for item in response.json()["results"]["bindings"]]}
