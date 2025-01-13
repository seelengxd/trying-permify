from pydantic import RootModel
import typer
import permify
from permify.api.data_api import DataApi
from permify.models.data_write_body import DataWriteBody
from permify.models.data_delete_body import DataDeleteBody
from permify.models.tuple import Tuple
from permify.models.attribute import Attribute
from permify.models.any import Any
from src.entities import ORGANISATION, PROBLEMS, PROJECT, USERS, ROLES

configuration = permify.Configuration(host="http://localhost:3476")

TENANT_ID = "t1"


def tuples() -> list[Tuple]:
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

    # grant users 4,5,6 admin, ta, student respectively
    role_assign_tuples = [
        {"entity": ROLES["Admin"], "relation": "assignee", "subject": USERS[3]},
        {"entity": ROLES["TA"], "relation": "assignee", "subject": USERS[4]},
        {"entity": ROLES["Student"], "relation": "assignee", "subject": USERS[5]},
    ]

    # create 2 problems
    problem_tuples = [
        {"entity": problem, "relation": "project", "subject": PROJECT}
        for problem in PROBLEMS
    ]

    ret = (
        organisation_tuples
        + project_tuples
        + role_tuples
        + role_assign_tuples
        + problem_tuples
    )
    return RootModel[list[Tuple]].model_validate(ret).root


def get_permify_bool(bool: bool) -> Any:
    value = Any.from_dict(
        {"@type": "type.googleapis.com/base.v1.BooleanValue", "data": bool}
    )
    print(value)
    return value


def attributes() -> list[Attribute]:
    """Add restricted boolean for problems"""
    ret = [
        {
            "entity": problem,
            "attribute": "restricted",
            "value": get_permify_bool(i == 0),
        }
        for i, problem in enumerate(PROBLEMS)
    ]
    return RootModel[list[Attribute]].model_validate(ret).root


def seed():
    """
    Reset data and seed with
    1 organisation
    1 project
    2 problems (1 restricted)
    3 roles (admin/ta/student)
    6 users (org owner, org admin, org observer, project admin, project ta, project student)
    """
    with permify.ApiClient(configuration) as api_client:
        data_api = DataApi(api_client)
        data_api.data_delete_without_preload_content(TENANT_ID, DataDeleteBody())
        data_api.data_write(
            TENANT_ID,
            DataWriteBody(
                metadata={"schema_version": "ctu0e6kb5eec73d9vh10"},
                tuples=tuples(),
                attributes=attributes(),
            ),
        )


if __name__ == "__main__":
    typer.run(seed)
