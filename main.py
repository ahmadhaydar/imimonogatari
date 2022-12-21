from fastapi import FastAPI, Header
from fastapi.responses import RedirectResponse, Response
import requests as request
from typing import Union

app = FastAPI()


@app.get("/resource/{resource_id}")
def resource(resource_id: str, accept: Union[str, None]=Header(default=None)):
    query = """
PREFIX imir:  <http://imimonogatari.org/resource/>
PREFIX imip: <http://imimonogatari.org/property/>
PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?property ?value WHERE {
    imir:%s ?property ?value .
}
    """ % resource_id
    response = request.get(
        "http://localhost:9999/blazegraph/namespace/bds/sparql",
        params={"query": query},
        headers={"Accept": accept})
    return Response(content=response.content, media_type=accept)
