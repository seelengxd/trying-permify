import permify
from permify.api.schema_api import SchemaApi
from permify.models.schema_write_body import SchemaWriteBody

configuration = permify.Configuration(
    host="http://localhost:3476"
)

with open("unicon.perm") as f:
    schema = f.read()

with permify.ApiClient(configuration) as api_client:
    schema_api = SchemaApi(api_client)
    schema_api.schemas_write("1", SchemaWriteBody.from_dict({"var_schema": schema}))

    # api_client = permify.api.permission_api.PermissionApi(api_client)

# todo:

# create an org
#  user 1: owner
#  user 2: observer
#  user 3: admin

# create a project
# 3 roles
# 1 restricted problem
# 1 unrestricted problem
