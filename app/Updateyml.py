if __name__ == "__main__":  # pragma: no cover
    import requests
    import yaml
    import sys
    import os.path

    PATH = "/users/"

    if len(sys.argv) > 1:
        PATH = sys.argv[1]

    SERVER_ADDR = "http://localhost:5000/api"
    DOC_ROOT = "./doc/"
    HEADERS = {"username": "user2",
               "password": "salasana1"}
    BODY = {
        "move": 6,
        "moveTime": 1
    }
    DOC_TEMPLATE = {
        "description": {},
        "responses": {
            "200": {
                "content": {
                    "application/vnd.mason+json": {
                        "example": {}

                    }}}}}

    resp_json = requests.get(
        SERVER_ADDR + PATH, headers=HEADERS).json()
    DOC_TEMPLATE["responses"]["200"]["content"]["application/vnd.mason+json"]["example"] = resp_json
    print(yaml.dump(DOC_TEMPLATE, sort_keys=False))
