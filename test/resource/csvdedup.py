import os
import sys
import argparse
import csv

HASH_WIDTH = 2

def merge_rows(row1, row2):
    assert row1[0] == row2[0]
    assert len(row1) == len(row2)
    merged = [row1[0]]
    for ix in range(1, len(row1)):
        #Use whichever is longer, for now
        if len(row1[ix]) > len(row2[ix]):
            merged.append(row1[ix])
        else:
            merged.append(row2[ix])
    return merged


def run(source, dest):
    header_row = None
    for entry in os.scandir(source):
        print('Processing', entry.path, '...', file=sys.stderr)
        #with gzip.open(resstem_fpath, 'at', newline='') as resstem_fp:
        resource_rows = {}
        with open(entry.path, 'rt', newline='') as infp:
            incsv = csv.reader(infp, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            new_hr = next(incsv)
            if not header_row: header_row = new_hr
            for row in incsv:
                if row[0] in resource_rows:
                    row = merge_rows(resource_rows[row[0]], row)
                resource_rows[row[0]] = row

            for resid, inrow in resource_rows.items():
                resstem = resid[:HASH_WIDTH]
                resstem_fpath = os.path.join(dest, resstem + '.csv')
                resstem_fpath_exists = os.path.exists(resstem_fpath)
                #Read then write back out
                #XXX Maybe later figure how to do it in place
                outrows = []
                if resstem_fpath_exists:
                    with open(resstem_fpath, 'rt', newline='') as resstem_fp:
                        resstem_csv = csv.reader(resstem_fp, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                        hr = next(resstem_csv)
                        for row in resstem_csv:
                            if row[0] == resid:
                                inrow = merge_rows(row, inrow)
                            else:
                                outrows.append(row)
                with open(resstem_fpath, 'wt', newline='') as resstem_fp:
                    resstem_csv = csv.writer(resstem_fp, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    resstem_csv.writerow(header_row)
                    for row in outrows:
                        resstem_csv.writerow(row)
                    resstem_csv.writerow(inrow)


if __name__ == '__main__':
    #python -m bibframe.zextra.reader.ead -v --outliblink /tmp/jmu.json.txt     parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser()
    parser.add_argument('source', metavar='PATH',
                        help='Directory with export from Library.Link in CSV format')
    parser.add_argument('dest', metavar='PATH',
                        help='Deduplicated directory with export from Library.Link in CSV format')
    args = parser.parse_args()

    assert os.path.isdir(args.source)
    assert os.path.isdir(args.dest)
    run(args.source, args.dest)

