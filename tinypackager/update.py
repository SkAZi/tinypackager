import boto, yaml, tempfile, os, sys, shutil, tarfile, glob, re
from utils import YamlException, read_yaml, safe_mkdir, glob_find, \
    validate_version, find_root, split_name_flag


class PackageUpdate:
    def __init__(self, root, flags, bucket, access_key, secret_key):
        if access_key is not None and secret_key is not None:
            conn = boto.connect_s3(
                aws_access_key_id = access_key,
                aws_secret_access_key = secret_key,
                host = 's3-eu-west-1.amazonaws.com'
            )
            self.bucket = conn.get_bucket(bucket)

        else:
            print "\nError: No AWS keys found..."
            exit(1)

        pwd = os.getcwd()
        self.root = root
        self.flags = flags
        root_path = find_root(root)
        if root_path is not None:
            os.chdir(root_path)
            self.download_path = tempfile.mkdtemp()
            self.process()
            self.cleanup()
            os.chdir(pwd)
        else:
            print "Error: no %s file found!" % self.root
            exit(1)


    def process(self):
        self.data = read_yaml(self.root)        
        for project, package in self.data.get("packages", {}).iteritems():
            for name, version in (package or {}).iteritems():
                print "Checking: %s-%s %s" % (project, name, version)
                (new_version, old_meta) = self.check_version(project, name, version)
                if new_version is False:
                    print "Info: dependency %s-%s %s is up to date" % (project, name, old_meta["version"])
                else:
                    dld = glob.glob(os.path.join(self.download_path, '%s-%s-*.tbz2' % (project, name)))
                    if len(dld) == 0:
                        unpacked_path = self.download(project, name, new_version)
                        self.install(project, name, unpacked_path)
                    elif os.path.basename(dld[0]) != "%s-%s-%s.tbz2" % (project, name, new_version):
                        print "Error: dependency %s already exists at different version" % name
                        exit(1)

        for installed in glob.glob('.tinylima/%s/*' % self.root):
            _p, project = os.path.split(installed)
            package, name = project.split("-")
            package = self.data.get("packages", {}).get(package, None) or {}
            if not package.get(name, False):
                print "Package %s is not longer needed" % project
                self.remove(project)


    def check_version(self, project, name, version):
        versions = self.list_versions()
        if version is True:
            try:
                version = versions["%s-%s" % (project, name)][-1]
            except KeyError:
                print "Error: no project found for %s-%s" % (project, name)
                exit(1)
            except IndexError:
                print "Error: no versions found for %s-%s" % (project, name)
                exit(1)
        elif version not in versions["%s-%s" % (project, name)]:
            print "Error: version %s not found for %s-%s: %s" % (version, project, name, ", ".join(versions["%s-%s" % (project, name)]))
            exit(1)

        old_meta_path = os.path.join(".tinylima", self.root, "%s-%s" % (project, name), "package.yml")
        if os.path.exists(old_meta_path):
            old_meta = read_yaml(old_meta_path)
        else:
            old_meta = {"version": '0.0'}

        for key, value in self.flags.iteritems():
            if old_meta.get(key) != self.flags[key]:
                return (version, old_meta)    

        if old_meta["version"] == version:
            return (False, old_meta)

        return (version, old_meta)


    def list_versions(self):
        if hasattr(self, "_last_versions"):
            return self._last_versions

        ret = {}
        for full_name in self.bucket.list():
            m = re.match(r"^(.*)/(.*)/(\d+)\.(\d+)\.tbz2$", str(full_name.key))
            if m is not None:
                name = "%s-%s" % (m.group(1), m.group(2))
                version = int(m.group(3)) * 10000 + int(m.group(4))
                if name not in ret:
                    ret[name] = []
                ret[name].append(version)

        for (key, val) in ret.iteritems():
            val.sort()
            ret[key] = map(lambda a: "%s.%s" % (a // 10000, a % 10000), val)

        self._last_versions = ret
        return ret


    def download(self, project, name, version):
        print "Downloading: %s-%s %s" % (project, name, version)

        archive_name = os.path.join(self.download_path, "%s-%s-%s.tbz2" % (project, name, version))

        key = self.bucket.get_key("%s/%s/%s.tbz2" % (project, name, version))
        if key is None:
            print "Error: Package %s-%s-%s not found" % (project, name, version)
            exit(1)

        key.get_contents_to_filename(archive_name)

        unpacked_path = os.path.join(self.download_path, "%s-%s-%s" % (project, name, version))
        os.makedirs(unpacked_path)

        with tarfile.open(archive_name, 'r|bz2') as tar:
            tar.extractall(path=unpacked_path)

        print "Updating package: %s-%s-%s" % (project, name, version)
        return unpacked_path


    def install(self, project, name, unpacked_path):
        pwd = os.getcwd()
        basic_name = '%s-%s' % (project, name)
        self.remove(basic_name)
        safe_mkdir('.tinylima/%s/%s' % (self.root, basic_name))

        install_log = open('.tinylima/%s/%s/installed.yml' % (self.root, basic_name), 'w')

        files_to_install = read_yaml(os.path.join(unpacked_path, 'files.yml'))
        package_yaml = read_yaml(os.path.join(unpacked_path, 'package.yml'))
        package_yaml.update(self.flags)

        destinations = {}
        for key, val in (self.data.get('destination') or {}).iteritems():
            val = val % package_yaml
            destinations[key % package_yaml] = val[1:] if val.startswith('/') else val

        print "Project", destinations

        for section, files in files_to_install.iteritems():
            print "Section", section

            base_section, split_section = split_name_flag(section)
            section_flags = {}
            for flag in split_section:
                key, value = flag.split('=')
                section_flags[str(key)] = str(value)   

            situated = True
            for key in section_flags:
                if self.flags[key] != section_flags[key]:
                    print "  Not situated flags for section %s" % section
                    situated = False
                    break

            if not situated or not destinations.get(base_section):
                break

            path_to_install = os.path.join(pwd, destinations.get(base_section))
            safe_mkdir(path_to_install)
            os.chdir(path_to_install)
            for file in files:
                print '  Copying %s' % os.path.join(path_to_install, file)
                folder, filename = os.path.split(file)
                if folder: safe_mkdir(folder)
                shutil.copyfile(os.path.join(unpacked_path, section, file), file)
                install_log.write("- '%s'\n" % os.path.join(path_to_install, file))
            os.chdir(pwd)

        shutil.copyfile(os.path.join(unpacked_path, 'files.yml'), '.tinylima/%s/%s/files.yml' % (self.root, basic_name))
        with open('.tinylima/%s/%s/package.yml' % (self.root, basic_name), 'w') as f:
            yaml.dump(package_yaml, f, default_flow_style=False)

        install_log.close()   


    def remove(self, package):
        level = os.path.abspath(os.getcwd())
        try:
            for file in read_yaml('.tinylima/%s/%s/installed.yml' % (self.root, package)):
                try:
                    if os.path.abspath(file).startswith(level):
                        print '  Removing %s' % file
                        os.remove(file)
                        #TODO: remove folder if empty
                    else:
                        print '  Can\'t remove %s, it is out of visibility' % file
                except OSError:
                    pass
            shutil.rmtree('.tinylima/%s/%s/' % (self.root, package), True)
        except TypeError:
            pass
        except YamlException:
            pass


    def cleanup(self):
        shutil.rmtree(self.download_path, True)
