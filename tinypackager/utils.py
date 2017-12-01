import string, os, yaml, re

class YamlException(Exception):
    pass

def read_yaml(filename):
    yaml.Loader.add_constructor(u'tag:yaml.org,2002:float', lambda self, node: self.construct_yaml_str(node))
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return yaml.load(f.read().replace("\t", "    "))
    else:
        raise YamlException('File not found')


def deepmerge(source, destination):
    for key, value in source.items():
        if isinstance(value, dict):
            deepmerge(value, destination.setdefault(key, {}))
        else:
            destination[key] = value
    return destination


def validate_version(version_string):
    r = re.match(r'^(\d+)\.(\d+)$', version_string)
    if not r:
        print "Error: package version must be strictly X.YYY"
        exit(1)
    return [int(r.group(1)), int(r.group(2))]


def prepare_pattern(pattern):
    pattern = pattern.replace('/**/', '(.\1)')
    pattern = pattern.replace('**/', '(.\1)')
    pattern = pattern.replace('/**', '(.\1)')
    pattern = pattern.replace('**', '(.\1)')
    pattern = pattern.replace('*', '([^\/]\1)')
    pattern = pattern.replace('\1', '*')
    pattern = pattern.replace('?', '.')
    pattern = re.sub(r'\[(.*)\]', '[\\1]', pattern)
    pattern = re.sub(r'\{(.*)\}', '(\\1)?', pattern)
    return '^%s$' % pattern


def glob_find(pattern):
    ret = []
    path_pattern, file_pattern = os.path.split(pattern)
    if path_pattern.startswith('.'): path_pattern = path_pattern[1:]
    path_pattern = re.compile(prepare_pattern(path_pattern))
    file_pattern = re.compile(prepare_pattern(file_pattern))
    for folder, _dirs, files in os.walk('.'):
        for filename in files:
            if path_pattern.match(folder[2:]) and file_pattern.match(filename):
                ret.append(os.path.join(folder[2:], filename))

    return ret

def find_root(root_file):
    pwd = os.getcwd()
    while not os.path.exists(root_file):
        _pwd1 = os.getcwd()
        os.chdir('..')
        _pwd2 = os.getcwd()
        if _pwd1 == _pwd2:
            os.chdir(pwd)
            return None
    root = os.getcwd()
    os.chdir(pwd)
    return root


def safe_mkdir(path):
    try:
        os.makedirs(path)
    except OSError:
        pass

def read_yaml_exit(name, message="Error: no message"):
    try:
        return read_yaml(name)
    except YamlException:
        print message
        exit(1)

def chdir_exit(path, message="Error: no message"):
    try:
        os.chdir(path)
    except OSError:
        print message
        exit(1)

