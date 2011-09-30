#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gevent import monkey #the best thing to do is put this import in manage.py
monkey.patch_socket()

import logging
import requests
import tablib
import zlib
#import shelve
import re
from collections import namedtuple
import htmlentitydefs
from BeautifulSoup import BeautifulSoup, NavigableString, Tag
from redis import Redis

import gevent
from gevent.queue import JoinableQueue, Queue

logging.basicConfig(level=logging.DEBUG)

Person = namedtuple('Person', ['name', 'phone', 'fax'])
Project = namedtuple('Project', ['theme', 'activities', 'acronym',
                                 'name', 'start_date', 'end_date',
                                 'duration', 'cost', 'funding',
                                 'status', 'contract_type',
                                 'coordinator', 'partners',
                                 'contact_person', 'reference'])

NUM_THEME_WORKER_THREADS = 6
NUM_PROJECT_WORKER_THREADS = 10

THEME_URL = "http://cordis.europa.eu/fetch?CALLER=FP7_PROJ_EN&QM_EP_PGA_A=%(theme)s"
#project_cache = None

def theme_worker():
    def get_projects(doc):
        for result in doc.findAll(title=u"Project acronym"):
            a = result.a
            link = "http://cordis.europa.eu" + dict(a.attrs)['href'][2:]
            yield link

    logging.info('START THEME WORKER')
    while True:
        count = 0
        theme = q.get()
        logging.info('THEME: %s', repr(theme))

        url = THEME_URL % {'theme': theme}
        try:
            while True:
                r = requests.get(url)
                if not r.ok:
                    logging.error("Request failed for url: %s", url)
                    continue
                doc = BeautifulSoup(r.content)
                for proj in get_projects(doc):
                    project_queue.put((theme, proj))
                    count += 1
                try:
                    next_ = dict(doc.find(
                            text="Next 20 projects &raquo;").parent.attrs
                        )['href'][2:]
                except AttributeError:
                    break
                url = "http://cordis.europa.eu" + next_
        except:
            logging.error("THEME_WORKER: Error for url: %s", url)
        finally:
            logging.info('THEME: %s finished, %d projects', repr(theme), count)
            q.task_done()


def project_worker():
#    global project_cache
    logging.info('START PROJECT WORKER')

    re_query = re.compile("QUERY=[a-zA-Z0-9\:]+")
    max_partners = 0
    red = Redis(db=6)
    while True:
        try:
            theme, url = project_queue.get()
            url = str(url)
            match = re_query.search(url)
            key = url.replace( url[match.start():match.end()+1], "" )
            logging.info('PROJECT: %s: %s' % (theme, url))

            value = red.get(key)
            if value is not None:
                page = zlib.decompress(value)
            else:
                r = requests.get(url)
                if not r.ok:
                   logging.error("Request failed for url: %s", url)
                   continue
                page = r.content
                red.set(key, page)

            doc = BeautifulSoup(page)
            content = doc.find(id="textcontent")
            info = content.find(text="Project details").findParent("table").find(text="Project Acronym:").findParent("td")
            coordinator_table = content.find(text="Coordinator")
            participant_table = content.find(text="Participants")
            offset = 1
            if not participant_table:
                participant_table = content.find(text="Beneficiaries")
                offset = 0
            partners_info = participant_table.findParent("table")
            partners_list = [x.text for x in partners_info.findAll("td")][offset:]

            activities = unescape(content.find(text="Research area:").parent.parent.getText()[len("Research area:"):].strip())
            name = unescape(content.find("h4").getText().strip())
            acronym = unescape(info.find(text="Project Acronym:").parent.nextSibling.strip())

            start_date = unescape(info.find(text="Start Date:").parent.nextSibling.strip())
            end_date = unescape(info.find(text="End Date:").parent.nextSibling.strip())
            duration = unescape(info.find(text="Duration:").parent.nextSibling.strip())
            cost = convert_to_currency(unescape(info.find(text="Project Cost:").parent.nextSibling.strip()))
            funding = convert_to_currency(unescape(info.find(text="Project Funding:").parent.nextSibling.strip()))
            status = unescape(info.find(text="Project Status:").parent.nextSibling.strip())
            contract_type = unescape(info.find(text="Contract Type:").parent.nextSibling.strip())
            partners = [unescape("%s, %s" % (x[0],x[1])) for x in zip(partners_list[0::2], partners_list[1::2])]
            reference = unescape(info.find(text="Project Reference:").parent.nextSibling.strip())

            if coordinator_table:
                contact_info = coordinator_table.findParent("table").find(text="Contact Person:").findParent("td")
                contact_info_tokens = contact_info.text.split("<br />")
                organization_info = coordinator_table.findParent("table").find(text="Organisation:").findParent("td")

                coordinator = unescape(organization_info.text[len("Organisation:"):])
                contact_name = unescape(contact_info_tokens[0][contact_info_tokens[0].find("Name:")+5:].strip()) if len(contact_info_tokens) > 0 else ""
                contact_phone = unescape(contact_info_tokens[1][contact_info_tokens[1].find("Tel:")+4:].strip()) if len(contact_info_tokens) > 1 else ""
                contact_fax = unescape(contact_info_tokens[2][contact_info_tokens[2].find("fax:")+5:].strip()) if len(contact_info_tokens) > 2 else ""
                contact = Person(contact_name, contact_phone, contact_fax)
            else:
                institution = content.find(text="Host Institution").findParent("tr").nextSibling.nextSibling
                node = institution.contents[0].contents[0]

                text = ""
                coordinator = ""
                contact_name = ""
                contact_phone = ""
                contact_fax = ""
                while True:
                    if type(node) == NavigableString:
                        if not coordinator:
                            text += (node + " ").strip()
                        else:
                            tokens = node.split(":")
                            if tokens[0] == "Contact":
                                contact_name = tokens[1].strip()
                            elif tokens[0] == "Tel":
                                contact_phone = tokens[1].strip()
                            elif tokens[0] == "Fax":
                                contact_fax = tokens[1].strip()
                    elif type(node) == Tag and node.name == "hr":
                        coordinator = text.strip()
                        text = ""
                    node = node.nextSibling
                    if not node:
                        break

                contact = Person(contact_name, contact_phone, contact_fax)





            if max_partners < len(partners):
                max_partners = len(partners)
            project = Project(theme, activities, acronym, name, start_date,
                              end_date, duration, cost, funding,
                              status, contract_type, coordinator,
                              partners, contact, reference)

            length_queue.put(len(partners))
            out_queue.put(project)
        except Exception, e:
            logging.exception(e)
        finally:
            project_queue.task_done()


