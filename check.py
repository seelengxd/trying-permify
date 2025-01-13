import permify as p
from typer import Typer
from src.entities import ORGANISATION, PROBLEMS, PROJECT, USERS, ROLES
from permify.models.read_attributes_body import ReadAttributesBody
from permify.models.read_relationships_body import ReadRelationshipsBody
from rich import print
from rich.table import Table
from rich.console import Console

app = Typer()

configuration = p.Configuration(host="http://localhost:3476")

TENANT_ID = "t1"
METADATA = {"schema_version": "ctu0e6kb5eec73d9vh10"}


@app.command()
def read():
    with p.ApiClient(configuration) as api_client:
        data_api = p.DataApi(api_client)
        attributes = data_api.data_attributes_read(
            TENANT_ID,
            ReadAttributesBody(metadata=METADATA, filter={}),
        )
        print(attributes)

        relations = data_api.data_relationships_read(
            TENANT_ID,
            ReadRelationshipsBody(
                metadata=METADATA,
                filter={},
            ),
        )
        print(relations)


def check_permission(entity, permission, subject) -> bool:
    with p.ApiClient(configuration) as api_client:
        permissions_api = p.PermissionApi(api_client)
        result = permissions_api.permissions_check(
            TENANT_ID,
            p.CheckBody(
                metadata={**METADATA, "depth": 100},
                entity=entity,
                permission=permission,
                subject=subject,
            ),
        )
        return result.can == p.CheckResult.CHECK_RESULT_ALLOWED


@app.command()
def check():
    results = {}

    PROBLEM_ACTIONS = ["view", "edit", "delete", "make_submission"]
    for action in PROBLEM_ACTIONS:
        results[f"{action} problem 1"] = [
            check_permission(PROBLEMS[1], action, user) for user in USERS
        ]
    for action in PROBLEM_ACTIONS:
        results[f"{action} problem 0 [bold red] (restricted)"] = [
            check_permission(PROBLEMS[0], action, user) for user in USERS
        ]

    table = Table(title="Permission check")
    table.add_column("Permission")
    for i in range(1, 7):
        table.add_column(f"User {i}")

    for k, v in results.items():
        table.add_row(k, *["✅" if x else "❌" for x in v])

    console = Console()
    console.print(table)


if __name__ == "__main__":
    app()
