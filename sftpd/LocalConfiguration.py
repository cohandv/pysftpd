import ConfigParser

class User(object):
    def __init__(self):
        self.anonymous = False
        self.password_hash = None
        self.root_path = None
        self.authorized_keys = []
        self.bucket = None
        self.username = None
        self.homeDirectory = 'uploads'


class LocalConfiguration(object):
    def getUsers(self, configFile, bucket):

        # Load the user auth file (authconfig.ini)
        auth_config = ConfigParser.RawConfigParser()
        auth_config.read(configFile)
        users = {}
        for username in auth_config.sections():
            u = User()
            if auth_config.has_option(username, 'anonymous'):
                u.anonymous = auth_config.getboolean(username, 'anonymous')
            if not u.anonymous:
                u.password_hash = auth_config.get(username, 'password')
            u.root_path = auth_config.get(username, 'root_path')
            u.username = username

            # TODO: Move authorized_keys parsing into a separate function
            u.authorized_keys = []
            u.bucket = bucket
            if auth_config.has_option(username, 'authorized_keys_file'):
                filename = auth_config.get(username, 'authorized_keys_file')
                for rawline in open(filename, 'r'):
                    line = rawline.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("ssh-rsa ") or line.startswith("ssh-dss "):
                        # Get the key field
                        try:
                            d = " ".join(line.split(" ")[1:]).lstrip().split(" ")[0]
                        except:
                            # Parse error
                            continue
                        if line.startswith("ssh-rsa"):
                            k = paramiko.RSAKey(data=base64.decodestring(d))
                        else:
                            k = paramiko.DSSKey(data=base64.decodestring(d))
                        del d
                        u.authorized_keys.append(k)
            users[username] = u
        return users
