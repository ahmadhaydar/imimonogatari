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
        "http://localhost:9999/blazegraph/namespace/bds/sparql",
        params={"query": query},
        headers={"Accept": "application/sparql-results+json"},
    )
    return {"data": [dict((k, v["value"]) for k, v in item.items()) for item in response.json()["results"]["bindings"]]}


@app.get("/search")
def search(query_field: str, safe_search: bool = False, limit: int = 100):
    # How to run
    # http://localhost:8000/search?query_field=Naruto
    # Set the query
    sfw_query = ""
    if safe_search == True:
        sfw_query = "?s imip:sfw true ."
    query = """
PREFIX imir:  <http://imimonogatari.org/resource/>
PREFIX imip: <http://imimonogatari.org/property/>
PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX bds:    <http://www.bigdata.com/rdf/search#>
SELECT ?s ?label ?thumbnail (GROUP_CONCAT(DISTINCT ?genre; SEPARATOR = ", ") AS ?genres) (GROUP_CONCAT(DISTINCT ?author; SEPARATOR = ", ") AS ?authors) ?publisherLabel ?rel WHERE {
  {
    SELECT ?s (SUM(?relevance) AS ?rel) WHERE {
      {
        ?s rdf:type imir:Works;
          ?property ?label.
        SERVICE bds:search {
          ?label bds:search "%s";
            bds:relevance ?relevance.
        }
      }
      UNION
      {
        ?s rdf:type imir:Works;
          ?property ?label.
        ?label rdfs:label ?labelInner.
        SERVICE bds:search {
          ?labelInner bds:search "%s";
            bds:relevance ?relevance.
        }
      }
    }
    GROUP BY ?s
    ORDER BY DESC (?rel)
    LIMIT %i
  }
  ?s rdf:type imir:Works;
    rdfs:label ?label;
    imip:genre ?genreId;
    ?subProperty ?authorId.
  ?subProperty rdfs:subPropertyOf imip:author.
  ?authorId rdfs:label ?author.
  ?genreId rdfs:label ?genre.
  OPTIONAL {
    ?s imip:publishedBy ?publisher.
    ?publisher rdfs:label ?publisherLabel.
  }
  OPTIONAL { ?s imip:malPicture ?thumbnail. }
  %s
}
GROUP BY ?s ?label ?comment ?thumbnail ?publisherLabel ?rel
ORDER BY DESC (?rel)
""" % ( query_field, query_field, limit, sfw_query )
    # Get the response
    response = get_query(query)
    return response

@app.get("/details")
def details(uri_field: str):
    # How to run
    # http://localhost:8000/details?uri_field=http://imimonogatari.org/resource/works/1
    # Set the query
    query = """
SELECT ?property ?value WHERE {
  <%s> ?property ?value .
}
    """ % (uri_field)
    # Get the response
    response = get_query(query)
    return response