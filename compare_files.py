#!/usr/bin/env python3
import argparse, configparser, sys, os, subprocess, filecmp
from pathlib import Path
import pyutils, diff

# arguments parser
parser = argparse.ArgumentParser()
parser.add_argument('--dir1',        '-d1',    help='Source dir #1, default: all files under current dir',  type=str)
parser.add_argument('--dir2',        '-d2',    help='Source dir #2',  type=str)
parser.add_argument('--match_path',  '-mp',    help='Match relative paths to files from dir1 & dir2',  action='store_true')
parser.add_argument('--limit',       '-lim',   help='Limit # files to compare',  type=int, default=0)
parser.add_argument('--diff',        '-di',    help='Select diff format. Default: disabled.',  type=str, choices=['context', 'unified', 'ndiff', 'html'])
parser.add_argument('--debug',       '-dbg',   help='Debug mode',  action='store_true')
args = parser.parse_args()


log = pyutils.init_logger(name=__name__, script=__file__, debug=args.debug)


## config file candidates are read in order with latest file options with highest priority
## base config file from script dir
config_files = [Path(__file__).with_suffix('.ini')]
## next higer priority config file from home directory
homedir = os.getenv('HOME', '')
if homedir:
   config_files.append(Path(homedir) / 'compare_files.ini')
## next higher priority config file from cwd
cwd = Path.cwd()
config_files.append(cwd / 'compare_files.ini')

config_files = [str(x) for x in config_files]  ## convert to strs
log.debug(f'config_files: {config_files}')

config = configparser.ConfigParser()
with open(config_files[0]) as cf:
    config.read_file(cf)
## config.read() automatically ignores the files that do not exist
if len(config_files) > 1:
    config.read(config_files[1:])

## get config from 'default' section and convert items to list
config = dict(config['default'])
for key in config:
    config[key] = config[key].split(',')
log.info(config)


dir1 = Path(args.dir1) if args.dir1 else cwd
rglob_includes = config['rglob_includes']
rglob_excludes = config['rglob_excludes']


src1_paths = list()
src1_list = list()
for pattern in rglob_includes:
    src1_paths.extend(list(dir1.rglob(pattern)))  

## convert src to str so in operator and other string methods can be used
src1_paths = [str(x) for x in src1_paths]
for src in src1_paths:
   exclude = False
   for exl in rglob_excludes:
      if exl in src:
         exclude = True ## skip file when exl pattern is found
   if not exclude:
       src1_list.append(src)
log.info(f'found {len(src1_list)} files to compare ...')

files_equal = list()
files_diff = list()
files_not_found = list()

if args.limit:
   src1_list = src1_list[:args.limit]

#log.debug([x.name for x in src1_list])
for src1 in src1_list:
   src2 = None
   src2_path = None
   dir1_str = str(dir1) + '/'
   if src1.startswith(dir1_str):
       src1 = pyutils.remove_prefix(prefix=dir1_str, text=src1)

   if args.match_path: ## use same relative paths to files
      src2_path = Path(args.dir2, src1)
      if(src2_path.is_file()):
        src2 = str(src2_path)
   else: # use find to locate file in anywhere under dir2
      src2_path = src1 ## default to src1 for "not found" reporting
      sh_cmds = ['find', args.dir2, f'-name "{src1}"']
      sh_cmd_str =' '.join(sh_cmds)
      log.debug('sh_cmd: {}'.format(sh_cmd_str))
      proc = subprocess.Popen(sh_cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      out, err = proc.communicate()
      out_lines = [line.strip() for line in out.decode().split('\n') if line.strip() != '']
      if out_lines:
          log.debug(f'found: {out_lines}')
          if len(out_lines) > 1:
               ## use first match when multiple matches are found
               log.info(f'found multiple matches for: {src1}, found: {out_lines}')
          src2 = out_lines[0]
          src2_path = Path(src2)

   if src2:
      if filecmp.cmp(src1, src2, shallow=False):
         files_equal.append(f'{src2}  {src1}')
         log.info(f'{src1} => files are equal')
      else:
         files_diff.append(f'{src2}  {src1}')
         log.info(f'{src1} => files are different')
         if args.diff:
             diff_args = diff.get_parser().parse_args([f'--{args.diff}', src1, src2])
             diff.diff(args=diff_args, log=log)
   else:
      log.info(f'{str(src2_path)} => file not found in dir2!')
      files_not_found.append( src1)

log.info('files equal: {} {}\n'.format(len(files_equal), pyutils.to_str(files_equal)))
log.info('files different: {} {}\n'.format(len(files_diff), pyutils.to_str(files_diff)))
log.info('files not found: {} {}\n'.format(len(files_not_found), pyutils.to_str(files_not_found)))
