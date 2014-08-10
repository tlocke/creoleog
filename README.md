Creoleog
========

Creoleog is a blogging engine written using Django on Google App Engine. You can
see Creoleog up and running at http://creoleog.appspot.com/

To run it locally:

* Install [Google App Engine](https://developers.google.com/appengine/).
* In the `creoleog` directory, execute `pip install -r requirements.txt`.
* Still in the `creoleog` directory, create a soft link to the `creole` Python
  library.
* For your particular installation you need to create a file called
  `creoleog/creoleog/secret.py` containing the line:
  `SECRET_KEY = " your entropy here "`
* Start and stop the server with `startserver` and `stopserver`.

There are tests that first do a PEP8 check on the code, and then execute some
system tests with Imprimatur. To run the tests:

* Install [Imprimatur](http://imprimatur.wikispaces.com/).
* Run ./test/runtests
