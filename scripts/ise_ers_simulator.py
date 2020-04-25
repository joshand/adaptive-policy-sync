import string
import random
import json
import os
from random import randint
from django.http import JsonResponse
import uuid


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
        s_choice = random.choice([0, 1, 2, 3])
        if s_choice == 1:
            srclist = []
            s_len = randint(2, 10)
            for s in range(0, s_len):
                srclist.append(str(randint(1, 65535)))
            src = "eq " + " ".join(srclist)
        elif s_choice == 2:
            s_start = randint(1, 65500)
            s_end = randint(s_start, 65535)
            src = "range " + str(s_start) + " " + str(s_end)
        elif s_choice == 3:
            s_port = randint(1, 65500)
            src = "eq " + str(s_port)
        else:
            src = "any"

        d_choice = random.choice([0, 1, 2, 3])
        if d_choice == 1:
            dstlist = []
            d_len = randint(2, 10)
            for d in range(0, d_len):
                dstlist.append(str(randint(1, 65535)))
            dst = "eq " + " ".join(dstlist)
        elif d_choice == 2:
            d_start = randint(1, 65500)
            d_end = randint(d_start, 65535)
            dst = "range " + str(d_start) + " " + str(d_end)
        elif d_choice == 3:
            d_port = randint(1, 65500)
            dst = "eq " + str(d_port)
        else:
            dst = "any"

        rule_pol = random.choice(["permit", "deny"])
        rule_proto = random.choice(["any", "tcp", "udp", "icmp"])
        rules.append(rule_pol + " " + rule_proto + " " + src + " " + dst)

    return "\n".join(rules)


