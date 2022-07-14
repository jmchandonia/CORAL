# CORAL back end prototype

## Installation on Linux (Debian 10)

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
pip3 install pandas pyArango dumper xarray diskcache oauthenticator
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
```

_install jupyterhub and dependencies:_

```
pip3 install jupyterhub
npm install -g configurable-http-proxy
pip3 install notebook
```

_add jupyterhub as user on Linux:_
```
useradd jupyterhub
```
_remember to set shell to nologin, add to shadow group_

_set up /etc/jupyterhub and /srv/jupyterhub files as described in docs above, or copy from another installation._

Be sure the following paths are set to point to the right directory:

```
in jupyterhub_config.py:
c.Spawner.notebook_dir = '/home/coral/prod/notebooks'

in jupyter_notebook_config.py:
c.NotebookApp.notebook_dir = '/home/coral/prod/notebooks'
```

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

### Directory setup

_add linux group for coral_

```
groupadd coral
usermod -a -G coral jupyterhub
```

_also, add all linux users who use coral to linux group coral, as above_

_set up new base directory for coral_

```
mkdir /home/coral/
cd /home/coral
chown -R jupyterhub .
chgrp -R coral .
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
mkdir java
mkdir notebooks
mkdir modules
cd modules
```

_Copy or move the files under "back_end/python" into the modules subdirectory._

_symlink 'coral' and 'var' directories from modules into the 'notebooks' directory_


### Authorized data access API

CORAL allows access to some of the APIs (all methods in web_services.py
with "@auth_ro_required" before the method definition) by clients with
an authorized RSA public key.  A public/private RSA key pair must
be generated, and the public key may be given out to developers who
want to access CORAL data through the API.

Sample code is in back_end/python/test/data_retrieval_test.py

To generate a pair of keys, do:

```
ssh-keygen -t rsa -b 4096 -P "" -f coral.key
```

This will create a public key called "coral.key.pub" to give to
application developers you want to have access to the CORAL API.
We call this the "data access API public key."

Keep the private key "coral.key" on the server, and install it
using the config.json file below.  We call this the "data access
API private key."


### Initial data, microtypes, and ontologies loading

_load in the data from a jupyter notebook:_

_copy example data and ontologies into data import directory, or convert some real data into the same json format ast the examples__

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
    "plot_types_file": "plot_types.json",
    "auth_private": "PATH_TO_DATA_ACCESS_API_PRIVATE_KEY",
    "auth_public": "PATH_TO_DATA_ACCESS_API_PUBLIC_KEY",
    "project_root": "/home/coral/prod",
    "users": "/path/to/users.json",
    "google_auth_file": "/path/to/google_auth_file"
    "captcha_secret_key": "YOUR_GOOGLE_RECAPTCHA_SECRET_KEY",
    "project_email": "YOUR_PROJECT_EMAIL",
    "project_email_password": "YOUR_PROJECT_EMAIL_PASSWORD",
    "admin_email": YOUR_ADMINS_EMAIL"
    "upstream_connection_criteria": {
        "coords": ["latitude", "longitude"]
    }
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


### Set up Users and Auth

In your `coral/back_end/python/var/` directory, create a file called `users.json`. This file will contain basic information about the user's permission levels and personal info. The structure of a user looks like the following:

```json
[
  {
    "username": "jsmith",
    "email": "jsmith@example.com",
    "user_level": 1,
    "allowed_upload_types": [
      "Well",
      "Sample",
      "OTU"
    ]
  }
]
```
When `users.json` is created, you must specify the filepath location in the `WebService.users` field of your `config.json`.

There can be any number of users added to the users.json array. `username`, `email` and `user_level` are all required. `user_level` indicates the amount of permissions a user has. A user with level 0 does not have access to Jupyter notebooks and certain more advanced features on the CORAL UI such as uploading of core types. User level 1 has all capabilities enabled.

`allowed_upload_types` is only necessary if the user is set to user_level 1 and needs to upload specific core types to the system according to their expertise. It is an array of core types stored in the system by their term name. A user will have power to upload any types that are saved in their `allowed_upload_types`.

If you want to give upload privileges for all types in your system to a user, you can set the `allowed_upload_types` field to '*' rather than listing out all the types.

#### Setting up Auth

Once you have configured your users.json file, you will need to generate Google OAuth2 credentials for login. Read the section below for information on how to obtain and configure your google OAuth credentials.

When you have your credentials, download them as a json file and store them in a secure place on your computer or linux machine and add the location of the credentials to the "WebService.google_auth_file" of your `config.json`:

```
  "WebService": {
    ...
    "google_auth_file": "path/to/your/google_auth.json"
  }
