---
layout: post
title: Flask-Twitter-OEmbedder and Flask Extension Testing
date: 2013-06-26 15:37
comments: true
categories:
- Flask
- Python
- Testing
---

Flask-Twitter-OEmbedder
----------

The Twitter API V1.1 provides an endpoint for easily [embedding tweets](https://dev.twitter.com/docs/api/1.1/get/statuses/oembed) into your webpages. However, Twitter rate limits this endpoint and requires authorization. Flask Twitter OEmbedder gets your Twitter credentials from your `app.config` and exposes the `oembed_tweet` function to the Jinja templates. Flask Twitter OEmbedder also manages the caching of the tweets, given an arbitrary cache using Flask-Cache.

You can check it out and fork it on [GitHub](https://github.com/eriktaubeneck/flask-twitter-oembedder). Feature requests, issues, and anything else are encouraged! This is very much alpha and I plan to continue working on it.

Flask Extension Testing
---------

[Flask-Twitter-OEmbedder](https://github.com/eriktaubeneck/flask-twitter-oembedder) was the first Flask extension I have written (and really the first proper Python package I've ever written). This summer I am lucky enough to be participating in [Hacker School](https://www.hackerschool.com/) and one of my goals for the batch was to be able to write unit tests for my code that I develop. Since this was my first proper package, I figured it was a great place to start.

<!-- more -->

Testing in the abstract seems reflexive and redundent; I wrote code specifically to perform `x`, why would I write more code to make sure that it does `x`? This was a particularly difficult mental block for me, especially coming to development from mathematics. However, as your code base grows and relies on more and more abstraction, when something breaks, testing helps you find exactly what you broke and where to fix it. It's not uncommon for libraries and extensions to change their API's at times, in which case it may not even be code that you wrote to do `x`, and now it does `y`. Luckily earlier this year, I attended PyCon and saw [this](http://pyvideo.org/video/1674/getting-started-with-automated-testing) great presentation on getting starting with automated testing Python.

After getting past my mental testing block, I was faced with a few other challanges with getting testing working with my Flask extension. I had broken my extension into a handful of base states which I wanted to test:

- the `oembed_tweet()` function is avaliable in the Jinja templates
- the `oembed_tweet()` function properly embeds a tweet when given a valid tweet id
- the `oembed_tweet()` function fails properly (depending on the `app.debug` and local `debug` state) when given an invalid tweet id

Each of these presented their own challanges. The first challange however, was just approaching the problem at hand. The testing documentation for Flask is all based for testing Flask apps, not Flask extensions. However, it quickly became clear that it was sufficent to use [Flask-Testing](http://pythonhosted.org/Flask-Testing/) to create a "dummy" app which would utilize my extension and be able to test if it worked properly.  Unfortunetly, Flask-Testing doesn't have a method like `assertExists`, so I ended up testing

     assert type(self.get_context_variable('oembed_tweet')) is types.FunctionType

The next challange was being able to run the tests offline. In general, unit tests shouldn't care if external API's are working or not. It is certainly useful and appropriate in some cases to write tests that to check for this, but for this test we just want to know if our code is working as expected, assuming that Twitter's API is working correctly.We(I paired with one of the awesome Hacker School facilitators, [Zach Allaun](https://github.com/zachallaun)) started with [vcrpy](https://github.com/kevin1024/vcrpy), which is a port of the Ruby [vcr](https://github.com/vcr/vcr) gem, however this didn't work quite right. We then moved onto [cassette](https://github.com/uber/cassette) but it unfortunetly didn't play nice with HTTPS. Finally we landed on [HTTPretty](https://github.com/gabrielfalcao/HTTPretty) which did exactly what we needed. We grabbed the actual response from Twitter and dumped it into a JSON, then HTTPretty blocks any out going requests to specific urls and returns the content of the JSON as if the request had gone through normally. It can be used as followed:

    @httpretty.activate
    def test_oembed_tweet_valid_id_debug_off(self):
        with open('tests/data/99530515043983360.json') as f:
            httpretty.register_uri(httpretty.GET, 'https://api.twitter.com/1.1/statuses/oembed.json?id=99530515043983360',
                body = f.read())
        response = self.client.get('/')
        oembed_tweet = self.get_context_variable('oembed_tweet')
        valid = oembed_tweet('99530515043983360')
        assert type(valid) is Markup

In this example, the `oembed_tweet` fuction makes a GET request using the `requests` package to the `uri` that we specified in the `httpretty.register_uri()` call, and the response is what we specified as the `body` in the same function.

One final interesting case is when we wanted to test what happens when we want to test how Flask-Twitter-OEmbedder handles an error from the Twitter API. In a development setting, we likely want this to actually raise an exception so that we can investigate what is causing the error (this could be a number of things: incorrect tweet id, Twitter API outage, deleted tweet, etc), but in production we would likely want it to fail gracefully and just return an empty string. Testing for an exception is fairly straight forward:

    try:
        invalid = oembed_tweet('abc')
    except Exception as e:
        assert type(e) is KeyError

There is one little trick here, however, that is easy to overlook. We are expecting the second line to fail, and then we are asserting that the failure is the type that we expect. However, what if the second line doesn't fail? In the context of the test, we would classify this as a failure, since the failure on line 2 is what we want. But in the code above, if line 2 doesn't fail for some reason, the `assert` will never happen and the test will pass. We can fix this by adding one line after line 2:

    try:
        invalid = oembed_tweet('abc')
        assert False
    except Exception as e:
        assert type(e) is KeyError

The addition of `assert False` will force the `try` clause to fail, even if line 2 doesn't fail as expected, and since `assert False` raises an `Assertion Error`, line 5 will fail properly.
