from ansible.errors import AnsibleFilterError
import json

try:
    import jq

    HAS_JQ = True
except ImportError:
    HAS_JQ = False


class FilterModule(object):
    def filters(self):
        return {"aws_jq": self.aws_jq}

    def aws_jq(self, data, query):
        """
        Apply a jq query to the provided data.
        """
        if not HAS_JQ:
            raise AnsibleFilterError("The 'jq' python library is required. Please install it using 'pip install jq'.")

        try:
            return jq.compile(query).input(json.loads(data)).all()
        except Exception as e:
            raise AnsibleFilterError(f"jq query failed: {str(e)} - Query: {query}")
