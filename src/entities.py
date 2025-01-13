ORGANISATION = {"type": "organisation", "id": "1"}
USERS = [{"id": f"{i}", "type": "user"} for i in range(1, 9)]
PROJECT = {"type": "project", "id": "1"}
ROLES = {
    "Admin": {"type": "role", "id": "1"},
    "TA": {"type": "role", "id": "2"},
    "Student": {"type": "role", "id": "3"},
}

PROBLEMS = [{"type": "problem", "id": str(i)} for i in range(1, 3)]
GROUPS = [{"type": "group", "id": "1"}]
SUBMISSIONS = [{"type": "submission", "id": "1"}, {"type": "submission", "id": "2"}]
