REQUIREMENTS
============

* Django 3.2
* Python 3.x
* gunicorn for production deployment
* gettext
* requests
* libxml2-python

The virtualenv install script installs everything but the Python sqlite and xml2
extensions.

HOW TO RUN
==========

# Create virtualenv environment
./install-virtualenv.sh

# init virtualenv
source env/bin/activate

# install requrirements
pip install -r requirements.txt

# Create local configuration
cp news/local_settings.py.template news/local_settings.py

# Set at least a secret key, preferably a working email address too
$EDITOR news/local_settings.py

# Compile translations
./manage.py compilemessages

