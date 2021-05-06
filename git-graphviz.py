#!/usr/bin/python

import sys
import os
import re
from subprocess import PIPE, Popen, run
import textwrap

FILE_NAME='graphviz.gv'
FILE_NAME_SVG='graphviz.svg'

DIR_ROOT = None
GIT_DIR = None

def git(args):
    p = Popen(['git'] + args, stdout=PIPE, close_fds=True)
    out = p.communicate()[0].decode().strip()
    if p.returncode != 0:
        return None
    return out

def escape_html(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def parse_commit(commit):
    fields = commit.split('\n')
    size = 1
    for l in fields[1:]:
        l.split(':')
        if not l or not l[0] in ('Merge', 'Author', 'Date'):
            break
        size += 1
    header = '<BR/>'.join([escape_html(x) for x in fields[:size]])
    out = f'<<TABLE BORDER="0" WIDTH="12">\n<TR><TD ALIGN="LEFT" BALIGN="LEFT">{header}</TD></TR>\n'
    if len(fields) > size:
        message = []
        for l in fields[size:]:
            wrapped = [escape_html(x) for x in textwrap.wrap(l.strip())]
            message.append('<BR/>'.join(wrapped))
        message = '<BR/>'.join(message)
        out += f'<TR><TD ALIGN="LEFT" BALIGN="LEFT"><FONT POINT-SIZE="12">{message}</FONT></TD></TR>\n'
    out += '</TABLE>>'
    return out

decorate = {}
nodes = []
commits = {}
forks = {}
forks_decorate = {}
log_options=['--branches', '--tags']

if __name__ == '__main__':
    DIR_ROOT = git(['rev-parse', '--show-toplevel'])
    if not DIR_ROOT:
        print('not a git repository')
        exit(1)
    for i in range(len(sys.argv)-1):
        if sys.argv[i] == '--':
            log_options = sys.argv[i+1:]
    repo_name = os.path.basename(DIR_ROOT)
    GIT_DIR = git(['rev-parse', '--git-dir'])
    print('Getting git commit(s) ...')
    out = git(['log', '--reverse', r'--pretty=format:%h|%p|%d'] + log_options)
    for l in out.split('\n'):
        columns = l.split('|')
        out2 = git(['log', '-1', '--no-color', '--date=iso-local', columns[0]])
        commits[columns[0]] = out2
        forks[columns[0]] = []
        for p in columns[1].split(' '):
            if p == '': continue
            forks[p].append(columns[0])
        if columns[2]:
            decorate[columns[0]] = columns[2].strip()
    fork_keys = [x for x in forks if len(forks[x]) > 1]
    forks_decorate = {x: {y: [] for y in forks[x]} for x in fork_keys}
    print(f'Processed {len(decorate)} decorate(s) ...')

    print('Getting git ref branch(es) ...')
    for k in decorate:
        out2 = git(['log', '--reverse', '--first-parent', r'--pretty=format:%h', k])
        log = out2.split('\n')
        nodes.append(log)
        for i in range(len(log) - 1):
            if log[i] in forks_decorate:
                forks_decorate[log[i]][log[i+1]].append(decorate[k])

    print('Getting git merged branch(es) ...')
    out = git(['log', '--merges', r'--pretty=format:%h|%p'] + log_options)
    for l in out.split('\n'):
        columns = l.split('|')
        parents = l.split(' ')
        if len(parents) > 1:
            for i in range(1, len(parents)):
                out2 = git(['log', '--reverse', '--first-parent', r'--pretty=format:%h', parents[i]])
                nodes.append([x for x in out2.split('\n')])
                nodes[-1].append(columns[0])

    print(f'Processed {len(nodes)} branch(es) ...')

    print('Generating do file ...')
    graphviz_file = os.path.join(DIR_ROOT, GIT_DIR, FILE_NAME)
    graphviz_svg = os.path.join(DIR_ROOT, GIT_DIR, FILE_NAME_SVG)
    graphviz = open(graphviz_file, 'w')
    graphviz.write('strict digraph "%s" {\n' % (repo_name,))
    graphviz.write('  node [shape=box];\n')
    graphviz.write('  edge [style="invis"];\n')
    for c in commits:
        label = parse_commit(commits[c])
        graphviz.write(f'  "m_{c}" [label={label}];\n')
    graphviz.write('  "' + '" -> "'.join(['m_' + k for k in commits]) + '";\n')
    graphviz.write('  edge [style=""];\n')
    for i in range(len(nodes)):
        graphviz.write('  node[group="%d", shape=oval, fixedsize=false];\n' % (i + 1,))
        graphviz.write('  "' + '" -> "'.join(nodes[i]) + '";\n')
    for k in forks_decorate:
        for c in forks_decorate[k]:
            if forks_decorate[k][c]:
                decorates = [escape_html(x) for x in forks_decorate[k][c]]
                graphviz.write('  "%s" -> "%s" [label=<%s>];\n' % (k, c, ('<BR/>'.join(decorates))))
    count = 0
    for c in commits:
        graphviz.write('  {rank="same"; "m_%s"; "%s";}\n' % (c,c))
        graphviz.write('  "m_%s" -> "%s" [weight=0, arrowtype="none", dirtype="none", arrowhead="none", style="dotted"];\n' % (c,c))
    for k in decorate:
        v = decorate[k]
        count += 1
        graphviz.write('  subgraph Decorate%d {\n' % (count,))
        graphviz.write('    rank="same";\n')
        if v.strip()[:5] == '(tag:':
            graphviz.write(f'    "{v.strip()}" [shape="box", style="filled", fillcolor="#ffffdd"];\n')
        else:
            graphviz.write(f'    "{v.strip()}" [shape="box", style="filled", fillcolor="#ddddff"];\n')
        graphviz.write(f'    "{v.strip()}" -> "{k}" [weight=0, arrowtype="none", dirtype="none", arrowhead="none", style="dotted"];\n')
        graphviz.write('  }\n')
    graphviz.write('}\n')
    graphviz.close()
    run(['dot', '-Tsvg', graphviz_file, '-o', graphviz_svg])
