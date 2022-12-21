from fastapi import FastAPI, Header
from fastapi.responses import RedirectResponse, Response
import requests as request
from typing import Union

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
