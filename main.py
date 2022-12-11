from fastapi import FastAPI
import rdflib

app = FastAPI()

g = rdflib.Graph(store="Oxigraph")
print("Loading graph...")
g.parse("manga.ttl", format="turtle")
print("Graph loaded.")

# search by title query
# Example get: http://localhost:8000/search?query_string=boku


@app.get("/search")
async def search(query_string: str):
    qres = g.query(
        """
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
""" % query_string
    )
    # return as json
    return [row.asdict() for row in qres]


@app.get("/")
def read_root():
    return {"Hello": "World"}
