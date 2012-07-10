from utils import project_ordering_key

PROGRAMMES = {
    'General': ['FP7',
                ],

    'Cooperation': ['FP7-HEALTH',
                    'FP7-COORDINATION',
                    'FP7-ENERGY',
                    'FP7-ENVIRONMENT',
                    'FP7-ICT',
                    'FP7-KBBE',
                    'FP7-NMP',
                    'FP7-SECURITY',
                    'FP7-SPACE',
                    'FP7-SSH',
                    'FP7-TRANSPORT',
                    'FP7-JTI',
                    ],

    'Euratom': ['FP7-EURATOM-FUSION',
                'FP7-EURATOM-FISSION'
                ],

    'Ideas': ['FP7-IDEAS',
              'FP7-IDEAS-ERC',
              ],

    'Capacities': ['FP7-INCO',
                   'FP7-INFRASTRUCTURES',
                   'FP7-POTENTIAL',
                   'FP7-REGIONAL',
                   'FP7-SIS',
                   'FP7-SME',
                   ],

    'People': ['FP7-PEOPLE',
               ],

    'JRC': []
}


def group_projects(projects, by_programme=False):
    """ group projects by theme.
    """
    mapping = {}
    for programme in PROGRAMMES:
        for name in PROGRAMMES[programme]:
            mapping[name] = programme if by_programme else name

    matrices = {}
    for key in mapping:
        matrices[mapping[key]] = []

    for project in projects:
        key = mapping.get(project['Theme'], None)
        if key is None:
            print "error: unknown theme ``{0}''".format(project['Theme'])
            continue
        matrices[key].append(project)

    for key in matrices:
        print "Grouped {0} projects under ``{1}''".format(
            len(matrices[key]), key)

    return matrices


def aggregate(projects, aggregation_fun=lambda _: 1):
    graph = {}
    for project in projects:
        nodes = [project['Coordinator']] + project['partners']
        for node1 in nodes:
            for node2 in nodes:
                if project_ordering_key(node1) <= project_ordering_key(node2):
                    if node1 not in graph:
                        graph[node1] = {}
                    if node2 not in graph[node1]:
                        graph[node1][node2] = 0
                    graph[node1][node2] += aggregation_fun(project)

    return graph
