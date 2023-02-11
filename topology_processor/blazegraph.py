from SPARQLWrapper import SPARQLWrapper, JSON, POST
class BlazegraphConnection(ConnectionInterface):
    sparql_obj: Optional[SPARQLWrapper] = None

    def connect(self):
        if not self.sparql_obj:
            url = self.connection_params.parameters[0].value
            self.sparql_obj = SPARQLWrapper(url)
            self.sparql_obj.setReturnFormat(JSON)

    def disconnect(self):
        self.sparql_obj = None
        
    def execute(self, query_message: str) -> QueryResponse:
        self.connect()
        self.sparql_obj.setQuery(query_message)
        self.sparql_obj.setMethod(POST)
        query_output = self.sparql_obj.query().convert()
        return query_output