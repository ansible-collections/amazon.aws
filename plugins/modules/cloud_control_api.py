from ansible.module_utils.basic import AnsibleModule
import boto3
import yaml
import json
import jsonpatch
import sys
import copy


def substract(src, dst):
    deletes = []
    for key, value in dst.items():
        if isinstance(value, dict):
            substract(src[key], dst[key])
        if src[key] == value:
            deletes.append(key)
    for delete in deletes:
        del src[delete]


def update(src, dst):
    deletes = []
    for key, value in dst.items():
        if isinstance(value, dict):
            if not key in src:
                src[key] = {}
            update(src[key], dst[key])
        else:
            src[key] = value


def run_module():
    client = boto3.client("cloudcontrol")
    module_args = dict(
        state=dict(type="str", choices=["absent", "present"]),
        type_name=dict(type="str", required=True),
        identifier=dict(type="str", required=True),
        properties=dict(type="dict", required=False),
    )

    result = dict(changed=False, original_message="", message="")

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        response = client.get_resource(
            TypeName=module.params["type_name"], Identifier=module.params["identifier"]
        )
        src = json.loads(response["ResourceDescription"]["Properties"])
        action = "update"
    except client.exceptions.ResourceNotFoundException:
        src = {}
        action = "create"

    if module.params["state"] == "absent":
        if module.params["properties"]:
            action = "update"
            dst = copy.deepcopy(src)
            substract(dst, module.params["properties"])
        else:
            dst = {}
            action = "delete"
    else:
        dst = copy.deepcopy(src)
        update(dst, module.params["properties"])

    if src == dst:
        module.exit_json(**result)

    result["changed"] = True

    result["diff"] = [
        {
            "before": yaml.dump(src, indent=2),
            "before_header": "Properties",
            "after": yaml.dump(dst, indent=2),
            "after_header": "Properties",
        }
    ]

    if module.check_mode:
        module.exit_json(**result)

    if action == "update":
        response = client.update_resource(
            TypeName=module.params["type_name"],
            Identifier=module.params["identifier"],
            PatchDocument=jsonpatch.make_patch(src, dst).to_string(),
        )
    elif action == "create":
        response = client.create_resource(
            TypeName=module.params["type_name"], DesiredState=json.dumps(dst)
        )
    elif action == "delete":
        response = client.delete_resource(
            TypeName=module.params["type_name"], Identifier=module.params["identifier"]
        )

    if response["ProgressEvent"]["OperationStatus"] in ("PENDING", "IN_PROGRESS"):
        waiter = client.get_waiter("resource_request_success")
        waiter.wait(
            RequestToken=response["ProgressEvent"]["RequestToken"],
            WaiterConfig={"Delay": 10, "MaxAttempts": 6},
        )
    else:
        assert response["ProgressEvent"]["OperationStatus"] == "SUCCESS", response

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