```

You will also need to store the public key value on the client facing environment, under `front_end/src/app/environments/YOUR_ENVIRONMENT.ts`. the field must be stored with the key name "GOOGLE_OAUTH2_CLIENT_KEY".

Once you have congigured this information properly, allowed users should be able to sign in to your CORAL app using gmail.

#### Setting up Authentication with Google

CORAL supports authentication both with OAuth2 and with SimplePam. The default and recommended behavior is to set up OAuth2 using Google's OAuth2 services. You can find more information about how Google's OAuth2 flow works [here](https://developers.google.com/workspace/guides/auth-overview). Visit [here](https://developers.google.com/adwords/api/docs/guides/authentication) for Google's more detailed instructions for getting started.

Once you have created a Google Developer account and have set up a profile, begin by going to the [Google Cloud Console](https://console.cloud.google.com) to get started with creating authentication. In the top left corner next to "Google Cloud Platform", click select a project. A modal window will pop up and you can click "NEW PROJECT" in the top right. After naming you project, you will be redirected to the dashboard where you can manage many google tools including authentication.

Next, click "APIs & Services" on the side panel - once that has loaded, you should see a new side panel that has "Credentials" within it. Click on "Credentials". You will need to first configure the Consent screen before creating the credentials. The "Configure Consent Screen" button will ask for consent, then take you to where you go to set up your credentials. You need to have a google workspace account if you want to set up internal only credentials.

_Note: As google changes their documentation frequently, these instructions are prone to change. It is important to have bookmarked the right information needed and make note of things as they change. It is recommended that you check up on your google developer console frequently to make sure that there are no issues and that things are still located where they are expected to be._
#### Setting up The credentials

Once you have granted consent, you will automatically be redirected to the page where you set up important information about which domains are allowed to access you developer token. You will need to provide the domain that the site will be hosted at (you can also use `localhost` with no port numbers for development), as well as the user support email and contact information.

When you have moved on, It will ask you for Authorized JavaScript origins as well as Authorized redirect URIs. You can add as many or as few as you like. JavaScript Origins will be the domains that your client will visit, and Authorized Redirect URIs are the callback that Google will use when they have finished authenticating. Note that for development you can add `localhost` (with or without port numbers) to either category, but they must be prefixed in this case with `http://` or `https://`.

For Authorized Redirect URIs, for each domain that you want to host CORAL on, you will need 2 URLs: 1 for the web service and one for the jupyterhub. the web service url is `https://<YOUR_DOMAIN>/coral/google_auth_code_store` and the jupyterhub endpoint is `https://<YOUR_DOMAIN>/jupyterhub/hub/oauth_callback`. Make sure that you do not end either endpoint with a trailing slash.

_Tip: If you ever find yourself in a part of the developer portal where you can't find the Credentials page, Click the hamburger menu on the top left and make sure the selected option is "APIs & Services"._
#### Adding Auth to web services

Once you have configured your settings correctly, you can download a json file containing all the important information needed for google to authenticate. The 2 most important fields are the Client ID and the Client secret. It should go without saying that you should never share these insecurely or incorporate them into the codebase directly.

Add this file to any directory you like where your web services are hosted, and edit your config.json's `WebService.google_auth_file` to the full path to the oauth json file. You will need to restart the server once you have added the file and edited the config to pick up the new auth info.

When you have finished editing the server portion, you will need to provide the client side with the Client ID as well. Inside of the front end's `src/environments` file, edit the relevant `environment.*.ts` files with the provided client id under the field called `GOOGLE_OAUTH2_CLIENT_KEY`. Remember that you want to provide the Client ID, NOT the client secret! The client ID always ends with `.apps.googleusercontent.com`.

#### Troubleshooting Google Auth issues

There are 2 main kinds of failures that can happen with Google auth. The first type is when google sends back a response (which will be forwarded to the client) that says "unauthorized_user". This message typically means that the redirect URI you have sent Google is not whitelisted or that you are using stale credentials. Double check your list of approved redirect URIs in the developer console and make sure that your client credentials file stored on the server is up to date with what you see in the developer console.

The other main issue that can happen is that the front end will receive an error message saying "Client at <<domain>> is not authorized to access Client ID <<client_id>>". This typically happens when the domain you are logging in from is not on the list of Authorized JavaScript origins. Add the domain you are using to the origin list. Note that this operation usually takes up to a day to carry out.

#### Setting up User Registration