def run(tags, acls, policies):
    newtags = {"SearchResult": {"total": tags, "resources": []}}
    newacls = {"SearchResult": {"total": tags, "resources": []}}
    newpolicies = {"SearchResult": {"total": tags, "resources": []}}

    tag_id = "947832a0-8c01-11e6-996c-525400b48521"
    tag_name = "TrustSec_Devices"
    tag_desc = "TrustSec Devices Security Group"
    tag_num = 2
    newtags["SearchResult"]["resources"].append({"id": tag_id, "name": tag_name, "description": tag_desc,
                                                 "value": tag_num, "generationId": 0, "propogateToApic": False,
                                                 "link": {"rel": "self", "type": "application/json",
                                                          "href": "{{url}}/ers/config/sgt/" + tag_id}
                                                 })
    tag_id = "92adf9f0-8c01-11e6-996c-525400b48521"
    tag_name = "Unknown"
    tag_desc = "Unknown Security Group"
    tag_num = 0
    newtags["SearchResult"]["resources"].append({"id": tag_id, "name": tag_name, "description": tag_desc,
                                                 "value": tag_num, "generationId": 0, "propogateToApic": False,
                                                 "link": {"rel": "self", "type": "application/json",
                                                          "href": "{{url}}/ers/config/sgt/" + tag_id}
                                                 })

    for t in range(0, int(tags)):
        tw = random_words(6)
        tag_id = str(uuid.uuid4())
        tag_name = (tw[0] + " " + tw[1]).title()
        tag_desc = (tw[2] + " " + tw[3] + " " + tw[4] + " " + tw[5]).title()
        tag_num = randint(3, 65529)
        newtags["SearchResult"]["resources"].append({"id": tag_id, "name": tag_name, "description": tag_desc,
                                                     "value": tag_num, "generationId": 0, "propogateToApic": False,
                                                     "link": {"rel": "self", "type": "application/json",
                                                              "href": "{{url}}/ers/config/sgt/" + tag_id}
                                                     })

    acl_id = "92951ac0-8c01-11e6-996c-525400b48521"
    acl_name = "Permit IP"
    acl_desc = "Permit IP SGACL"
    acl_rules = "permit ip"
    newacls["SearchResult"]["resources"].append({"id": acl_id, "name": acl_name, "description": acl_desc,
                                                 "generationId": 0, "aclcontent": acl_rules,
                                                 "link": {"rel": "self", "type": "application/json",
                                                          "href": "{{url}}/ers/config/sgacl/" + acl_id}
                                                 })
    acl_id = "92919850-8c01-11e6-996c-525400b48521"
    acl_name = "Deny IP"
    acl_desc = "Deny IP SGACL"
    acl_rules = "deny ip"
    newacls["SearchResult"]["resources"].append({"id": acl_id, "name": acl_name, "description": acl_desc,
                                                 "generationId": 0, "aclcontent": acl_rules,
                                                 "link": {"rel": "self", "type": "application/json",
                                                          "href": "{{url}}/ers/config/sgacl/" + acl_id}
                                                 })

    for a in range(0, int(acls)):
        tw = random_words(6)
        acl_id = str(uuid.uuid4())
        acl_name = (tw[0] + " " + tw[1]).title()
        acl_desc = (tw[2] + " " + tw[3] + " " + tw[4] + " " + tw[5]).title()
        acl_v = random.choice(["IPV4", "IPV6", ""])
        acl_rules = get_rules()
        if acl_v == "":
            newacls["SearchResult"]["resources"].append({"id": acl_id, "name": acl_name, "description": acl_desc,
                                                         "generationId": 0, "aclcontent": acl_rules,
                                                         "link": {"rel": "self", "type": "application/json",
                                                                  "href": "{{url}}/ers/config/sgacl/" + acl_id}
                                                         })
        else:
            newacls["SearchResult"]["resources"].append({"id": acl_id, "name": acl_name, "description": acl_desc,
                                                         "generationId": 0, "ipVersion": acl_v, "aclcontent": acl_rules,
                                                         "link": {"rel": "self", "type": "application/json",
                                                                  "href": "{{url}}/ers/config/sgacl/" + acl_id}
                                                         })

    pol_id = "92c1a900-8c01-11e6-996c-525400b48521"
    pol_src = pol_dst = "92bb1950-8c01-11e6-996c-525400b48521"
    pol_name = "ANY-ANY"
    pol_desc = "Default egress rule"
    pol_catch = "PERMIT_IP"
    pol_acls = ["92951ac0-8c01-11e6-996c-525400b48521"]
    newpolicies["SearchResult"]["resources"].append({"id": pol_id, "name": pol_name, "description": pol_desc,
                                                     "sourceSgtId": pol_src, "destinationSgtId": pol_dst,
                                                     "matrixCellStatus": "ENABLED", "defaultRule": pol_catch,
                                                     "sgacls": pol_acls,
                                                     "link": {"rel": "self", "type": "application/json",
                                                              "href": "{{url}}/ers/config/egressmatrixcell/" + pol_id}
                                                     })

    for b in range(0, int(policies)):
        tw = random_words(6)
        pol_id = str(uuid.uuid4())
        pol_name = (tw[0] + " " + tw[1]).title()
        pol_desc = (tw[2] + " " + tw[3] + " " + tw[4] + " " + tw[5]).title()
        pol_catch = random.choice(["NONE", "PERMIT_IP", "DENY_IP"])
        pol_acls = []
        apply_acl = random.choice([True, False])
        if apply_acl:
            for x in range(0, randint(2, 6)):
                pol_acls.append(random.choice(newacls["SearchResult"]["resources"])["id"])
        pol_src = random.choice(newtags["SearchResult"]["resources"])["id"]
        pol_dst = random.choice(newtags["SearchResult"]["resources"])["id"]
        newpolicies["SearchResult"]["resources"].append({"id": pol_id, "name": pol_name, "description": pol_desc,
                                                         "sourceSgtId": pol_src, "destinationSgtId": pol_dst,
                                                         "matrixCellStatus": "ENABLED", "defaultRule": pol_catch,
                                                         "sgacls": pol_acls,
                                                         "link": {"rel": "self", "type": "application/json",
                                                                  "href": "{{url}}/ers/config/egressmatrixcell/" +
                                                                  pol_id}
                                                         })

    write_file("sgt.json", json.dumps(newtags, indent=4))
    write_file("sgacl.json", json.dumps(newacls, indent=4))
    write_file("egressmatrixcell.json", json.dumps(newpolicies, indent=4))


def parse_url(request):
    baseurl = "/".join(request.build_absolute_uri().split("/")[:3])
    p = request.path.replace("/ise/ers/config/", "").replace("/ise/ers/config", "")
    arr = p.split("/")
    if len(arr) > 1:
        file_type = arr[0] + ".json"
        elem_id = arr[1]
        tmp = json.loads(read_file_all(file_type).replace("{{url}}", baseurl))
        ret = {}
        for r in tmp["SearchResult"]["resources"]:
            if r["id"].lower() == elem_id:
                ret = {arr[0].title().replace("Egressmatrixcell", "EgressMatrixCell"): r}
                break
    elif len(arr) == 1:
        file_type = arr[0] + ".json"
        tmp = json.loads(read_file_all(file_type).replace("{{url}}", baseurl))
        ret = {"SearchResult": {"total": len(tmp["SearchResult"]["resources"]), "resources": []}}
        for r in tmp["SearchResult"]["resources"]:
            newr = {}
            for k in r:
                if k in ["id", "name", "description", "link"]:
                    newr[k] = r[k]
            ret["SearchResult"]["resources"].append(newr)
    else:
        ret = {}
    return JsonResponse(ret, safe=False)