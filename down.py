#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import namedtuple
from gevent import monkey #the best thing to do is put this import in manage.py
monkey.patch_socket()

import logging
import requests
import tablib
import shelve
from BeautifulSoup import BeautifulSoup

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
NUM_PROJECT_WORKER_THREADS = 50

THEME_URL = "http://cordis.europa.eu/fetch?CALLER=FP7_PROJ_EN&QM_EP_PGA_A=%(theme)s"
cache = None

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
                if r.status_code != 200:
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
    global cache
    logging.info('START PROJECT WORKER')
    while True:
        try:
            theme, url = project_queue.get()
            logging.info('PROJECT: %s: %s' % (theme, url))

            if url in cache:
                project = cache[url]
            else:
                r = requests.get(url)
                if not r.ok:
                   logging.error("Request failed for url: %s", url)
                   continue

                doc = BeautifulSoup(r.content)
                content = doc.find(id="textcontent")
                info = content.find(text="Project details").findParent("table").find(text="Project Acronym:").findParent("td")
                contact_info = content.find(text="Coordinator").findParent("table").find(text="Contact Person:").findParent("td")
                contact_info_tokens = contact_info.text.split("<br />")
                organization_info = content.find(text="Coordinator").findParent("table").find(text="Organisation:").findParent("td")
                partners_info = content.find(text="Participants").findParent("table")
                partners_list = [x.text for x in partners_info.findAll("td")][1:]

                contact_name = unescape(contact_info_tokens[0][contact_info_tokens[0].find("Name:")+5:].strip())
                contact_phone = unescape(contact_info_tokens[1][contact_info_tokens[1].find("Tel:")+4:].strip())
                contact_fax = unescape(contact_info_tokens[2][contact_info_tokens[2].find("fax:")+4:].strip())
                contact = Person(contact_name, contact_phone, contact_fax)

                activities = unescape(content.find(text="Research area:").parent.parent.getText()[len("Research area:"):].strip())
                name = unescape(content.find("h4").getText().strip())
                acronym = unescape(info.find(text="Project Acronym:").parent.nextSibling.strip())

                start_date = unescape(info.find(text="Start Date:").parent.nextSibling.strip())
                end_date = unescape(info.find(text="End Date:").parent.nextSibling.strip())
                duration = unescape(info.find(text="Duration:").parent.nextSibling.strip())
                cost = unescape(info.find(text="Project Cost:").parent.nextSibling.strip())
                funding = unescape(info.find(text="Project Funding:").parent.nextSibling.strip())
                status = unescape(info.find(text="Project Status:").parent.nextSibling.strip())
                contract_type = unescape(info.find(text="Contract Type:").parent.nextSibling.strip())
                coordinator = unescape(organization_info.text[len("Organisation:"):])
                partners = [unescape("%s, %s" % (x[0],x[1])) for x in zip(partners_list[0::2], partners_list[1::2])]
                reference = unescape(info.find(text="Project Reference:").parent.nextSibling.strip())

                project = Project(theme, activities, acronym, name, start_date,
                                  end_date, duration, cost, funding,
                                  status, contract_type, coordinator,
                                  partners, contact, reference)
                cache[url] = project

            out_queue.put(project)
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
    cache = shelve.open("cache")

    q = JoinableQueue()
    project_queue = JoinableQueue()
    out_queue = Queue()

    for i in range(NUM_THEME_WORKER_THREADS):
         gevent.spawn(theme_worker)

    for i in range(NUM_PROJECT_WORKER_THREADS):
         gevent.spawn(project_worker)

    for item in get_themes():
        q.put(item)

    try:
        q.join()  # block until all tasks are done
        project_queue.join()
    except KeyboardInterrupt:
        # close the shelve
        raise
    # close the shelve
    out_queue.put(StopIteration)

    cache.close()

    data = None
    for i, out in enumerate(out_queue):
        if data is None:
            data = tablib.Dataset(headers=out._fields)
            data.append(out._fields)
        logging.info('OUT: %d, %s', i, repr(out))
        data.append(out)

    with open('projects.%s.ods' % (get_timestamp(),), 'w') as f:
        f.write(data.ods)



