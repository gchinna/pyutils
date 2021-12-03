#!/usr/bin/env python3
""" Command line interface or module wrapper to difflib.py providing diffs in four formats:

* ndiff:    lists every line and highlights interline changes.
* context:  highlights clusters of changes in a before/after format.
* unified:  highlights clusters of changes in an inline format.
* html:     generates side by side comparison with change highlights.

Adapted from: https://docs.python.org/3/library/difflib.html#a-command-line-interface-to-difflib
"""

import sys, os, difflib, argparse, itertools
from datetime import datetime, timezone

import pyutils

## Defaults
default_lines  = 3
default_maxdiff = 100
default_context = False


def get_parser():
    parser = argparse.ArgumentParser()
    ## optional args
    parser.add_argument('--context', '-c', action='store_true', default=False,
                        help='Produce a context format diff (default)')
    parser.add_argument('--unified', '-u', action='store_true', default=False,
                        help='Produce a unified format diff')
    parser.add_argument('--html', '-m', action='store_true', default=False,
                        help='Produce HTML side by side diff (can use -c and -l in conjunction)')
    parser.add_argument('--ndiff', '-n', action='store_true', default=False,
                        help='Produce a ndiff format diff')
    parser.add_argument('--lines', '-l', type=int, default=default_lines,
                        help=f'Set number of context lines (default: {default_lines})')
    parser.add_argument('--maxdiff', '-md', type=int, default=default_maxdiff,
                        help=f'Set number of context lines (default: {default_maxdiff})')
    ## required args - input files
    parser.add_argument('fromfile')
    parser.add_argument('tofile')
    return parser


def file_mtime(path):
    t = datetime.fromtimestamp(os.stat(path).st_mtime,
                               timezone.utc)
    return t.astimezone().isoformat()


def diff(args, log=None):
    print(f'args: {args}')
    lines = getattr(args, 'lines')
    maxdiff = getattr(args, 'maxdiff')
    context = getattr(args, 'context')
    fromfile = getattr(args, 'fromfile')
    tofile = getattr(args, 'tofile')

    fromdate = file_mtime(fromfile)
    todate = file_mtime(tofile)
    with open(fromfile) as ff:
        fromlines = ff.readlines()
    with open(tofile) as tf:
        tolines = tf.readlines()

    if hasattr(args, 'unified') and args.unified:
        diff_lines = difflib.unified_diff(fromlines, tolines, fromfile, tofile, fromdate, todate, n=lines)
    elif hasattr(args, 'ndiff') and args.ndiff:
        diff_lines = difflib.ndiff(fromlines, tolines)
    elif hasattr(args, 'html') and args.html:
        diff_lines = difflib.HtmlDiff().make_file(fromlines, tolines, fromfile, tofile, context=context, numlines=lines)
    else:
        diff_lines = difflib.context_diff(fromlines, tolines, fromfile, tofile, fromdate, todate, n=lines)

    
    diff_out = None
    if maxdiff:
        # grab the first {maxdiff} elements from generator
        # convert to list so append() can be used.
        diff_out = list(itertools.islice(diff_lines, maxdiff))
        # slicing a generator will exhaust it partially, check if it is fully exhausted or not.
        try:
           next_line = next(diff_lines)
           diff_out.append('++++++++++++++++ AND MORE ++++++++++++++++\n')
        except StopIteration:
           pass
    else:
        diff_out = diff_lines

    if diff_out:
        if log:
           log.info('  >> DIFF:\n{}'.format(pyutils.to_str(seq=diff_out, sep='')))
        else:
            sys.stdout.writelines(diff_out)


if __name__ == '__main__':
    args = get_parser().parse_args()
    diff(args)
