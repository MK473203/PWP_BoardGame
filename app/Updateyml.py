import requests
import yaml
import os.path

SERVER_ADDR = "http://localhost:5000/api"
DOC_ROOT = "./doc/"
DOC_TEMPLATE = {
    "description": {},
    "responses": {
        "200":{
            "content":{
                "application/vnd.mason+json":{
                    "example": {}

                }}}}}

resp_json = requests.post(SERVER_ADDR + "/games/15bd5a922e1b48ef9411b0d357660b73/join?username=user1&password=123456789").json()
DOC_TEMPLATE["responses"]["200"]["content"]["application/vnd.mason+json"]["example"] = resp_json
print(yaml.dump(DOC_TEMPLATE, default_flow_style=False))