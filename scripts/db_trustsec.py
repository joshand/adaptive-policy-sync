from sync.models import Tag, ACL, Policy
import datetime
from django.utils.timezone import make_aware
from django.db.models import Q
import json
from scripts.dblog import append_log


def clean_sgts(src, sgts, is_base, sync_session, log=None):
    changed_objs = []
    if is_base:
        active_id_list = []
        if src == "ise":
            for s in sgts:
                active_id_list.append(s["id"])
        elif src == "meraki":
            for s in sgts:
                active_id_list.append(s["groupId"])

        tags = Tag.objects.filter(syncsession=sync_session)
        for i in tags:
            if src == "ise" and i.ise_id and i.ise_id not in active_id_list:
                append_log(log, "setting ise", i.ise_id, "for delete")
                i.push_delete = True
                i.last_update = make_aware(datetime.datetime.now())
                i.save()
                changed_objs.append(i)
            if src == "meraki" and i.meraki_id and i.meraki_id not in active_id_list:
                append_log(log, "setting meraki", i.meraki_id, "for delete")
                i.push_delete = True
                i.last_update = make_aware(datetime.datetime.now())
                i.save()
                changed_objs.append(i)
    return changed_objs


def clean_sgacls(src, sgacls, is_base, sync_session, log=None):
    changed_objs = []
    if is_base:
        active_id_list = []
        if src == "ise":
            for s in sgacls:
                active_id_list.append(s["id"])
        elif src == "meraki":
            for s in sgacls:
                active_id_list.append(s["aclId"])

        acls = ACL.objects.filter(syncsession=sync_session)
        for i in acls:
            if src == "ise" and i.ise_id and i.ise_id not in active_id_list:
                i.push_delete = True
                i.last_update = make_aware(datetime.datetime.now())
                i.save()
                changed_objs.append(i)
            if src == "meraki" and i.meraki_id and i.meraki_id not in active_id_list:
                i.push_delete = True
                i.last_update = make_aware(datetime.datetime.now())
                i.save()
                changed_objs.append(i)
    return changed_objs


def clean_sgpolicies(src, sgpolicies, is_base, sync_session, log=None):
    changed_objs = []
    if is_base:
        active_id_list = []
        if src == "ise":
            for s in sgpolicies:
                active_id_list.append(s["id"])
        elif src == "meraki":
            for s in sgpolicies:
                active_id_list.append("s" + str(s["srcGroupId"]) + "-d" + str(s["dstGroupId"]))

        policies = Policy.objects.filter(syncsession=sync_session)
        for i in policies:
            if src == "ise" and i.ise_id and i.ise_id not in active_id_list:
                i.push_delete = True
                i.last_update = make_aware(datetime.datetime.now())
                i.save()
                changed_objs.append(i)
            if src == "meraki" and i.meraki_id and i.meraki_id not in active_id_list:
                i.push_delete = True
                i.last_update = make_aware(datetime.datetime.now())
                i.save()
                changed_objs.append(i)
    return changed_objs


def merge_sgts(src, sgts, is_base, sync_session, log=None):
    changed_objs = []
    for s in sgts:
        tag_num = None
        if "value" in s:
            tag_num = s["value"]
        elif "tag" in s:
            tag_num = s["tag"]

        if tag_num is not None:
            i = Tag.objects.filter(tag_number=tag_num)
            if len(i) > 0:
                if is_base:
                    append_log(log, "db_trustsec::merge_sgts::sgt::" + src + "::", tag_num,
                               "exists in database; updating...")
                    t = i[0]
                    t.tag_number = tag_num
                    if t.name != s["name"] and t.cleaned_name() != s["name"]:
                        t.name = s["name"]
                    t.description = s["description"].replace("'", "").replace('"', "")
                    t.push_delete = False
                else:
                    append_log(log, "db_trustsec::merge_sgts::sgt::" + src + "::", tag_num,
                               "exists in database; not base, only add data...")
                    t = i[0]

                t.syncsession = sync_session
                if src == "meraki":
                    t.meraki_id = s["groupId"]
                    t.meraki_data = json.dumps(s)
                elif src == "ise":
                    t.ise_id = s["id"]
                    t.ise_data = json.dumps(s)
                t.last_update = make_aware(datetime.datetime.now())
                changed_objs.append(t)
                t.save()
            else:
                append_log(log, "db_trustsec::merge_sgts::creating tag", tag_num, "...")
                t = Tag()
                t.tag_number = tag_num
                t.name = s["name"]
                t.description = s["description"].replace("'", "").replace('"', "")
                t.syncsession = sync_session
                t.sourced_from = src
                if src == "meraki":
                    t.meraki_id = s["groupId"]
                    t.meraki_data = json.dumps(s)
                elif src == "ise":
                    t.ise_id = s["id"]
                    t.ise_data = json.dumps(s)
                t.last_update = make_aware(datetime.datetime.now())
                changed_objs.append(t)
                t.save()
            sync_session.dashboard.force_rebuild = True
            sync_session.dashboard.save()
    return changed_objs


