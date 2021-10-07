
def python_info(path=False):
    import sys
    print(f'Python version: {sys.version}')
    print(f'Python exe: {sys.executable}')
    if path: ## do not print path by default due to possibly a long list
        print(f'Python path: {sys.path}')


def contains_any(seq, subseq):
    for c in subseq:
        if c in seq:
            return True
    return False

def contains_all(seq, subseq):
    for c in subseq:
        if c not in seq:
            return False
    return True


def replace_prefix(prefix, to, text):
    import re
    prefix = re.escape(prefix) # escape '.' or any regex special chars
    regex = re.compile('^{}'.format(prefix))
    #print('regex: {}'.format(regex))
    return regex.sub(to, text) 


def replace_suffix(suffix, to, text):
    import re
    suffix = re.escape(suffix) # escape '.' or any regex special chars
    regex = re.compile('{}$'.format(suffix))
    #print('regex: {}'.format(regex))
    return regex.sub(to, text) 


## removeprefix - available in python 3.9+
def remove_prefix(prefix, text, strip=True):
    if strip:
        text = text.strip()
    if text.startswith(prefix):
        return text[len(prefix):]
    return text

def remove_suffix(suffix, text, strip=True):
    if strip:
        text = text.strip()
    if text.endswith(suffix):
        return text[:-len(suffix)]


def get_date_suffix():
    from datetime import datetime
    current_time = datetime.now()
    current_time_str = current_time.strftime('%Y_%b_%d__%H_%M_%S')
    ## extract month and date as date_suffix
    ## 2020_Jul_10__13_00_37
    date_parts = current_time_str.strip().split('_')
    date_suffix = date_parts[1] + date_parts[2]
    return date_suffix



'''
Function to get average of a list: use mean() function from statistics module.
''' 


def init_logger(name, logfile='', logdir='', log_level = None, console=True):
    '''
    Initialize logger and retun log object.
        name: name of the logger, __name__ recommended
        logfile: name of log file. When empty, logfile is not created
        logdir: Optional logfile dir. Default: Current dir
        log_level: Optional log level. Default: INFO
    '''
    import logging
    import os

    if not log_level:
        log_level = logging.INFO   ## default level

    log = logging.getLogger(name)
    log.setLevel(log_level)
    
    if logfile and logdir:
        logfile = os.path.join(logdir, logfile)

    formatter = logging.Formatter('%(asctime)s: %(name)s: %(levelname)s: %(message)s', '%Y/%b/%d-%H:%M:%S')
    if console:  # create console handler for logger
        log_ch = logging.StreamHandler()
        log_ch.setFormatter(formatter)
        log_ch.setLevel(log_level)
        log.addHandler(log_ch)

    if logfile: # create file handler for logger
        log_fh = logging.FileHandler(filename=logfile, mode='w')
        log_fh.setFormatter(formatter)
        log_fh.setLevel(log_level)
        log.addHandler(log_fh)
        log.info('log: {}, level: {}'.format(logfile, logging.getLevelName(log_level)))
    else:
        log.info('log level: {}'.format(logging.getLevelName(log_level)))
    return log


def file_length(filename, max_lines=0):
    line_count = 0
    with open(filename) as fh:
        for i, line in enumerate(fh):
            line_count += 1
            if max_lines and line_count >= max_lines:
                break

    return line_count


## save a df to excel sheet
def save_df2xlsx(df, writer, sheet_name, out_columns=None, wr_index=None):
    import pandas as pd
    ## drop the columns that do not exist in df
    ##df_columns = list(set(out_columns) & set(df.columns))
    ## use for loop to retain the order of columns
    #print('writing df to sheet={}\n'.format(sheet_name), df.head())
    if not df.empty:  ## write only if not empty
        if wr_index == None:
            wr_index = False
            if isinstance(df.index, pd.core.index.MultiIndex):
                wr_index = True
        df_columns = list()
        if out_columns:
            for col in out_columns:
                if col in df.columns:
                    df_columns.append(col)
        else:
            df_columns = df.columns
        df.to_excel(writer, sheet_name=sheet_name, float_format='%.2f', columns=df_columns, index=wr_index)
  

