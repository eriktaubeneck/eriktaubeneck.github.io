---
layout: post
title: print can be deceiving
date: 2013-03-19 11:42
comments: true
categories:
---

This is more of a short musing than a blog post, but maybe some insight that can help a beginner. This is written specifically with respect to Python, but I think some of the basic ideas translate to other object oriented languages.

when `print` was your best friend
-----------------

When someone is new to Python, and more so when new to programming in general, `print` is your best friend. Learning a new language is done by comparing what you expect happen and what actually happen. The prototypical example in any language is

    print 'Hello World!'

and a new comer to Python going through something like [Learn Python the Hard Way](http://learnpythonthehardway.org/) (LPTHW) will spend a number of lessons where a script ends with a `print` statement revealing the *answer*. This is notable because in a production system, `print` isn't used much at all, unless something goes wrong.

<!-- more -->

when `print` isn't used
-------------------

There are varying types of "systems" you can build in Python: (in rough order of rising complexity) scripts, packages, applications, web services/apis. This list is certainly not exhaustive, but except for the most basic scripts that calculate something like a summary statistic, `print` is rarely used.

Most python "systems" (or really in any language) are used to deal with data structures that are rarely reduced down to one dimension. For example, [Project Euler, Problem 1](http://projecteuler.net/problem=1) challenges you to find the sum of all the multiples of 3 or 5 below 1000. Python accomplishes this in 1 step:

    print sum([x for x in range(1000) if x % 3 == 0 or x % 5 == 0])

In this case, we are looking for the *answer* to the problem. However, most "systems" aren't designed to answer a problem, but to *solve* it. A python module typically defines certain models and methods for manipulating those methods. A web application models objects like users and is able to pass objects specific to that user to the browser. A web scrapper loads external webpages, allowing you to collect relevant data from the page. You are unlikely to use `print` to handle that data. More likely you will store it to a database or a flat file.

when `print` can be deceiving
--------------------

You will never stop using `print`, it just will stop to be the intention of your programs. However, when ever working with a new module or framework, often times you are back to Hello World. By now you are able to read the docs and write a small program without any issue. But as you start to explore the more subtle features, often the docs will simply imply the correct implementation.

`print` will again be your best friend when you mess something up and you're trying to figure out where you went wrong. However, `print` can often hide important things when you are debugging. For example, in an interactive python session:

    >>> print 2
    2
    >>> print '2'
    2

`print` isn't going let you know if the object you are printing here is a `int` or a `str`. Even more insidious, it could be a custom class with an attribute `val = 2` with it's `__repr__` method defined as `print self.val`. This is roughly the problem I recently ran into.

I was working with the [python-twitter](https://github.com/bear/python-twitter) module and trying to deal with different twitter errors differently. The pseudo-code to figure out the errors:

    try:
      x = twitter_api.call()
    except TwitterError as error:
      print error

The result I got here in one case was `[{'message':'error code 1'}]` and in the other `error code 2`. Now this is kind of a pain in the ass, and really the result of python-twitter handling different errors with different methods (probably an issue worth fixing), but it's solvable with

    try:
      x = twitter_api.call()
    except:
      if type(error) == list and error[0]['message'] == 'error code 1':
        #do whatever you need for error message 1
      elif error == 'error code 2':
        #do whatever you need for error message 2
      else:
        raise #Errors should never pass silently.

The problem here is that error is not a `str` but a instance of the `TwitterError` class, which has an attribute `message` that is printed when `print` is called on the object. This is expect behavior, and quite obviously implied by `TwitterError as error`. But easy enough to miss. A find and replace of `error` to `error.message` on the above code fixes it.

One really handy way to help with these types of situations is running `python -i your_script.py`. This will open up an interactive session after the script exits upon an error or on completion. In this case, I was able observe the `error` variable after the `TwitterError` was raised when I thought that it would be captured. So remember, `print` doesn't always give you the full picture.
