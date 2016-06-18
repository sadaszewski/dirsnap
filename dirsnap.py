#
# Author: Stanislaw Adaszewski, 2016
# License: Simplified 2-clause BSD
# Website: http://algoholic.eu
#
# Create and compare directory tree snapshots
#

from argparse import ArgumentParser
import sys
import os
from stat import S_ISDIR
import gzip


def create_parser():
    parser = ArgumentParser()
    parser.add_argument('--snap', type=str, help='Create snapshot of'
        ' specified directory tree')
    parser.add_argument('--compare', type=str, help='Compare two'
        ' specified snapshots', nargs=2)
    parser.add_argument('--out', type=str, help='Specifies output'
        ' file name, defaults to dirsnap.out', default='dirsnap.out.gz')
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    if not ((args.snap is None) ^ (args.compare is None)):
        sys.stderr.write('Either --snap or --compare has to be'
            ' specified\n')
        return

    if args.snap is not None:
        snap(args)
    else:
        comp(args)


def snap(args):
    fout = gzip.open(args.out, 'wb')
    fout.write('%s\n' % args.snap)
    Q = [args.snap]
    while len(Q) > 0:
        dirname = Q.pop(0)
        st = os.stat(dirname)
        if S_ISDIR(st.st_mode):
            L = sorted(os.listdir(dirname))
            L = map(lambda x: os.path.join(dirname, x), L)
            fout.write('D %d %s\n' % (len(L), os.path.split(dirname)[1]))
            Q = L + Q
        else:
            fout.write('F %d %s\n' % (st.st_size, os.path.split(dirname)[1]))
    fout.close()


class SnapReader():
    def __init__(self, fname):
        self.f = gzip.open(fname, 'rb')
        self.basedir = self.f.readline()[:-1]
        self.stack = [[1, self.basedir]]
        self.unread_buf = []

    def close(self):
        self.f.close()

    def read(self):
        if len(self.unread_buf) > 0:
            return self.unread_buf.pop(0)
        line = self.f.readline()
        if line == '':
            return None
        n = len(line)
        line = line[:-1]
        line = line.split(' ')
        typ = line[0]
        sz = int(line[1])
        name = ' '.join(line[2:])
        while len(self.stack) > 0 and self.stack[-1][0] <= 0:
            self.stack.pop()
        self.stack[-1][0] -= 1
        if len(self.stack) > 0:
            name = os.path.join(self.stack[-1][1], name)
        if typ == 'D':
            self.stack.append([sz, name])
        return (typ, sz, name, n)

    def unread(self, e):
        # self.f.seek(-e[3], 1)
        self.unread_buf.append(e)


def comp(args):
    fin1 = SnapReader(args.compare[0])
    fin2 = SnapReader(args.compare[1])
    while True:
        e1 = fin1.read()
        # print e1
        # os.stat(e1[2])
        if e1 is None: break
        # print 'e1:', e1
        # os.stat(e1[2])
        while True:
            e2 = fin2.read()
            if e2 is None:
                print 'L %s' % e1[2]
                break
            elif e2[2] == e1[2]: # match
                # print e1[2], e2[2]
                break
            elif e2[2] < e1[2]: # only in fin2
                print 'R %s' % e2[2]
                pass
            else: # only in fin1
                print 'L %s' % e1[2]
                fin2.unread(e2)
                break
    while True:
        e2 = fin2.read()
        if e2 is None: break
        print 'R %s' % e2[2]
    fin1.close()
    fin2.close()


if __name__ == '__main__':
    main()
