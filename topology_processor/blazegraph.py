from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List
from SPARQLWrapper import SPARQLWrapper, JSON, POST
import sys

        
class BlazegraphConnection():
    sparql_obj: Optional[SPARQLWrapper] = None

    def connect(self):
        if not self.sparql_obj:
            path = sys.argv[0]
            print(path)
            if "/gridappsd/services/gridappsd-topology-processor" in path:
                url = "http://blazegraph:8080/bigdata/namespace/kb/sparql"
            else:
                url = "http://localhost:8889/bigdata/namespace/kb/sparql"
                
            self.sparql_obj = SPARQLWrapper(url)
            self.sparql_obj.setReturnFormat(JSON)

    def disconnect(self):
        self.sparql_obj = None
        
    def execute(self, query_message: str) -> QueryResponse:
        self.connect()
        self.sparql_obj.setQuery(query_message)
        self.sparql_obj.setMethod(POST)
        query_output = self.sparql_obj.query().convert()
        return query_output['results']['bindings']