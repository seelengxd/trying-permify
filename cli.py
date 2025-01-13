import os
from typing import Annotated
from pydantic import RootModel
import typer
import permify as p
from rich.console import Console
from rich.table import Table
from rich import print
from src.entities import (
    GROUPS,
    ORGANISATION,
    PROBLEMS,
    PROJECT,
    SUBMISSIONS,
    USERS,
    ROLES,
)

configuration = p.Configuration(host="http://localhost:3476")

TENANT_ID = "t1"

app = typer.Typer()

if os.path.exists("schema_version"):
    with open("schema_version") as f:
        METADATA = {"schema_version": f.read()}
else:
    METADATA = {}


@app.command()
def init(schema_text: Annotated[typer.FileText, typer.Option]):
    schema = schema_text.read()
    with p.ApiClient(configuration) as api_client:
        schema_api = p.SchemaApi(api_client)
        response = schema_api.schemas_write(
            "t1", p.SchemaWriteBody.from_dict({"schema": str(schema)})
        )
        with open("schema_version", "w") as f:
            f.write(response.schema_version)


def tuples() -> list[p.Tuple]:
    # organisation: users 1,2,3 as owner, admin and observer respectively
    organisation_tuples = [
        {"entity": ORGANISATION, "relation": "owner", "subject": USERS[0]},
        {"entity": ORGANISATION, "relation": "admin", "subject": USERS[1]},
        {"entity": ORGANISATION, "relation": "observer", "subject": USERS[2]},
    ]

    # the organisation has one project
    project_tuples = [{"entity": PROJECT, "relation": "org", "subject": ORGANISATION}]

    # grant access to the roles
    role_permissions = {}
    role_permissions["Student"] = [
        "view_problems_access",
        "make_submission_access",
        "view_own_submission_access",
    ]
    role_permissions["TA"] = role_permissions["Student"] + [
        "edit_problems_access",
        "delete_problems_access",
        "view_others_submission_access",
    ]
    role_permissions["Admin"] = role_permissions["TA"] + [
        "view_restricted_problems_access",
        "edit_restricted_problems_access",
        "delete_restricted_problems_access",
    ]

    role_tuples = [
        {
            "entity": PROJECT,
            "relation": permission,
            "subject": {**ROLES[role], "relation": "assignee"},
        }
        for role in role_permissions
        for permission in role_permissions[role]
    ]

    # grant users 4,5,6,7 admin, ta, student, student, student respectively
    role_assign_tuples = [
        {"entity": ROLES["Admin"], "relation": "assignee", "subject": USERS[3]},
        {"entity": ROLES["TA"], "relation": "assignee", "subject": USERS[4]},
        {"entity": ROLES["Student"], "relation": "assignee", "subject": USERS[5]},
        {"entity": ROLES["Student"], "relation": "assignee", "subject": USERS[6]},
        {"entity": ROLES["Student"], "relation": "assignee", "subject": USERS[7]},
    ]

    # create 2 problems
    problem_tuples = [
        {"entity": problem, "relation": "project", "subject": PROJECT}
        for problem in PROBLEMS
    ]

    # create 1 group with user 6, 7
    group_tuples = [
        {"entity": GROUPS[0], "relation": "member", "subject": USERS[i]}
        for i in range(5, 7)
    ]

    # create submission 1 (owned by group) and submission 2 (owned by user 8)
    submission_tuples = [
        {"entity": SUBMISSIONS[0], "relation": "problem", "subject": PROBLEMS[0]},
        {"entity": SUBMISSIONS[1], "relation": "problem", "subject": PROBLEMS[0]},
        {"entity": SUBMISSIONS[0], "relation": "group_owner", "subject": GROUPS[0]},
        {"entity": SUBMISSIONS[1], "relation": "owner", "subject": USERS[7]},
    ]

    ret = (
        organisation_tuples
        + project_tuples
        + role_tuples
        + role_assign_tuples
        + problem_tuples
        + group_tuples
        + submission_tuples
    )
    return RootModel[list[p.Tuple]].model_validate(ret).root


def get_permify_bool(bool: bool) -> p.Any:
    value = p.Any.from_dict(
        {"@type": "type.googleapis.com/base.v1.BooleanValue", "data": bool}
    )
    return value


def attributes() -> list[p.Attribute]:
    """Add restricted boolean for problems"""
    ret = [
        {
            "entity": problem,
            "attribute": "restricted",
            "value": get_permify_bool(i == 1),
        }
        for i, problem in enumerate(PROBLEMS)
    ]
    return RootModel[list[p.Attribute]].model_validate(ret).root


@app.command()
def seed():
    """
    Reset data and seed with
    1 organisation
    1 project
    2 problems (1 restricted)
    3 roles (admin/ta/student)
    6 users (org owner, org admin, org observer, project admin, project ta, project student)
    """
    with p.ApiClient(configuration) as api_client:
        data_api = p.DataApi(api_client)
        data_api.data_delete_without_preload_content(TENANT_ID, p.DataDeleteBody())
        data_api.data_write(
            TENANT_ID,
            p.DataWriteBody(
                metadata=METADATA,
                tuples=tuples(),
                attributes=attributes(),
            ),
        )


@app.command()
def read():
    with p.ApiClient(configuration) as api_client:
        data_api = p.DataApi(api_client)
        attributes = data_api.data_attributes_read(
            TENANT_ID,
            p.ReadAttributesBody(metadata=METADATA, filter={}),
        )
        print(attributes)

        relations = data_api.data_relationships_read(
            TENANT_ID,
            p.ReadRelationshipsBody(
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
                metadata={**METADATA, "depth": 200},
                entity=entity,
                permission=permission,
                subject=subject,
            ),
        )
        return result.can == p.CheckResult.CHECK_RESULT_ALLOWED


@app.command()
def check():
    results = {}

    ORGANISATION_ACTIONS = ["view", "edit", "delete"]
    for action in ORGANISATION_ACTIONS:
        results[f"{action} organisation"] = [
            check_permission(ORGANISATION, action, user) for user in USERS
        ]

    PROBLEM_ACTIONS = ["view", "edit", "delete", "make_submission"]
    for action in PROBLEM_ACTIONS:
        results[f"{action} problem 1"] = [
            check_permission(PROBLEMS[0], action, user) for user in USERS
        ]
    for action in PROBLEM_ACTIONS:
        results[f"{action} problem 2 [bold red] (restricted)"] = [
            check_permission(PROBLEMS[1], action, user) for user in USERS
        ]

    for submission in SUBMISSIONS:
        results[f"view submission {submission['id']}"] = [
            check_permission(submission, "view", user) for user in USERS
        ]

    table = Table(title="Permission check")
    table.add_column("Permission")
    labels = [
        "Owner",
        "Admin",
        "Observer",
        "Project Admin",
        "TA",
        "Student [Group]",
        "Student [Group]",
        "Student",
    ]
    for i in range(1, 9):
        table.add_column(f"User {i}\n{labels[i - 1]}")

    for k, v in results.items():
        table.add_row(k, *["✅" if x else "❌" for x in v])

    console = Console()
    console.print(table)


if __name__ == "__main__":
    app()
