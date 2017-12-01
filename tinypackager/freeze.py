import os, glob
from utils import read_yaml, find_root

class PackageFreeze():
    def __init__(self, root):
        pwd = os.getcwd()
        root_path = find_root(root)
        if root_path:
            os.chdir(root_path)
            for installed in glob.glob('.tinylima/%s/*' % root):
                data = read_yaml(os.path.join(installed, 'package.yml'))
                print "%s-%s: %s" % (data['project'], data['name'], data['version'])
        else:
            print "Error: %s not found" % root
            exit(1)
        os.chdir(pwd)