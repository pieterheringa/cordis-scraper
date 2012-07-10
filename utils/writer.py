from utils import project_ordering_key


def create_txt1(fout, graph):
    single_nodes = set()
    data = ''
    for node in sorted(graph.keys(), key=project_ordering_key):
        single_nodes.add(node)
        cells = [node]
        for node2 in sorted(graph[node], key=project_ordering_key):
            cells += [node2] * graph[node][node2]

        data += u"{0}\n".format(
            u" \t".join(cells)
        )

    fout.write(u"dl n={0}\r\n" \
               u"format=nodelist1\r\n" \
               u"labels embedded\r\n" \
               u"\r\n" \
               u"data:\r\n" \
               u"{1}".format(len(single_nodes), data))


def create_txt2(fout, projects):
    n_cols = 0
    data = ''
    for project in projects:
        cells = [unicode(project['Project Reference']),
                 project['Coordinator']] + \
                project['partners']
        data += u"{0}\n".format(
            u" \t".join(cells)
        )
        n_cols = max(n_cols, len(cells))

    fout.write(u"dl nr={0}, nc={1}\r\n" \
               u"format = nodelist2\r\n" \
               u"row labels embedded\r\n" \
               u"column labels embedded\r\n" \
               u"\r\n" \
               u"data:\r\n" \
               u"{2}".format(len(projects), n_cols, data))
