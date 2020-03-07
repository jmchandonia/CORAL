# generix_prototype
Prototype for the GeneriX project.

## Installation on Debian 10

Each step in the installation is described below.  If you already
have a prerequisite step installed, you can skip it.

### Build environment

- install package managers pip3 and npm:
apt-get install python3-pip
apt-get install npm nodejs
- upgrade pip:
pip3 install --upgrade pip

### Jupyterhub installation

- (based on https://jupyterhub.readthedocs.io/en/stable/quickstart.html)
- install jupyter:
pip3 install jupyter
- install jupyterhub and dependencies:
pip3 install jupyterhub
npm install -g configurable-http-proxy
pip3 install notebook

- set up /etc/jupyterhub and /srv/jupyterhub files as described in docs
- above, or copy from another installation.
- make these files owned by jupyterhub, delete old sqlite and jupyterhub_cookie_secret
