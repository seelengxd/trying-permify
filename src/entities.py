def make_entity(type: str, id: str):
    return {"type": type, "id": id}


ORGANISATION = make_entity("organisation", "1")
USERS = [make_entity("user", str(i)) for i in range(1, 9)]
PROJECT = make_entity("project", "1")
ROLES = {
    "Admin": make_entity("role", "1"),
    "TA": make_entity("role", "2"),
    "Student": make_entity("role", "3"),
}

PROBLEMS = [make_entity("problem", str(i)) for i in range(1, 3)]
GROUPS = [make_entity("group", "1")]
SUBMISSIONS = [make_entity("submission", str(i)) for i in range(1, 3)]