## save a dict of dfs to excel file with each df to a seperate sheet.
def save_dict2xlsx(df_dict, filename, out_columns=None, wr_index=None):
    import pandas as pd
    writer = pd.ExcelWriter(filename)
    for ii, key in enumerate(df_dict.keys()):
        df = df_dict[key]
        sheet_name = key
        ## to workaround Exception: Invalid Excel character '[]:*?/\' in sheetname '{sheet_name}'
        if "::" in sheet_name:
            sheet_name = sheet_name.replace('::', '.')

        ## to workaround Exception: Excel worksheet name '{sheet_name}' must be <= 31 chars.
        ## use first 10 and last 20 chars when the length is longer
        sname_len = len(sheet_name)
        if sname_len > 31:
            sheet_name = '{}-{}'.format(sheet_name[:10], sheet_name[(sname_len -20):])
        ## drop the columns that do not exist in df
        ##df_columns = list(set(out_columns) & set(df.columns))
        ## use for loop to retain the order of columns
        save_df2xlsx(df, writer, sheet_name, out_columns, wr_index)


## save a list of dfs to excel file with each df to a seperate sheet.
def save_list2xlsx(df_list, filename, out_columns=None, wr_index=None):
    import pandas as pd
    writer = pd.ExcelWriter(filename)
    for i, df in enumerate(df_list):
        sheet_name = 'sheet{}'.format(i)
        save_df2xlsx(df, writer, sheet_name, out_columns, wr_index)
  

## load a dict of dfs from excel file with each df from a seperate sheet.
def load_xlsx2dict(filename):
    import pandas as pd
    xl = pd.ExcelFile(filename)
    df_dict = dict()
    for sheet_name in xl.sheet_names:
        df_dict[sheet_name] = xl.parse(sheet_name)

    return df_dict


## load config yaml file and update args
def parse_config(args, config_file = 'config.yaml', config_attr='config_file'):
    import os
    import yaml
    ## adopted from: https://codereview.stackexchange.com/questions/79008/parse-a-config-file-and-add-to-command-line-arguments-using-argparse-in-python
    ## add path when absolute path is not given and given relative path/file does not exist
    if not os.path.isfile(config_file):
        print('ERROR: config_file: {} not found!'.format(config_file))
        sys.exit(1)

    print('Using config_file: ', config_file)
    with open(config_file) as yaml_fh:
        config_dict = yaml.load(yaml_fh)
        delattr(args, config_attr)
        args_dict = args.__dict__
        ##print('config_file args: ', config_dict)
        for key, value in config_dict.items():
            if key not in args_dict.keys():
                print('ERROR: Invalid arg {} found in config_file!'.format(key))
                sys.exit(1)
            elif isinstance(value, list):
                args_dict[key].extend(value)
            elif not args_dict[key]:  ## command-line option NOT set by user, use config_file option.
                args_dict[key] = value
                ##print('config yaml {} arg: {}'.format(key, value))
            else:  ## command-line option set by user, ignore config_file option.
                print('override config yaml {} arg: {} => {}'.format(key, value, args_dict[key]))
    return args


def flatten(seq, uniquify=True):
    """flatten(sequence) -> list

    Returns a single, flat list which contains all elements retrieved
    from the sequence and all recursively contained sub-sequences
    (iterables).

    Examples:
    >>> [1, 2, [3,4], (5,6)]
    [1, 2, [3, 4], (5, 6)]
    >>> flatten([[[1,2,3], (42,None)], [4,5], [6], 7, MyVector(8,9,10)])
    [1, 2, 3, 42, None, 4, 5, 6, 7, 8, 9, 10]"""

    result = []
    for el in seq:
        #if isinstance(el, (list, tuple)):
        if hasattr(el, "__iter__") and not isinstance(el, str):
            result.extend(flatten(el))
        else:
            result.append(el)
    if uniquify:
        result = list(set(result))
    return result
