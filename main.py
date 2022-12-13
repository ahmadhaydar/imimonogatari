from typing import List
import requests as request
from fastapi import FastAPI
from pydantic import BaseModel

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
    return {"data": [dict((k, v["value"]) for k, v in item.items()) for item in response.json()["results"]["bindings"]]}

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
    return response

# get query based on various search filters
# input: [{"type": "title", "value": "boku", "optional": false}, {"type": "genre", "value": "action", "optional": false}, {"type": "author", "value": "kazuma", "optional": false}, {"type": "publisher", "value": "kodansha", "optional": false}]
# output: {
#   "data": [
#     {
#       "s": "http://imimonogatari.org/resource/works/1",
#       "label": "Boku no Hero Academia",
#       "titles": "Boku no Hero Academia, My Hero Academia",
#       "genres": "Action, Comedy, School, Shounen, Super Power",
#       "comment": "Boku no Hero Academia is a Japanese superhero manga series written and illustrated by Kōhei Horikoshi. It has been serialized in Weekly Shōnen Jump since July 2014, and has been collected into 30 tankōbon volumes as of March 2021. The story follows Izuku
# ...
# example curl
# make it accept json
# curl -H "Content-Type: application/json" -X GET -d '[{"type": "title", "value": "boku", "optional": false}, {"type": "genre", "value": "action", "optional": false}, {"type": "author", "value": "kazuma", "optional": false}, {"type": "publisher", "value": "kodansha", "optional": false}]' http://localhost:8000/search/filter


class SearchFilter(BaseModel):
    type: str
    value: str
    optional: bool


class SearchFilterList(BaseModel):
    search_filter: List[SearchFilter]


@app.get("/search/filter")
def search_filter(search_filter: SearchFilterList):
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
    """
    # Add the filters
    for filter in search_filter:
        if filter.optional == False:
            query += """
            FILTER(REGEX(?%s, "%s", "i"))
            """ % (
                filter.type,
                filter.value,
            )
        else:
            query += """
            OPTIONAL {
                FILTER(REGEX(?%s, "%s", "i"))
            }
            """ % (
                filter.type,
                filter.value,
            )
    # Close the query
    query += """
    } GROUP BY ?s ?label ?comment ?malUrl ?publisherLabel
    """
    # Get the response
    response = get_query(query)
    return response
