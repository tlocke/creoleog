Creoleog
========

Creoleog is a blogging engine written using Django on Google App Engine. You can
see Creoleog up and running at http://creoleog.appspot.com/

To run it locally:

* Install [Google App Engine](https://developers.google.com/appengine/).
* In the `creoleog` directory, execute `pip install -r requirements.txt`.
* For your particular installation you need to create a file called
  `creoleog/creoleog/secret.py` containing the line:
  `SECRET_KEY = " your entropy here "`
* Start and stop the server with `startserver` and `stopserver`.
