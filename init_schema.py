from typing import Annotated
import typer
import permify
from permify.api.schema_api import SchemaApi
from permify.models.schema_write_body import SchemaWriteBody

configuration = permify.Configuration(
    host="http://localhost:3476"
)

def init(schema_text: Annotated[typer.FileText, typer.Option]):
    schema = schema_text.read()
    with permify.ApiClient(configuration) as api_client:
        schema_api = SchemaApi(api_client)
        response = schema_api.schemas_write("t1", SchemaWriteBody.from_dict({"schema": str(schema)}))
        print(response)

if __name__ == "__main__":
    typer.run(init)