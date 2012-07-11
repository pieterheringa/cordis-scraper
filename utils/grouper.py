from utils import project_ordering_key, get_min_max

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


def group_projects(projects, by_programme=False, by_year=False):
    """ group projects by theme.
    """

    min_y = max_y = None
    if by_year:
        min_y, max_y = get_min_max(projects, key=lambda x: x['call year'])

    mapping = {}
    for programme in PROGRAMMES:
        for name in PROGRAMMES[programme]:
            if min_y is None or max_y is None:
                mapping[name] = programme if by_programme else name
            else:
                for year in range(min_y, max_y + 1):
                    mapping['{0}_{1}'.format(year, name)] = '{0}_{1}'.format(
                        year, programme if by_programme else name)

    matrices = {}
    for key in mapping:
        matrices[mapping[key]] = []

    for project in projects:
        name = project['Theme']
        if by_year:
            name = '{0}_{1}'.format(project['call year'], name)

        key = mapping.get(name, None)
        if key is None:
            print "error: unknown theme ``{0}''".format(project['Theme'])
            continue
        matrices[key].append(project)

    matrices = {key: value for key, value in matrices.iteritems() if len(value)}

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
                if node1 == node2:
                    continue
                if node1 not in graph:
                    graph[node1] = {}
                if node2 not in graph[node1]:
                    graph[node1][node2] = 0
                graph[node1][node2] += aggregation_fun(project)

    return graph
