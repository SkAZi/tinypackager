import boto, yaml, tempfile, os, sys, shutil, tarfile
from utils import YamlException, glob_find, validate_version, find_root, \
    read_yaml_exit, chdir_exit, safe_mkdir

class PackageCreate:
    def __init__(self, root, package, bucket=None, access_key=None, secret_key=None, bump_version=False, dest_path="."):
        if self.load(root, package, bump_version):
            if access_key is not None and secret_key is not None:
                conn = boto.connect_s3(
                    aws_access_key_id = access_key,
                    aws_secret_access_key = secret_key,
                    host = 's3-eu-west-1.amazonaws.com'
                )
                self.bucket = conn.get_bucket(bucket)

                if self.check():
                    print "Warning: package %s already exists" % self.name(splitter="/")
                    exit(0)

                else:
                    print "\nUploading enabled, processing..."
                    temp_dir = self.collect(package)
                    result = self.pack(temp_dir)
                    self.upload(result)
                    self.cleanup(temp_dir)

            else:
                print "\nUploading disabled, processing..."
                temp_dir = self.collect(package)
                result = self.pack(temp_dir)
                shutil.copy(result, dest_path)
                self.cleanup(temp_dir)
                print "\nArchive: %s.tbz2" % self.name()


    def load(self, root, package, bump_version):
        self.options = read_yaml_exit(package, "Error: no %s file found!" % package)

        if bump_version:
            majv, minv = validate_version(unicode(self.options.get('version', '0.0')))
            self.options['version'] = "%s.%s" % (majv, minv + 1)
            with open(package, 'w') as f:
                yaml.dump(self.options, f, default_flow_style=False)
        else:
            majv, minv = validate_version(unicode(self.options.get('version', '0.0')))
            self.options['version'] = "%s.%s" % (majv, minv)

        self.root = find_root(root)
        if self.root is not None:
            self.options['rootfile'] = self.root
            root_options = read_yaml_exit(os.path.join(self.root, root))
            root_options.update(self.options)
            self.options = root_options

        print "Building %(project)s-%(name)s version %(version)s" % self.options
        return True


    def name(self, need_version=True, splitter="-"):
        project = self.options.get('project', 'test')
        name = self.options.get('name', 'project')
        version = self.options.get('version', '0.0')

        if need_version:
            return splitter.join((project, name, version))
        else: 
            return splitter.join((project, name))


    def collect(self, package):
        pwd = os.getcwd()
        temp_dir = tempfile.mkdtemp()
        shutil.copy(package, temp_dir)
        log = open(os.path.join(temp_dir, 'files.yml'), 'w')

        print "\nCollecting..."
        roots = self.options.get('root', {})
        for proto_section, data in self.options.get('data', []).iteritems():
            base_section = proto_section.split(" ", 2)[0]

            root_keys = []
            for root_key, root_value in roots.iteritems():
                base_root_key  = root_key.split(' ', 2)
                root_options = base_root_key[1] if len(base_root_key) > 1 else ""
                base_root_key = base_root_key[0]
                if base_root_key == base_section:
                    root_keys.append((root_key, root_options, root_value))

            sections = [(proto_section, './')] if len(root_keys) == 0 else []

            for root_key, root_options, root_value in root_keys:
                sections.append(("%s %s" % (proto_section, root_options), root_value))


            for section, base_path in sections:
                section_dir_name = os.path.join(temp_dir, section)
                print "  section %s" % section
                log.write("%s:\n" % section)

                if isinstance(data, basestring): data = [data]
                for data_item in data:
                    print "    patern %s" % data_item

                    if base_path.startswith('/') and self.root is not None:
                        chdir_exit(os.path.join(self.root, base_path[1:]), 
                            "Error: wrong root for section '%s' %s" % (section, os.path.join(self.root, base_path[1:])))
                        file_list = glob_find(data_item)

                    else:
                        if base_path.startswith('/'):
                            print "    Warning: Root not found, processing relative"

                        chdir_exit(base_path, 
                            "Error: wrong root for section '%s' %s" % (section, base_path))

                        file_list = glob_find(data_item)

                    if len(file_list) == 0:
                        print "    Warning: Nothing found on %s" % data_item

                    for filename in file_list:
                        print "      file %s" % filename

                        src_dir, src_file = os.path.split(filename)
                        dest_path = os.path.join(section_dir_name, src_dir)
                        safe_mkdir(dest_path)

                        log.write("  - '%s'\n" % filename)
                        if os.path.isfile(filename):
                            shutil.copy(filename, dest_path)

                    os.chdir(pwd)

        log.close()
        print "Done."
        return temp_dir


    def pack(self, temp_dir):
        pwd = os.getcwd()
        os.chdir(temp_dir)
        tar_name = '%s.tbz2' % self.name()
        tar = tarfile.open(tar_name, 'w|bz2')

        sys.stdout.write("\nPacking...")
        try:
            for root, dirs, files in os.walk("."):
                for f in files: 
                    if f != tar_name:
                        tar.add(os.path.join(root, f))
        finally:
            tar.close()
            print 'Done.'

        os.chdir(pwd)
        return os.path.join(temp_dir, tar_name)


    def upload(self, archive_name):
        archive_bname = '%s.tbz2' % self.name(splitter="/")
        print "\nUploading archive %s... " % archive_bname,
        key = self.bucket.new_key(archive_bname)
        with open(archive_name, 'r') as f:
            key.set_contents_from_file(f)
        print "Done."


    def check(self):
        archive_bname = '%s.tbz2' % self.name(splitter="/")
        return self.bucket.get_key(archive_bname) is not None


    def cleanup(self, temp_dir):
        shutil.rmtree(temp_dir, True)
