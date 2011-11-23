import re
import csv

def create_csv(fout, coordinators, partners):
    csv_writer = csv.writer(fout, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow([''] + partners)

    for coordinator in coordinators:
        row = [coordinator]
        for partner in partners:
            value = 0
            if partner in coordinators[coordinator]:
                value = coordinators[coordinator][partner]
            row.append(unicode(value))
        csv_writer.writerow(row)


def create_net(fout, coordinators, partners):

    counter = 1
    arcs = ''
    mapping_c = {}
    mapping_p = {}
    fout.write('*vertices\n')
    for coordinator in coordinators:
        if coordinator not in mapping_c:
            mapping_c[coordinator] = counter
            fout.write('\t%d\t"COORDINATOR %s"\n' % (counter, coordinator.replace('"', '\"')))
            counter += 1

        for partner in partners:
            if partner not in mapping_p:
                mapping_p[partner] = counter
                fout.write('\t%d\t"PARTNER %s"\n' % (counter, partner.replace('"', '\"')))
                counter += 1
            arcs += '\t%d %d\n' % (mapping_c[coordinator], mapping_p[partner])
    fout.write('*arcs\n')
    fout.write(arcs)


def create_txt1(fout, coordinators, partners):
    n_tot = 0
    p_mapping = {}
    p_counter = 0
    data = ""
    for c_idx, coordinator in enumerate(coordinators):
        data += "C%d " % c_idx
        n_tot += 1
        for partner in coordinators[coordinator]:
            if partner not in p_mapping:
                p_counter += 1
                n_tot += 1
                p_mapping[partner] = "P%d" % p_counter
            data += "%s " % p_mapping[partner]
        data += "\n"

    fout.write("""dl n=%d
format=nodelist1
labels embedded

data:
%s
""" % (n_tot, data))


def create_txt2(fout, calls):
    n_rows = 0
    n_cols = 0
    c_mapping = {}
    p_mapping = {}
    c_counter = 0
    p_counter = 0
    data = ""
    for activities in calls:
        activities_cleaned = re.sub("[^a-z0-9]+", "_", activities[:activities.find(' ')].lower())
        for call_counter, call in enumerate(calls[activities]):
            coordinator, partners = call

            if coordinator not in c_mapping:
                c_counter += 1
                c_mapping[coordinator] = "C%04d" % c_counter


            cells = [c_mapping[coordinator]]
            for partner in partners:
                if partner not in p_mapping:
                    p_counter += 1
                    p_mapping[partner] = "P%04d" % p_counter
                cells.append(p_mapping[partner])
            data += "%s_%03d\t%s\n" % (activities_cleaned, call_counter, ",\t".join(cells))
            n_rows += 1
            n_cols = max(n_cols, len(cells) + 1)

    fout.write("""dl nr=%d, nc=%d
format = nodelist2
row labels embedded
column labels embedded

data:
%s
""" % (n_rows, n_cols, data))