Setting up User registration requires google reCaptcha V2 credentials, which can be obtained [here](https://www.google.com/recaptcha/about/). When you have received your google credentials, you will want to store your secret key in the `WebService.captcha_secret_key` field of your `config.json`. Since the public sitekey will be sent to the client side, you must add it as a string value to the "GOOGLE_CAPTCHA_SITE_KEY" field of your environment.ts.

For sending automated emails when a user requests registration, it is recommended to set up a new gmail account with the "allow less secure apps to access this email" setting turned on ([More Info Here](https://support.google.com/accounts/answer/6010255?hl=en)). This will allow web_services.py to send an email to your admin's account when a user has successfully registered after validating that they're not a robot.

Make sure to add your newly created email account to the `WebService.project_email` and the admin's email to the `WebService.admin_email` of your `config.json`.

### Setting up Authentication in JupyterHub

To use the same Google Authentication system with jupyterhub, make sure you have the `oauthenticator` module installed. It has extensions of the jupyterhub authenticator base class that will allow you to log in with Google Oauth2 credentials.

Once you have confirmed that it is installed, add the following code to your `/etc/jupyterhub/jupyterhub_config.py`:
```python
import json
import re
from oauthenticator.google import LocalGoogleOAuthenticator

class UsernameAuthenticator(LocalGoogleAuthenticator):
  def normalize_username(self, username):
    with open('/path/to/your/users.json') as f:
      registered_users = json.load(f)

    email_regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if re.search(email_regex, username):
      for user in registered_users:
        if username == user['email']:
          return username.lower().split('@')[0]
    else:
      for user in registered_users:
        if username == user['username']:
          return username
    
    raise ValueError('Username %s not allowed: please contact site administrator for approval' % username)
```
This will ensure that the user logging in with Google Oauth2 will validate using their unique email. It is important to check whether or not the username in `normalize_username` is an email, because upon restarting `jupyterhub.service`, the system will automatically validate all currently existing Unix users using this method. This ensures that restarting wont fail after validating the currently existing users.

Once you have implemented this method, you need to set up the user authenticator configuration. Add the following code below, outside of the `UsernameAuthenticator` class:

```python
c.JupyterHub.authenticator_class = UsernameAuthenticator
with open ('/path/to/your/google_auth.json') as authfile:
  google_oauth = json.load(authfile)

c.UsernameAuthenticator.client_id = google_oauth['web']['client_id']
c.UsernameAuthenticator.client_secret = google_oauth['web']['client_secret']
# Important: your Oauth2 callback url MUST match this pattern or else jupyterhub wont know how to validate the Oauth2 token
c.UsernameAuthenticator.oauth_callback_url = 'https://<YOUR_DOMAIN>/jupyterhub/hub/oauth_callback'
```

Finally, if you would like to the system to automatically create a system user account without having to manually add one, you can configure the system so that when a new user is authenticated and validated through OAuth2 and `users.json`, it will automatically create a user in your system. To set this up, add the following commands:

```python
c.UsernameAuthenticator.create_system_users = True
c.UsernameAuthenticator.add_user_cmd = ['useradd', '-m', '--home-dir', '/home/USERNAME', '-r', '-g', 'coral', '-s', '/sbin/nologin']
```
This enables system users that don't currently exist to be added via shell using the command provided in `c.UsernameAuthenticator.add_user_cmd`. Note that depending on your Unix/Linux distribution, this command may vary. Make sure you know the format of your system's add user command before adding it to the config. Make sure that the command adds the user to the `coral` group and sets their shell to `nologin`.

This process may take some trial and error, and depending on your system it might be necessary to allow the `jupyterhub` user to run your useradd command in `etc/sudoers`.

when adding the user with their username, jupyterhub_config automatically replaces any instance of 'USERNAME' in the add_user_cmd array with the username defined in `users.json`. 

More information of the jupyterhub add_user_cmd can be found [here](https://jupyterhub.readthedocs.io/en/stable/api/auth.html)

**Important:** Make sure that when adding users to `users.json`, every user has a unique username. Jupyterhub depends on the usernames defined in the file, and if there are 2 duplicate usernames then those users will share an account on the system.
### CORAL Web Services

The back end relies on graphviz to draw graphs.  Version 2.42 or
higher is recommended.  The "dev" or "devel" package is also needed,
so that the python library pygraphviz will install:

```
apt-get install graphviz graphviz-dev
```

_These run in a virtualenv, so install this first:_

```
pip3 install virtualenv 
python3 -m virtualenv /home/coral/env/
source /home/coral/env/bin/activate
pip3 install flask flask_cors pandas simplepam pyjwt pyArango dumper xarray openpyxl diskcache pycryptodome networkx pygraphviz
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
WorkingDirectory=/home/coral/prod/modules
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

_Start web services automatically on boot_

```
systemctl enable coral-web-services
service coral-web-services start
```

_debug by looking in /var/log/daemon.log_

### Add image thumbnail generation script (if Image is a static type in your instance)

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


### Install java code needed for format conversion

Copy or move the files under "back_end/java" into the /home/coral/prod/java subdirectory.

Install dependencies:

```
cd /home/coral/prod/java/
git clone https://github.com/kbase/jars.git
git clone https://github.com/kbaseapps/GenericsUtil.git
../bin/compile_java.sh

```

### Install on MacOS for Development

Please note that it is not recommended to try to set up the CORAL back end in a production capacity. These instructions are for local development only. These instructions are to install CORAL at a user profile level for personal development.

_Begin with installing environment dependencies:_

```
brew install python3-pip node python3-setuptools
```
_Note: if running on MacOS and brew is not installed, you can install with this command, as described by [the docs](https://brew.sh/)
```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
- Create a new directory anywhere in your User directory and clone the repository.
- Create a new python environment and activate:
```
pip3 install virtualenv 
python3 -m virtualenv /home/coral/env/
source /home/coral/env/bin/activate
```
when you are activated, install the following packages:
```
pip3 install flask flask_cors pandas simplepam pyjwt pyArango dumper xarray openpyxl diskcache pycryptodome
```
_install jupyterhub and dependencies:_

```
pip3 install jupyterhub
npm install -g configurable-http-proxy
pip3 install notebook
```
When Jupyterhub is installed, the server can be run in development with the command 'Jupyterhub'
- ArangoDB can be installed on MacOS via homebrew:
```
brew install arangodb
```
when ArangoDB is installed you can start up the server by running the command:
```
/usr/local/Cellar/arangodb/<VERSION>/sbin/arangod &
```
You can also stop, start, or restart arangodb using brew services:
```
sudo brew services start arangodb
sudo brew services stop arangodb
sudo brew services restart arangodb
```
- In order to import data into arango, you will first need to create a database. When ArangoDB is running, you can run the arango shell with the command `arangosh`
- You may be prompted to reset the root password, if not, reset it in the shell with the following command:
```
require("/org/arangodb/users").update("root", "YOUR_NEW_PASSWORD")
```
refer [here](https://www.arangodb.com/docs/stable/security-change-root-password.html) for more information and troubleshooting.
- Once users are configured, you will need to create a new database to use for development. Without creating a new database, the data import will fail.
```
db._createDatabase('YOUR_DEV_DB_NAME')
```
- in order to run CORAL back end locally, you will need to create a config.json file in /back_end/var/, with the following parameters filled out. Running CORAL will fail without these parameters.
```json
{
    "WebService": {
        "port": 8082,
        "https": false, # can be true if you set up a self signed certificate
        "cert_pem": "/path/to/your/localhost.crt",
        "key_em": "/path/to/your/localhost.key",
        "plot_types_file": "plot_types.json",
        "auth_private": "/path/to/your/private/key",
        "auth_public": "/path/to/your/public/key"
    },
    "Workspace": {
        "data_dir": "/path/to/data/to/use/in/CORAL"
    },
    "Import": {
        "ontology_dir": "/path/to/ontologies",
        "entity_dir": "/path/to/entities",
        "process_dir": "/path/to/processes",
        "brick_dir": "/path/to/bricks"
    },
    "ArangoDB": {
        "url": "http://127.0.0.1:8529",
        "user": "root",
        "password": "<YOUR_PASSWORD>",
        "db": "<YOUR_DEV_DB_NAME>"
    }
}
```
- Once you have configured your config.json, you can import your data into the development database. This import may take a while depending on the size of your imported data.
_make a "reload_data" notebook to load and set everything up, then run it._
_sample "reload data" notebook contents (e.g., in /home/coral/prod/notebooks/reload_data.ipynb):_
```
from coral.dataprovider import DataProvider
from coral import toolx
toolx.init_system()
```
_NOTE: On MacOS, if the import fails with `[Errno 49] Can't assign requested address`, check in /etc/hosts to make sure that 127.0.0.1 is set to localhost. If you are still getting this error, restarting your computer should fix the issue. This is a bug with MacOS._

- Once the data import has completed, you can visit localhost:8529 to view the database and make sure everything has imported properly. You can also view the imported data via the Arango Shell.
### Install UI

See README.md in front\_end directory
