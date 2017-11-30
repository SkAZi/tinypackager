import boto, yaml, tempfile, os, sys, shutil, tarfile
from utils import YamlException, read_yaml, mkdirsafe, glob_find, validate_version, find_root

class PackageCreate:
    def __init__(self, root, package, bucket=None, access_key=None, secret_key=None, bump_version=False):
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
                print "\nArchive: %s" % self.pack(temp_dir)


    def load(self, root, package, bump_version):
        try:
            self.options = read_yaml(package)
        except YamlException:
            print "Error: no %s file found!" % package
            exit(1)

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
            root_options = read_yaml(os.path.join(self.root, root))
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
        log = open(os.path.join(temp_dir, 'files.yaml'), 'w')

        print "\nCollecting..."
        for section, data in self.options.get('data', []).iteritems():
            print "  section %s" % section
            log.write("%s:\n" % section)

            section_dir_name = os.path.join(temp_dir, section)
            base_section = section.split(" ", 2)[0]
            base_path = self.options.get('root', {}).get(base_section, './')

            for data_item in data:
                print "    patern %s" % data_item

                if base_path.startswith('/') and self.root is not None:
                    os.chdir(os.path.join(self.root, base_path[1:]))
                    file_list = glob_find(data_item)

                else:
                    if base_path.startswith('/'):
                        print "    Warning: Root not found, processing relative"
                    os.chdir(base_path)
                    file_list = glob_find(data_item)

                if len(file_list) == 0:
                    print "    Warning: Nothing found on %s" % data_item

                for filename in file_list:
                    src_dir, src_file = os.path.split(filename)
                    dest_path = os.path.join(section_dir_name, src_dir)
                    mkdirsafe(dest_path)

                    print "      file %s" % filename
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
