---
layout: post
title: Using Flask with nginx and uWSGI
date: 2013-01-07 11:49
comments: true
---

Starting with AWS
------------------

I'm using [Amazon Web Services](http://aws.amazon.com) for hosting my application. It has all sorts of fantastic capabilities, but for small stuff all I'm really using it for is to run a Ubuntu 12.04 Server. (AMI: ubuntu/images/ebs/ubuntu-precise-12.04-amd64-server-20121001 (ami-3d4ff254)). This is on the free tier, so if you're a new account, you can run one of these for free for a year. If not, running it full time will cost you about $15/month. Attach that thing to a elastic IP (they're free as long as you're using it) and connect with SSH.

    ssh -i key.pem ubuntu@aws-ip-address

One of the first things I do is add my public key to `~/.ssh/authorized_keys` on the server so that I can connect without the `-i key.pem`.

<!-- more -->

Installing nginx (engine-x)
---------------------------

First, add the correct repo so that you can install the correct version. Create a file `/etc/apt/sources.list.d/nginx-lucid.list` and add the following:

    deb http://nginx.org/packages/ubuntu/ lucid nginx
    deb-src http://nginx.org/packages/ubuntu/ lucid nginx

We will also add the gpg key to to the apt keyring. From your home directory, run:

    wget http://nginx.org/keys/nginx_signing.key
    sudo apt-key add nginx_signing.key
    rm nginx_signing.key

Now we can install nginx with:

    sudo apt-get update
    sudo apt-get install nginx

Installing uWSGI
----------------

First, we need to install pip, then we can use pip to install uISGI.

    sudo apt-get install python-dev build-essential python-pip
    sudo pip install uwsgi

We are going to want to un uWSGI in the background, so we will create a uwsgi user:

    sudo useradd -c 'uwsgi user,,,' -g nginx -d /nonexistent -s /bin/false uwsgi

Now, create the file `/etc/init/uwsgi.conf` and put the following in it:

    description "uWSGI"
    start on runlevel [2345]
    stop on runlevel [06]

    respawn

    exec uwsgi --master --processes 4 --die-on-term --uid uwsgi --gid nginx --socket /tmp/uwsgi.sock --chmod-socket 660 --no-site --vhost --logto /var/log/uwsgi.log

Flask Configuration
-------------------

We need to set up a Python virtual environment so that we can point uWSGI to the correct python interpreter. If you plan on ever using MySQL with Flask, then you'll need to use the `--system-site-packages` option for your virtual environment. For some reason, I was unable to install python-mysqldb so that the virtual environment could use it without this option.

    sudo pip install virtualenv
    sudo virtualenv --system-site-packages /srv/webapps/helloworld/env
    source /srv/webapps/helloworld/env/bin/activate

You are now using the virtual environment. To install Flask, simply run:

    sudo pip install flask

Now, we can deactivate the virtual environment with:

    deactivate

For right now, I'm just going to set up the hello world Flask app. Going to `aws-ip-address` should simply produce "Hello, world!". We are going to store this in `/srv/webapps/helloworld`. It can really go wherever you want, so adjust accordingly if you want to put it somewhere else.

    sudo mkdir -p /etc/webapps/helloworld

Now, inside of this directory, we are going to put our Flask app. It seems odd, but we are going to create another folder called `helloworld`. Then inside of that, we are going put the webapp inside of that dir in the file `__init__.py`. We will also create the `static` folder for static files like images and css stylesheets.

    cd /etc/webapps/helloworld
    sudo mkdir helloworld
    sudo mkdir helloworld/static
    sudo touch helloworld/__init__.py

Open this file and include:

    from flask import Flask
    app = Flask(__name__)

    @app.route('/')
    def landing():
      return 'Hello, world!'

This allows us to import `helloworld` as a module. In `/etc/webapps/helloworld` create a file called `runserver.py`. In this we put:

    from helloworld import app

    if __name__ == '__main__':
      app.run(host='0.0.0.0', port=80)

The `if __name__ == '__main__'` is extremely important, because we only want this part to run if we run the script ourselves (rather than through a uWSGI process.). By manually setting the host and port like this, we should be able to run this and be able to access it through the built in development server. From `/srv/webapps/helloworld` run:

    source /env/bin/activate
    sudo python runserver.py

Now, by going to `aws-ip-address` in your browser, you should see "Hello, world!".  If you get an error that the address is already in use, nginx is probably already running and you can kill it with `sudo killall nginx`. If the page seems to hang and never loads, check your AWS security groups to make sure you have port 80 (HTTP) open. When you're done, deactivate the virtual environment:

    deactivate

Congrats! You have a Flask app running. Now, let's getting running with nginx and uWSGI so it can handle a bit more traffic.

Setting up nginx and uWSGI
---------------------------

First, let's add some permissions for our uwsgi user.

    sudo usermod -a -G nginx uwsgi

adds the user `uwsgi` to the group `nginx`.

    sudo chown -R uwsgi:nginx /srv/webapps/helloworld

changes the owner of the directory to `uwsgi:nginx`.

    sudo chmod -R g+w /srv/webapps/helloworld

give the group owner write capabilities to so that uWSGI can write the compiled python files.

nginx uses `.conf` files to set it's configuration options. We first remove the default configuration file:

    sudo rm /etc/nginx/conf.d/default.conf

If you don't have this file, you may be running a different version on nginx. Now create `/etc/nginx/conf.d/helloworld.conf` and include the following:

    server {
        listen       80;
        server_name  localhost;

        location /static {
            alias /srv/webapps/helloworld/helloworld/static;
        }

        location / {
            include uwsgi_params;
            uwsgi_pass unix:/tmp/uwsgi.sock;
            uwsgi_param UWSGI_CHDIR /srv/webapps/helloworld;
            uwsgi_param UWSGI_PYHOME /srv/webapps/helloworld/env;
            uwsgi_param UWSGI_MODULE helloworld;
            uwsgi_param UWSGI_CALLABLE app;
        }
    }

And there you go! Flask with a real deployment option. That said, I should say that I am not a deployment expert, and much of this here is exactly from a [blog by Conrad Kramer](http://blog.kramerapps.com/post/22551999777/flask-uwsgi-nginx-ubuntu) with a few changes. Any suggestions on how to make this process easier or better, links to other tutorials, or anything of the like, please let me know at erik(dot)taubeneck(at)gmail.com.
