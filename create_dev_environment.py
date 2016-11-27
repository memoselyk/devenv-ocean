import argparse
import os
import requests
from pprint import pprint

TOKEN_FILE = "API_TOKEN.txt"


def load_api_token():
    "Returns the API token from the corresponding file"
    if not os.path.isfile(TOKEN_FILE):
        raise Exception("File {} doesn't exist!".format(TOKEN_FILE))

    with open(TOKEN_FILE) as f:
        return f.read().strip()


def api_call(endpoint, api_token):
    "Calls an API endpoint adding required authentication"
    headers = {"Authorization": "Bearer %s" % api_token}
    response = requests.get("https://api.digitalocean.com/v2/%s" % endpoint,
                            headers=headers)
    return response.json()


def find_ssh_key(key_name, api_token):
    response = api_call('account/keys', api_token)
    return [k for k in response['ssh_keys'] if k['name'] == key_name][0]


def create_dev_droplet(api_token, droplet_name, ssh_keyname):
    # Load cloud-init configuration
    with open('dev_init.yml') as f:
        init_data = f.read()

    # Get SSH key id
    print "Finding SSH key information..."
    ssh_key = find_ssh_key(ssh_keyname, api_token)
    print "SSH key id is %s" % ssh_key["id"]

    # Add users' ssh-keys information
    init_lines = init_data.splitlines()
    keys_sections = [n for n, l in enumerate(init_lines)
                     if l.endswith('ssh-authorized-keys:')]

    for lno in reversed(keys_sections):
        init_lines.insert(lno + 1,
                          init_lines[lno].replace('ssh-authorized-keys:',
                                                  '- ' + ssh_key['public_key']))
    init_data = '\n'.join(init_lines)

    print "=" * 40
    print init_data
    print "=" * 40

    droplet_data = {
        "name": droplet_name,
        "size": "512mb",
        "image": "ubuntu-14-04-x64",
        "region": "nyc3",
        "ssh_keys": [ssh_key["id"]],
        "user_data": init_data
    }

    headers = {"Authorization": "Bearer %s" % api_token,
               "Content-Type": "application/json"}

    print "Creating the droplet..."
    response = requests.post("https://api.digitalocean.com/v2/droplets",
                             headers=headers,
                             json=droplet_data)

    pprint(response)


def parse_args():
    p = argparse.ArgumentParser(description="Create a droplet configured for development")

    p.add_argument("name", help="Name of the new droplet")
    p.add_argument("ssh_key", help="Name of the SSH key to be added to user")

    return p.parse_args()


def main():
    args = parse_args()
    api_token = load_api_token()
    create_dev_droplet(api_token, args.name, args.ssh_key)


if __name__ == "__main__":
    main()
