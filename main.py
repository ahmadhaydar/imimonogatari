from fastapi import FastAPI, Header, Query
from fastapi.responses import RedirectResponse, Response, JSONResponse
import requests as request
from typing import Union, List
from pydantic import BaseModel

app = FastAPI()


@app.get("/resource/{resource_id}")
def resource(resource_id: str, accept: Union[str, None]=Header(default=None)):
    query = """
    
SELECT ?property ?value WHERE {
    <http://imimonogatari.org/resource/%s> ?property ?value .
}
    """ % resource_id
    response = request.get(
        "http://localhost:9999/blazegraph/namespace/bds/sparql",
        params={"query": query},
        headers={"Accept": accept})
    return Response(content=response.content, media_type=accept)

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

@app.get("/search/filter")
def search_filter(search_title: str = Query(default=None), search_publisher: str = Query(default=None), search_genre: List[str] = Query(default=[]),
search_author: List[str] = Query(default=[]), offset: int = Query(default=0), safe_search: bool = False):
    if search_title == None and search_publisher == None and len(search_genre) == 0 and len(search_author) == 0:
      return JSONResponse(status_code=400, content={"message": "Filter arguments not filled"})

    #Set the query
    query = """
        PREFIX imir:  <http://imimonogatari.org/resource/>
        PREFIX imip: <http://imimonogatari.org/property/>
        PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX bds: <http://www.bigdata.com/rdf/search#>

        SELECT DISTINCT ?s ?label ?thumbnail ?comment (GROUP_CONCAT(DISTINCT ?title;separator=", ") as ?titles) (GROUP_CONCAT(DISTINCT ?genre; SEPARATOR = ", ") AS ?genres) (GROUP_CONCAT(DISTINCT ?author; SEPARATOR = ", ") AS ?authors) ?malUrl ?publisherLabel where {
          
          ?s rdf:type imir:Works ;
            rdfs:label ?label ;
            rdfs:comment ?comment;
            imip:title ?title;
            imip:genre ?genreId ;
            imip:malUrl ?malUrl ;
            ?subProperty ?authorId .
          ?subProperty rdfs:subPropertyOf imip:author .
          ?authorId rdfs:label ?author .
          ?genreId rdfs:label ?genre . \n
    """
    if safe_search:
      query += "?s imip:sfw true . \n"
    if search_title:
      query += """ 
          SERVICE bds:search {?title bds:search "%s"; bds:relevance ?titRel} \n""" %search_title
    if search_publisher:
      query += """  
          ?s imip:publishedBy ?publisher.
          ?publisher rdfs:label ?publisherLabel.
          SERVICE bds:search {?publisherLabel bds:search "%s"; bds:relevance ?pubRel} \n""" %search_publisher
    else:
      query += """
          OPTIONAL {
            ?s imip:publishedBy ?publisher.
            ?publisher rdfs:label ?publisherLabel. \n
          }
      """
    query += """   
          OPTIONAL { ?s imip:malPicture ?thumbnail. } \n"""

    # Add the filters
    for author in search_author:
      query += """
          {SELECT ?s ?authRel WHERE {
            ?s rdf:type imir:Works;
              ?subProperty ?authorId .
            ?subProperty rdfs:subPropertyOf imip:author .
            ?authorId rdfs:label ?author .
            
            service bds:search {
                ?author bds:search "%s" ; bds:relevance ?authRel .
            }
          } GROUP BY ?s ?authRel} \n
            """ % (author)
    
    for genre in search_genre:
      query += """
          {SELECT ?s WHERE {
            ?s rdf:type imir:Works;
              imip:genre ?genreId .
            ?genreId rdfs:label ?genre .
            
            service bds:search {
                ?genre bds:search "%s" .
            }
          } GROUP BY ?s} \n
            """ % (genre)

    # Close the query
    query += "} GROUP BY ?s ?label ?thumbnail ?comment ?malUrl ?publisherLabel "

    # Order by and Offset
    if search_title:
      query += "ORDER BY DESC(MAX(?titRel))"
    elif search_author:
      query += "ORDER BY DESC(MAX(?authRel))"
    elif search_publisher:
      query += "ORDER BY DESC(?pubRel)"
    query += f"LIMIT 100 OFFSET {offset}"

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
