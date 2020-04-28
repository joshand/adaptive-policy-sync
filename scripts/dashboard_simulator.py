from django.views.decorators.csrf import csrf_exempt
import string
import random
import json
import os
import datetime
from random import randint
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from .base_simulator import handle_request


def write_file(out_filename, content):
    with open(os.path.join("scripts", out_filename), 'w') as out_file:
        out_file.write(content)


def read_file(in_filename):
    with open(os.path.join("scripts", in_filename), 'r+') as in_file:
        return in_file.read().splitlines()


def read_file_all(in_filename):
    with open(os.path.join("scripts", in_filename), 'r+') as in_file:
        return in_file.read()


def random_words(size):
    out = []
    lst = read_file("words.txt")
    for s in range(0, size):
        o = random.choice(lst)
        out.append(o)

    return out


def string_num_generator(size):
    chars = string.digits
    return ''.join(random.choice(chars) for _ in range(size))


def string_generator(size):
    chars = string.digits + string.ascii_uppercase + string.ascii_lowercase
    return ''.join(random.choice(chars) for _ in range(size))


def get_rules():
    rules = []
    r_count = randint(2, 6)
    for r in range(0, r_count):
        rule = {}
        s_choice = random.choice([0, 1, 2, 3])
        if s_choice == 1:
            srclist = []
            s_len = randint(2, 10)
            for s in range(0, s_len):
                srclist.append(str(randint(1, 65535)))
            src = ",".join(srclist)
        elif s_choice == 2:
            s_start = randint(1, 65500)
            s_end = randint(s_start, 65535)
            src = str(s_start) + "-" + str(s_end)
        elif s_choice == 3:
            s_port = randint(1, 65500)
            src = str(s_port)
        else:
            src = "any"

        d_choice = random.choice([0, 1, 2, 3])
        if d_choice == 1:
            dstlist = []
            d_len = randint(2, 10)
            for d in range(0, d_len):
                dstlist.append(str(randint(1, 65535)))
            dst = ",".join(dstlist)
        elif d_choice == 2:
            d_start = randint(1, 65500)
            d_end = randint(d_start, 65535)
            dst = str(d_start) + "-" + str(d_end)
        elif d_choice == 3:
            d_port = randint(1, 65500)
            dst = str(d_port)
        else:
            dst = "any"

        rule["policy"] = random.choice(["allow", "deny"])
        rule["protocol"] = random.choice(["any", "tcp", "udp", "icmp"])
        rule["srcPort"] = src
        rule["dstPort"] = dst
        rules.append(rule)

    return rules


def run(orgs, tags, acls, policies):
    neworgs = []
    newtags = {}
    newacls = {}
    newpolicies = {}
    isotime = datetime.datetime.now().isoformat()

    for o in range(0, int(orgs)):
        w = random_words(2)
        org_name = (w[0] + " " + w[1]).title()
        org_id = string_num_generator(18)
        org_code = string_generator(7)
        org_url = "{{url}}/o/" + org_code + "/manage/organization/overview"
        neworgs.append({"id": org_id, "name": org_name, "url": org_url})

        newtags[org_id] = []
        t0_desc = "Unknown group applies when a policy is specified for unsuccessful group classification"
        t2_desc = "MerakiInternal group is used by Meraki devices for internal and dashboard communication"
        newtags[org_id].append({"groupId": 0, "value": 0, "name": "Unknown", "description": t0_desc,
                                "versionNum": 0, "networkObjectId": None, "createdAt": isotime,
                                "updatedAt": isotime})
        newtags[org_id].append({"groupId": 1, "value": 2, "name": "MerakiInternal", "description": t2_desc,
                                "versionNum": 0, "networkObjectId": None, "createdAt": isotime,
                                "updatedAt": isotime})
        for t in range(0, int(tags)):
            tw = random_words(6)
            tag_name = (tw[0] + " " + tw[1]).title()
            tag_desc = (tw[2] + " " + tw[3] + " " + tw[4] + " " + tw[5]).title()
            tag_num = randint(3, 65529)
            newtags[org_id].append({"groupId": t + 2, "value": tag_num, "name": tag_name, "description": tag_desc,
                                    "versionNum": 0, "networkObjectId": None, "createdAt": isotime,
                                    "updatedAt": isotime})

        newacls[org_id] = []
        for a in range(0, int(acls)):
            tw = random_words(6)
            acl_name = (tw[0] + " " + tw[1]).title()
            acl_desc = (tw[2] + " " + tw[3] + " " + tw[4] + " " + tw[5]).title()
            acl_ver = random.choice(["ipv4", "ipv6", "agnostic"])
            acl_rules = get_rules()
            newacls[org_id].append({"aclId": a, "name": acl_name, "description": acl_desc, "ipVersion": acl_ver,
                                    "rules": acl_rules, "versionNum": 0, "createdAt": isotime, "updatedAt": isotime})

        newpolicies[org_id] = []
        for b in range(0, int(policies)):
            tw = random_words(6)
            pol_name = (tw[0] + " " + tw[1]).title()
            pol_desc = (tw[2] + " " + tw[3] + " " + tw[4] + " " + tw[5]).title()
            pol_catch = random.choice(["global", "deny all", "allow all"])
            pol_acls = []
            apply_acl = random.choice([True, False])
            if apply_acl:
                for x in range(0, randint(2, 6)):
                    pol_acls.append(random.choice(newacls[org_id])["aclId"])
            pol_src = random.choice(newtags[org_id])["groupId"]
            pol_dst = random.choice(newtags[org_id])["groupId"]
            newpolicies[org_id].append({"name": pol_name, "description": pol_desc, "monitorModeEnabled": False,
                                        "versionNum": 0, "catchAllRule": pol_catch, "bindingEnabled": True,
                                        "aclIds": pol_acls, "updatedAt": isotime, "srcGroupId": pol_src,
                                        "dstGroupId": pol_dst})

    write_file("orgs.json", json.dumps(neworgs, indent=4))
    write_file("groups.json", json.dumps(newtags, indent=4))
    write_file("acls.json", json.dumps(newacls, indent=4))
    write_file("bindings.json", json.dumps(newpolicies, indent=4))


