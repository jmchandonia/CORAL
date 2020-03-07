# generix_prototype
Prototype for the GeneriX project.

## Installation on Debian 10

Each step in the installation is described below.  If you already
have a prerequisite step installed, you can skip it.

### Build environment

_install package managers pip3 and npm:_

apt-get install python3-pip

apt-get install npm nodejs

_upgrade pip:_

pip3 install --upgrade pip

### Jupyterhub installation

_(based on https://jupyterhub.readthedocs.io/en/stable/quickstart.html)_

_install jupyter:_

pip3 install jupyter

_install jupyterhub and dependencies:_

pip3 install jupyterhub

npm install -g configurable-http-proxy

pip3 install notebook

_set up /etc/jupyterhub and /srv/jupyterhub files as described in docs above, or copy from another installation._

_make these files owned by jupyterhub, delete old sqlite and jupyterhub_cookie_secret_
