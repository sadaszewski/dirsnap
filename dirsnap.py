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
    parser.add_argument('--lst', type=str, help='List contents of'
        ' existing snapshot')
    parser.add_argument('--snap', type=str, help='Create snapshot of'
        ' specified directory tree')
    parser.add_argument('--compare', type=str, help='Compare two'
        ' specified snapshots', nargs=2)
    parser.add_argument('--out', type=str, help='Specifies output'
        ' file name, defaults to dirsnap.out.gz', default='dirsnap.out.gz')
    parser.add_argument('--maxdepth', help='Limit output path depth',
        type=int)
    parser.add_argument('--nohidden', help='Skip hidden files and'
        ' directories', action='store_true')
    parser.add_argument('--strip', type=int, default=[0, 0], nargs=2,
        help='Strip prefix containing specified number of slashes'
        ' on respective sides from each file name in comparison mode')
    parser.add_argument('--prefix', type=str, default='',
        help='Use only entries starting with given prefix in'
        ' comparison mode')
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    if not ((args.lst is not None) ^ (args.snap is not None) ^ (args.compare is not None)):
        sys.stderr.write('Either --snap or --compare has to be'
            ' specified\n')
        return

    if args.lst is not None:
        lst(args)
    elif args.snap is not None:
        snap(args)
    else:
        comp(args)


def lst(args):
    reader = SnapReader(args.lst)
    while True:
        e = reader.read()
        if e is None: break
        output_diff(args, e[2], '%s %d' % (e[0], e[1]))


def snap(args):
    fout = gzip.open(args.out, 'wb')
    fout.write('%s\n' % args.snap)
    Q = [args.snap]
    while len(Q) > 0:
        dirname = Q.pop(0)
        st = os.lstat(dirname)
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
            return self.unread_buf.pop()
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
        return [typ, sz, name, n]

    def unread(self, e):
        # self.f.seek(-e[3], 1)
        self.unread_buf.append(e)


def output_diff(args, name, side):
    path = name.split(os.sep)
    if args.maxdepth is not None and len(path) > args.maxdepth + 1:
        return
    if args.nohidden and len(filter(lambda x: x.startswith('.'), path)) > 0:
        return
    print '%s %s' % (side, name)


def path_manip(path, args, side):
    strip = args.strip[0] if side == 'L' else args.strip[1]
    path = os.path.sep.join(path.split(os.path.sep)[strip:])
    if not path.startswith(args.prefix): path = ''
    return path


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
        # if : continue
        e1[2] = path_manip(e1[2], args, 'L')
        if e1[2] == '': continue
        while True:
            e2 = fin2.read()
            if e2 is not None:
                # if : e2[2] = ''
                e2[2] = path_manip(e2[2], args, 'R')
                # os.path.sep.join(e2[2].split(os.path.sep)[args.strip:])
                # if e2[2] == '': continue
            if e2 is None or e2[2] == '':
                output_diff(args, e1[2], 'L')
                # print 'L %s' % e1[2]
                break
            elif e2[2] == e1[2]: # match
                # print e1[2], e2[2]
                break
            elif e2[2] < e1[2]: # only in fin2
                # print 'R %s' % e2[2]
                output_diff(args, e2[2], 'R')
                pass
            else: # only in fin1
                # print 'L %s' % e1[2]
                output_diff(args, e1[2], 'L')
                fin2.unread(e2)
                break
    while True:
        e2 = fin2.read()
        if e2 is None: break
        e2[2] = path_manip(e2[2], args, 'R')
        if e2[2] == '': continue
        # print 'R %s' % e2[2]
        output_diff(args, e2[2], 'R')
    fin1.close()
    fin2.close()


if __name__ == '__main__':
    main()