def merge_sgacls(src, sgacls, is_base, sync_session, log=None):
    changed_objs = []
    for s in sgacls:
        tag_name = None
        tag_name = s["name"]
        tn_ise = tag_name.replace(" ", "_")
        tn_mer = tag_name.replace("_", " ")

        if tag_name:
            i = ACL.objects.filter(Q(name=tn_ise) | Q(name=tn_mer))
            if len(i) > 0:
                if is_base:
                    append_log(log, "db_trustsec::merge_sgacls::acl::" + src + "::", tag_name,
                               "exists in database; updating...")
                    t = i[0]
                    if t.name != tag_name and t.cleaned_name() != tag_name:
                        t.name = tag_name
                    t.description = s["description"].replace("'", "").replace('"', "")
                    t.push_delete = False
                else:
                    append_log(log, "db_trustsec::merge_sgacls::acl::" + src + "::", tag_name,
                               "exists in database; not base, only add data...")
                    t = i[0]

                t.syncsession = sync_session
                if src == "meraki":
                    t.meraki_id = s["aclId"]
                    t.meraki_data = json.dumps(s)
                elif src == "ise":
                    t.ise_id = s["id"]
                    t.ise_data = json.dumps(s)
                    if s.get("generationId", "") == "0":
                        t.visible = False
                t.last_update = make_aware(datetime.datetime.now())
                changed_objs.append(t)
                t.save()
            else:
                append_log(log, "db_trustsec::merge_sgacls::creating acl", tag_name, "...")
                t = ACL()
                t.name = tag_name
                t.description = s["description"].replace("'", "").replace('"', "")
                t.syncsession = sync_session
                t.sourced_from = src
                if src == "meraki":
                    t.meraki_id = s["aclId"]
                    t.meraki_data = json.dumps(s)
                elif src == "ise":
                    t.ise_id = s["id"]
                    t.ise_data = json.dumps(s)
                    if s.get("generationId", "") == "0":
                        t.visible = False
                t.last_update = make_aware(datetime.datetime.now())
                changed_objs.append(t)
                t.save()
            sync_session.dashboard.force_rebuild = True
            sync_session.dashboard.save()
    return changed_objs


def merge_sgpolicies(src, sgpolicies, is_base, sync_session, log=None):
    changed_objs = []
    for s in sgpolicies:
        binding_name = binding_desc = policy_name = policy_desc = None
        if src == "meraki":
            p_src = Tag.objects.filter(meraki_id=s["srcGroupId"])
            p_dst = Tag.objects.filter(meraki_id=s["dstGroupId"])
            if len(p_src) > 0 and len(p_dst) > 0:
                binding_name = str(p_src[0].tag_number) + "-" + str(p_dst[0].tag_number)
                binding_desc = str(p_src[0].name) + "-" + str(p_dst[0].name)
                policy_name = s.get("name", "")
                policy_desc = s.get("description", "")
        elif src == "ise":
            p_src = Tag.objects.filter(ise_id=s["sourceSgtId"])
            p_dst = Tag.objects.filter(ise_id=s["destinationSgtId"])
            if len(p_src) > 0 and len(p_dst) > 0:
                if p_src[0].tag_number == 65535 and p_dst[0].tag_number == 65535:
                    return None

                binding_name = str(p_src[0].tag_number) + "-" + str(p_dst[0].tag_number)
                binding_desc = str(p_src[0].name) + "-" + str(p_dst[0].name)
                policy_name = s.get("name", "")
                policy_desc = s.get("description", "")

        if binding_name:
            if policy_name is None or policy_name == "":
                policy_name = binding_name
            if policy_desc is None or policy_desc == "":
                policy_desc = binding_desc

            i = Policy.objects.filter(mapping=binding_name)
            if len(i) > 0:
                if is_base:
                    append_log(log, "db_trustsec::merge_sgpolicies::" + src + "::policy", binding_name,
                               "exists in database; updating...")
                    t = i[0]
                    t.mapping = binding_name
                    t.name = policy_name
                    t.description = policy_desc
                    t.push_delete = False
                else:
                    append_log(log, "db_trustsec::merge_sgpolicies::" + src + "::policy", binding_name,
                               "exists in database; not base, only add data...")
                    t = i[0]

                t.syncsession = sync_session
                if src == "meraki":
                    t.meraki_id = s["bindingId"]
                    t.meraki_data = json.dumps(s)
                elif src == "ise":
                    t.ise_id = s["id"]
                    t.ise_data = json.dumps(s)
                t.last_update = make_aware(datetime.datetime.now())
                changed_objs.append(t)
                t.save()
            else:
                append_log(log, "db_trustsec::merge_sgacls::creating policy", binding_name, "...")
                t = Policy()
                t.mapping = binding_name
                t.name = policy_name
                t.description = policy_desc
                t.syncsession = sync_session
                t.sourced_from = src
                if src == "meraki":
                    t.meraki_id = s["bindingId"]
                    t.meraki_data = json.dumps(s)
                elif src == "ise":
                    t.ise_id = s["id"]
                    t.ise_data = json.dumps(s)
                t.last_update = make_aware(datetime.datetime.now())
                changed_objs.append(t)
                t.save()
            sync_session.dashboard.force_rebuild = True
            sync_session.dashboard.save()
    return changed_objs
