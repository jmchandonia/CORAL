# CORAL back end
Back end CORAL prototype

## Installation on Debian 10

Each step in the installation is described below.  If you already
have a prerequisite step installed, you can skip it.

### Build environment

_install package managers pip3 and npm, and setuptools:_

```
apt-get install python3-pip npm nodejs python3-setuptools
```

_upgrade pip:_

```
pip3 install --upgrade pip
```

### Other Python prerequisites

```
pip3 install pandas pyArango dumper xarray
```

### Apache installation

```
apt-get install apache2
```

This installation guide assumes you use SSL.  If on a public
server, you can get a SSL certificate from letsencrypt.org.  If on
a private development server, you can generate your own certificate
(in /etc/ssl/certs) using these directions from letsencrypt.org:

```
openssl req -x509 -out localhost.crt -keyout localhost.key \
  -newkey rsa:2048 -nodes -sha256 \
  -subj '/CN=localhost' -extensions EXT -config <( \
   printf "[dn]\nCN=localhost\n[req]\ndistinguished_name = dn\n[EXT]\nsubjectAltName=DNS:localhost\nkeyUsage=digitalSignature\nextendedKeyUsage=serverAuth")

mv localhost.key ../private
```

### Jupyterhub installation

_(based on https://jupyterhub.readthedocs.io/en/stable/quickstart.html)_

_install jupyter:_

```
pip3 install jupyter
````

_install jupyterhub and dependencies:_

```
pip3 install jupyterhub
npm install -g configurable-http-proxy
pip3 install notebook
```

```
useradd jupyterhub
```

_remember to set shell to nologin, add to shadow group_

_set up /etc/jupyterhub and /srv/jupyterhub files as described in docs above, or copy from another installation._

_make these files owned by jupyterhub, delete old sqlite and jupyterhub_cookie_secret_

_ssl certs need to be readable by jupyterhub user_


### Sudo spawner for Jupyterhub

```
pip3 install sudospawner
apt-get install sudo
```

_note: was getting "OSError: [Errno 99] Cannot assign requested address" on spawning jupyterhub_

_this is because ip 127.0.0.1 needs to be explicitly specified_

_had to create file /usr/local/bin/sudospawner-singleuser:_

```
#!/bin/bash -l
exec "/usr/local/bin/jupyterhub-singleuser" --ip 127.0.0.1 $@
```

_In /etc/sudoers:_

```
Cmnd_Alias JUPYTER_CMD = /usr/local/bin/sudospawner

# actually give the Hub user permission to run the above command on behalf 
# of the coral users without prompting for a password:

%jupyterhub ALL=(jupyterhub) /bin/sudo
jupyterhub ALL=(%coral) NOPASSWD:JUPYTER_CMD
```

_add users who use coral, and jupyterhub, to linux group coral_

### Directory setup

_add linux group for coral_

```
groupadd coral
usermod -a -G coral jupyterhub
```

_set up new base directory for coral_

```
mkdir /home/coral/
cd /home/coral
chown jupyterhub .
chgrp coral .
chmod -R g+w .
chmod -R g+s .
setfacl -dm g:coral:rw .
```

### ArangoDB setup

_Follow directions from ArangoDB website; something like this:_

```
cd /tmp
curl -OL https://download.arangodb.com/arangodb37/DEBIAN/Release.key
apt-key add - < Release.key
echo 'deb https://download.arangodb.com/arangodb37/DEBIAN/ /' | tee /etc/apt/sources.list.d/arangodb.list
apt-get install apt-transport-https
apt-get update
apt-get install arangodb3
```

### Make Systemd start up Jupyterhub automatically

_in /etc/systemd/system, make jupyterhub.service:_

```
[Unit]
Description=Jupyterhub
After=network-online.target

[Service]
User=jupyterhub
ExecStart=/usr/local/bin/jupyterhub --JupyterHub.spawner_class=sudospawner.SudoSpawner
WorkingDirectory=/etc/jupyterhub

[Install]
WantedBy=multi-user.target
```

_make it start automatically:_

```
systemctl enable jupyterhub
service jupyterhub start
```

_to view output when testing:_

```
service jupyterhub status
```

### Get Jupyterhub and ArangoDB working behind Apache

_enable all options needed by apache:_

```
a2enmod ssl rewrite proxy proxy_http proxy_wstunnel
```

_in apache conf (/etc/apache2/sites-enabled/000-default.conf):_

```
        SSLProxyEngine on
        SSLProxyVerify none
        SSLProxyCheckPeerCN off
        SSLProxyCheckPeerName off
        SSLProxyCheckPeerExpire off
        ProxyPreserveHost On
        ProxyRequests off

        TraceEnable Off

        <Location /jupyterhub>
            ProxyPass https://localhost:8000/jupyterhub
            ProxyPassReverse https://localhost:8000/jupyterhub
            ProxyPassReverseCookieDomain localhost YOUR_FULL_DOMAIN_NAME_HERE
        </Location>

        <LocationMatch "/jupyterhub/(user/[^/]*)/(api/kernels/[^/]+/channels|terminals/websocket)(.*)">
            ProxyPassMatch wss://localhost:8000/jupyterhub/$1/$2$3
            ProxyPassReverse wss://localhost:8000/jupyterhub/$1/$2$3
        </LocationMatch>

        <Location /arangodb/>
            ProxyPass http://localhost:8529/
            ProxyPassReverse http://localhost:8529/
            ProxyPreserveHost On
            AuthType Basic
            AuthName "Restricted Content"
            AuthUserFile /etc/apache2/htpasswd
            Require valid-user
        </Location>

        <Location /_db/>
            ProxyPass http://localhost:8529/_db/
            ProxyPassReverse http://localhost:8529/_db/
            ProxyPreserveHost On
        </Location>

        <Location /_api/>
            ProxyPass http://localhost:8529/_api/
            ProxyPassReverse http://localhost:8529/_api/
            ProxyPreserveHost On
        </Location>
```

_Set up CORAL front end links_

_e.g., in /var/www/html/coral/index.html:_

```
<html>
<body>
CORAL Resources
  <ul>
    <li><a href="/coral-ui/">CORAL UI</a>
    <li><a href="/jupyterhub/">JupyterHub</a>
    <li><a href="/arangodb/">ArangoDB</a>
  </ul>
</body>
</html>
```

### ArangoDB Config

Now that you can get at ArangoDB through Apache, log in and
create databases.  You need at least a "production" database,
but you could have "test" or other versions for development.
They can be called whatever you want.

### More setup of directory structure

Here I'm going to assume you have only a "prod" environment for
production.  But as mentioned above, you might want more than one,
for testing and development.

```
cd /home/coral
mkdir prod
cd prod
mkdir bin
mkdir data_import
mkdir data_store
mkdir data_store/cache
mkdir data_store/images
mkdir data_store/images/thumbs
mkdir data_store/tmp
mkdir notebooks
mkdir modules
cd modules
```

Copy or move the files under "back_end/python" into the modules subdirectory.

### Initial data, microtypes, and ontologies loading

_load in the data from a jupyter notebook:_

_rsync data_import, notebooks, images from server with data_

_define your process type and all other static types in /home/coral/prod/modules/var/typedef.json_

_set up /home/coral/prod/modules/var/upload_config.json with all the filenames of all ontologies, bricks, entities, and processes that you want to load._

_set up any predefined brick type templates in var/brick_type_templates.json_

_make var/config.json based on the following template:_

```
{
  "Import":{
    "ontology_dir": "/home/coral/prod/data_import/ontologies/",
    "entity_dir": "/home/coral/prod/data_import/data/",
    "process_dir": "/home/coral/prod/data_import/data/",
    "brick_dir": "/home/coral/prod/data_import/data/"
  },
  "Workspace":{
    "data_dir": "/home/coral/prod/data_store/"
  }, 
 "ArangoDB": {
    "url": "http://127.0.0.1:8529",
    "user": "YOUR_USER_NAME",
    "password": "YOUR_PASSWORD",
    "db": "YOUR_PRODUCTION_DATABASE_NAME"
  }, 
  "WebService": {
    "port": 8082,
    "https": true,
    "cert_pem": "PATH_TO_FULLCHAIN.PEM file",
    "key_pem": "PATH_TO_PRIVKEY.PEM file",
    "plot_types_file": "plot_types.json"
  }
}

```

_make a "reload_data" notebook to load and set everything up, then run it._

_sample "reload data" notebook contents (e.g., in /home/coral/prod/notebooks/reload_data.ipynb):_

```
from coral.dataprovider import DataProvider
from coral import toolx
toolx.init_system()
```

_this will set up tables required for web services to start._

### CORAL Web Services

_These run in a virtualenv, so install this first:_

```
pip3 install virtualenv 
python3 -m virtualenv /home/coral/env/
source /home/coral/env/bin/activate
pip3 install flask flask_cors pandas simplepam pyjwt pyArango dumper xarray openpyxl
```

_note:  Be careful to install pyjwt, NOT jwt!  Or login will fail!_

_create /etc/systemd/system/coral-web-services.service:_

```
[Unit]
Description=CORAL Web Services
After=network.target

[Service]
User=root
EnvironmentFile=/etc/sysconfig/coral-web-services
ExecStart=/home/coral/env/bin/python -m coral.web_services
WorkingDirectory=/home/coral/prod/modules/coral
Restart=always
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

_create /etc/sysconfig/coral-web-services:_

```
PATH=/home/coral/env/bin:/usr/local/bin:/usr/bin:/bin
PYTHONIOENCODING=utf-8
PYTHONPATH=/home/coral/env/
VIRTUAL_ENV=/home/coral/env/
```

_to start web services_

```
service coral-web-services start
```

_debug by looking in /var/log/daemon.log_

### Add image thumbnail generation script (if Image is a static type)

Install prerequisite perl library and software:

```
apt-get install libimage-size-perl imagemagick
```

Copy or move the files under "back_end/bin" into the /home/coral/prod/bin subdirectory.

Set up cron job to create thumbnails:

```
cd /etc/cron.hourly
echo "cd /home/coral/prod/data_store/ && /home/coral/prod/bin/thumbnails.pl" > coral-thumbnails.sh
chmod 755 coral-thumbnails.sh
```



### Install UI

See README.md in front\_end direcotry