def get_themes():
    # http://cordis.europa.eu/fp7/projects_en.html
    r = requests.get('http://cordis.europa.eu/fp7/projects_en.html')
    assert r.status_code == 200, "Error retrieving themes"
    doc = BeautifulSoup(r.content)
    for option in doc.find(id="themes"):
        try:
            option = option.string.strip()
        except:
            continue
        if not option or option == u"Any":
            continue
        yield option

def convert_to_currency(string):
    toks = string.split()
    result = float(toks[0])
    if "million" in toks:
        result *= 1000000

    # if `string` contains something we don't know, we should probably not convert it,
    # but leave it as it is...
    for tok in toks[1:]:
        if tok not in ["million", "euro"]:
            return string

    return result


def get_timestamp():
    """
    returns a string containg the timestamp (in seconds)
    """
    from datetime import datetime
    from time import mktime

    return str(mktime(datetime.utcnow().timetuple()))[:-2]


# Thanks to Fredrik Lundh, http://effbot.org/zone/re-sub.htm#unescape-html
def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)


if __name__ == "__main__":
#    project_cache = shelve.open("project_cache.shelve")

    q = JoinableQueue()
    project_queue = JoinableQueue()
    out_queue = Queue()
    length_queue = Queue()

    for i in range(NUM_THEME_WORKER_THREADS):
         gevent.spawn(theme_worker)

    for i in range(NUM_PROJECT_WORKER_THREADS):
         gevent.spawn(project_worker)

#    i = 0
    for item in get_themes():
        q.put(item)
#        i += 1
#        if i > 2:
#            break

    try:
        q.join()  # block until all tasks are done
        project_queue.join()
    except KeyboardInterrupt:
        logging.info('CTRL-C: save before exit')
#        project_cache.close()
        raise
#    project_cache.close()

    length_queue.put(StopIteration)
    max_length = 0
    for length in length_queue:
        if max_length < length:
            max_length = length

    out_queue.put(StopIteration)
    data = None

    headers = ["Theme", "Activities (research area)", "Project Acronym", "Start Date", "End Date", "Duration", "Project Cost", "Project Funding", "Project Status", "Contract Type", "Coordinator"]
    for i in range(max_length):
        headers.append("Partner %d" % (i+1))
    headers.extend(["Person Coordinator", "Phone", "Fax", "Project Reference"])
    data = tablib.Dataset(headers=headers)
    for i, out in enumerate(out_queue):
        logging.info('OUT: %d', i)
        row = [out.theme, out.activities, out.acronym, out.start_date, out.end_date, out.duration, out.cost, out.funding, out.status, out.contract_type, out.coordinator]
        for i in out.partners:
            row.append(i)
        for i in range(max_length - len(out.partners)):
            row.append("")
        row.extend([out.contact_person.name, out.contact_person.phone, out.contact_person.fax, out.reference])
        data.append(row)

    with open('projects.%s.csv' % (get_timestamp(),), 'w') as f:
        f.write(data.csv)