@csrf_exempt
def parse_url(request):
    baseurl = "/".join(request.build_absolute_uri().split("/")[:3])
    p = request.path.replace("/meraki/api/v1/organizations/", "").replace("/meraki/api/v1/organizations", "")
    arr = p.split("/")

    isotime = datetime.datetime.now().isoformat()
    org_id = arr[0]

    fixedvals = {"organizations": {"id": "{{id-num:18}}", "url": "{{url}}/o/{{id-mix:7}}/manage/organization/overview"},
                 "groups": {"groupId": "{{length}}", "versionNum": 0, "createdAt": isotime, "updatedAt": isotime},
                 "acls": {"aclId": "{{length}}", "versionNum": 0, "createdAt": isotime, "updatedAt": isotime},
                 "bindings": {"versionNum": 0, "updatedAt": isotime}}
    postvals = {"organizations": {"name": None},
                "groups": {"name": None, "description": None, "value": None, "networkObjectId": None},
                "acls": {"name": None, "description": None, "ipVersion": None, "rules": None},
                "bindings": {"srcGroupId": None, "dstGroupId": None, "name": None, "description": None, "aclIds": None,
                             "catchAllRule": None, "bindingEnabled": None, "monitorModeEnabled": None}}
    info = {"organizations": {"id": "id", "unique": [{"id": []}]},
            "groups": {"id": "groupId", "unique": [{"value": [], "groupId": []}]},
            "acls": {"id": "aclId", "unique": [{"name": [], "aclId": []}]},
            "bindings": {"none_as_delete_key": "aclIds", "put_unique": ["srcGroupId", "dstGroupId"],
                         "unique_results": []}}

    if len(arr) == 1:
        file_type = "orgs.json"
        full_dataset = []
        dataset = json.loads(read_file_all(file_type))
        if arr[0] == "":
            elem_id = None
        else:
            elem_id = arr[0]
        endpoint = "organizations"
    else:
        file_type = arr[2] + ".json"
        # dataset = json.loads(read_file_all(file_type).replace("{{url}}", baseurl)).get(org_id, [])
        full_dataset = json.loads(read_file_all(file_type))
        dataset = full_dataset.pop(org_id, [])
        if len(arr) == 3 or request.method == "POST":
            elem_id = None
        else:
            elem_id = arr[3]
        endpoint = arr[2]
        if endpoint == "bindings" and (request.method == "POST" or request.method == "DELETE"):
            return HttpResponseBadRequest("Unsupported Method")

    if request.body:
        jd = json.loads(request.body)
    else:
        jd = None

    updated_data, ret = handle_request(request.method, jd, baseurl, endpoint, elem_id, dataset, fixedvals, postvals,
                                       info)
    if updated_data:
        if isinstance(full_dataset, list):
            write_file(file_type, json.dumps(full_dataset + [updated_data], indent=4))
        else:
            full_dataset[org_id] = updated_data
            write_file(file_type, json.dumps(full_dataset, indent=4))
    return ret
