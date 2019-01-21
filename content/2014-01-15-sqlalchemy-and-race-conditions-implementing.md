---
layout: post
title: SQLAlchemy and Race Conditions: Implementing `get_one_or_create()`
date: 2014-01-15 13:57
comments: true
categories: [python, SQLAlchemy, Celery]
---

Note: Examples here are built with respect to [Flask SQLAlchemy](http://pythonhosted.org/Flask-SQLAlchemy/), and while some notation may match that convention, the concepts should apply to use of [SQLAlchemy](http://www.sqlalchemy.org/) in general.

##Motivation
Suppose we have a [Flask](http://flask.pocoo.org/) app that interacts with an API on a site that hosts webgames. Our users have OAuth'ed our application into the API so we can see their activity, and we want to track which games they have beat. (We'll assume that users only beat a game once or more generally we are only concerned with the first time they beat it.) We create the `Game` and `GameBeat` models like so:

<!-- more -->

``` python
class Game(db.Model):
    __tablename__  = 'games'
    id = db.Column(db.Integer, primary_key=True)
    provider_game_id = db.Column(db.String(255))
    provider_game_name = db.Column(db.String(255))
    provider_game_category = db.Column(db.String(255))

class GameBeat(db.Model):
    __tablename__ = 'game_beats'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    game = db.relationship("Game",
                           backref="beats",
                           lazy="joined",
                           innerjoin=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("User",
                           backref="game_beats",
                           lazy="joined",
                           innerjoin=True)
    beat_at = db.Column(db.DateTime())
```

A few notes on these models. This assumes that each `Game` object coming from the API has an `id`, `name`, and `category` attribute, and anytime a game is beat by a user, you can get the datetime of when it was beat. One other convention is using `db.String(255)` for `provider_game_id` (rather than `db.Integer`). You will often see this with APIs where the `ids` can be very large integers (think of the number of Tweets on Twitter for example), and while Python handles big ints well, unless you want to use big ints for actually doing math, a string will be much more efficient (and you'll be less likely to have an issue with your backend datastore).

##Implementing a basic `get_one_or_create()`

NOTE: The original implementation I used was first inspired from [this Stack Overflow](http://stackoverflow.com/questions/2546207/does-sqlalchemy-have-an-equivalent-of-djangos-get-or-create) question.

If you've ever played around with [Django](https://www.djangoproject.com/), you've probably seen the `get_or_create()` function, but if not the concept is straight forward. First look for an object given a set of constraints, and if it doesn't exist, create it. The usefulness here is pretty obvious in our above example. Without it, given a list of `game_beats` from the API and a `user`, we'd have to do something like

```
for game_beat_data in game_beat_data_list:
    if db.session.query(Game).filter(Game.provider_game_id == game_beat_data['game']['game_id']).count() == 0:
        game = Game(provider_game_id = game_beat_data['game']['game_id'],
                    provider_game_name = game_beat_data['game']['game_name'],
                    provider_game_category = game_beat_data['game']['game_category']
                    )
    else:
        game = db.session.query(Game).filter(Game.provider_game_id == game_beat_data['game']['game_id']).one()
    if db.session.query(GameBeat).filter(GameBeat.game == game).filter(GameBeat.user == user).count() == 0:
        game_beat = GameBeat(game = game,
                             user = user,
                             beat_at = game_beat_data['beat_at']
                             )
    else:
        game_beat = db.session.query(GameBeat).filter(GameBeat.game == game).filter(GameBeat.user == user).one()
    db.session.add(game_beat)
db.session.commit()
```

This is quite verbose, and the logic is repeated twice, so it seems like a perfect place to write a function. Here's a first attempt, (and we'll build from here):

```
from sqlalchemy.orm.exc import NoResultFound

def get_one_or_create(session,
                      model,
                      **kwargs):
   try:
       return session.query(model).filter_by(**kwargs).one()
   except NoResultFound:
       return model(**kwargs)
```

There are a couple small differences here. Most obvious is the change to a `try/except` block rather than getting the `count()` explicitly. The advantage here is that if the object exists, we only have to make one call to the datastore. The other is the use of `filter_by()`, which is just a version of `filter` that uses keyword arguments.

Using this function, our above example now becomes:

```
for game_beat_data in game_beat_data_list:
    game = get_one_or_create(
        db.session,
        Game,
        provider_game_id = game_beat_data['game']['game_id']
    )
    game_beat = get_one_or_create(
        db.session,
        GameBeat,
        game = game,
        user = user,
        beat_at = game_beat_data['beat_at']
    )
    db.session.add(game_beat)
db.session.commit()
```

Now, since I've broken the inputs into our function onto multiple lines, we've only dropped from 17 lines to 15, however I'd still argue this is a HUGE decrease in complexity. We can now actually fit in under 80 characters without having to use `\` for newlines, but more generally, it's simply more readable.

## A small modification

I'm not going to motivate this, but sometimes you'll want to know if the object you're getting back was newly created or pulled from the datastore, so we can easily return a `bool` as well by updating our function to

```
from sqlalchemy.orm.exc import NoResultFound

def get_one_or_create(session,
                      model,
                      **kwargs):
   try:
       return session.query(model).filter_by(**kwargs).one(), True
   except NoResultFound:
       return model(**kwargs), False
```

and now we just have to remember that when we use it, to unpack into two variables

```
obj, exists = get_one_or_create( … )
```

or else we will end up with a `tuple` where we expected `obj`.

## The `@classmethod` decorator

One of my favorite Python patterns is using the `@classmethod` decorator with a creator function. In our above example, suppose we want to be able to create a `Game` object, but we may or may not have the `provider_game_name` and `provider_game_category` immediately available. We can update our model definition (assuming we have a `get_game_data_from_api` function from our API):

```
class Game(db.Model):
    __tablename__  = 'games'
    id = db.Column(db.Integer, primary_key=True)
    provider_game_id = db.Column(db.String(255))
    provider_game_name = db.Column(db.String(255))
    provider_game_category = db.Column(db.String(255))

    @classmethod
    create_from_provider_game_id(cls, provider_game_id,**kwargs):
        provider_game_name = kwargs.get('provider_game_name', None)
        provider_game_category = kwargs.get('provider_game_category', None)
        if not provider_game_name and provider_game_category:
            game_data = get_game_data_from_api(provider_game_id)
            provider_game_name = game_data['provider_game_name']
            provider_game_category = game_data['provider_game_category']
        return cls(provider_game_id = provider_game_id,
                   provider_game_name = provider_game_name,
                   provider_game_category = provider_game_category)
```

now if we do

```
game = Game.create_from_provider_game_id(provider_game_id = game_beat_data['game']['id'])
```

we get a new `Game` object which will ping the API in order to get the other data to fill it out. But, if we already have the data (or we *maybe* have the data), we can do the following:

```
game = Game.create_from_provider_game_id(
           provider_game_id = game_beat_data['game']['id'],
           provider_game_name = game_beat_data['game'].get('name', None),
           provider_game_category = game_beat_data['game'].get('category', None)
       )

```

I like to think of writing code like this as being *fault tolerant*. If you've played with external APIs before, their behavior can often change slightly. Moreover, writing code like this gives me a consistent pattern, so if in one case I have a collection of `dict`s from an API with all the relevant game data, and in another case I only have a collection of the `provider_game_id`s, I can use the same pattern. If I have all the data, I can save myself `n` calls to the API, and if I'm not sure (or maybe the API is inconsistent - yes it happens), it will still work.


## Updating `get_one_or_create`

It's quickly obvious that our current implementation of `get_one_or_create()` won't handle such pattern for creating model instances. But this is programming, we are the creators. Let's update our function:

```
from sqlalchemy.orm.exc import NoResultFound

def get_one_or_create(session,
                      model,
                      create_method='',
                      create_method_kwargs=None,
                      **kwargs):
    try:
        return session.query(model).filter_by(**kwargs).one(), True
    except NoResultFound:
        kwargs.update(create_method_kwargs or {})
        return getattr(model, create_method, model)(**kwargs), False
```

The reason for adding this `create_method_kwargs` `dict` is fairly straight forward: consider a case where we need to hand a `user` to our API method `get_game_data_from_api`, but we don't store a `user` on the `Game` object and certainly don't want to include it in the `filter_by`.

At this point, we have a pretty robust `get_one_or_create()` function that worked quite well for me, until it didn't.

## An Unexpected Exception

By using my newly minted `get_one_or_create()` wherever I create objects, you can imagine my surprise when `MultipleResultsFound` exceptions starting being raised when trying to `get_one_or_create()` a `Game`. I scoured my code for any place that I created a `Game`; luckily `grep` makes this easy. Nothing. I expanded my test so that I was mocking a scan for 100 users. Nothing. Maybe there was a unicode issue where the *get* part was trying to match to a unicode to string (and failing) but the *create* part was then creating the attribute as a string. A new test quickly disproved this. Nothing.

I was lost. I was writing tests *hoping* that they would fail just so I could figure out what was going wrong. And it was 4am. I *hate* going to sleep at a point like this. (I use *sleep* loosely here - I generally don't sleep well and lay awake trying to figure out how to fix my problem.) I'm not sure if it was that night or the next morning (or even when you draw the line going to bed at 4am for that matter…), but I eventually realized why I was getting duplicate objects in my datastore.

During the time between the *get* call when the object doesn't exist and the call to `db.session.commit()`, the object was created somewhere else. I was using Celery to batch the update and it was a brand new scan, so a lot of stuff was being created. Since the `db.session.commit()` comes at the end of the loop, there can actually be a fair amount of time between these calls. But even if a `db.session.commit()` happened sooner, we want to be *sure* that another matching object didn't get created between the *get* and *create* parts of a function.

## Celery "async" and Race Conditions

### `@celery.task()`

I use quotes here in the way I'd use air quotes if we were talking: the [Celery](http://www.celeryproject.org/) async task model isn't true async in the way that [Twisted](http://twistedmatrix.com/trac/) or [`asyncio`](http://docs.python.org/3.4/library/asyncio.html) is. Instead it uses an external messaging system (I use [Redis](http://redis.io/) - mostly due to the price on [Heroku](https://www.heroku.com/)). Functions and their inputs (remember that in Python, functions, like everything else, are objects) are JSONified, stored in the message system, and then deJSONified and executed in a completely separate process.

It does become more complicated if you care about the result of a function call, but often you call functions only for their side effects. Sometimes you'll want to kick off a job of a few such function calls as a result of a web request. If the job takes awhile (anything more than a second) you certainly do not wish to wait (or can't, eventually you'll timeout) for that function to complete before responding. Celery makes this pattern straight forward, if not easy, to accomplish with a synchronous web framework like Flask.

Celery also makes it really easy to horizontally scale a batch of jobs. Suppose we want to update the `GameBeat`s for all our users. We could create a celery task like so

```
from app import celery, db
from app.models import User
from app.provider_apis import get_provider_api

@celery.task()
def update_game_beats_for_user_id(user_id):
    user = db.session.query(User).get(user_id)
    api = get_provider_api(user)
    game_beat_data_list = api.get_game_beats()
    for game_beat_data in game_beat_data_list:
        …
```

where the `…` completes the pattern above showing the usage of `get_one_or_create()`. We can now create a task for each user by running

```
from app.tasks import update_game_beats_for_user_id
from app import db
from app.models import User

users = db.session.query(User).query.all()
for user in users
    update_game_beats_for_user_id.delay(user.id)
```

This makes it possible to spin up a number of Celery workers (Heroku for this is as easy as scrolling a slider on a web interface and clicking "Apply", or a single short bash command) and get all these tasks done quickly.

### Race Conditions

Whenever you have multiple concurrent processes interacting with an external service, you have to be concerned about race conditions, e.g. from the perspective of any process, the state of that external service may change at anytime without any interaction from that process. Luckily, Celery is designed to handle this and maps jobs out in a way that no two processes will receive the same message.

SQLAlchemy even has some protection against this, although I'm not sure exactly how it's implemented. I do know that if I have an `ipython` shell open with a transition pending, a query in another process will stall. This goes out the window, however, when we're working with Celery workers on separate Heroku instances or even separate web instances. So we certainly want to protect against this type of thing in production.

In our example, since we plan to look up `Game` objects by `provider_game_id` and expect only one instance, we should have defined that column with a unique constraint like so:

```
class Game(db.Model):
    …
    provider_game_id = db.Column(db.String(255), unique=True)
    …
```

Luckily we can make this change after the fact (which I won't show here, but I plan to write about next). Had we done this originally, we would never have gotten the `MultipleResultsFound` exception, but instead would have gotten a `IntegrityError` when trying to execute `db.session.commit()` of an transition that would *create* our duplicated item. This is desirable since the exception comes *before* the duplicate is introduced into the datastore. However, it would be best for our `get_one_or_create` function to take care of this as well.

## A "final" `get_one_or_create()`

Again, think air quotes. As a developer, I never think or anything as final. Or maybe I always think an implementation is final, and I'm always wrong. Regardless, of the concerns I've reached so far, here is a "final" version:

```
def get_one_or_create(session,
                      model,
                      create_method='',
                      create_method_kwargs=None,
                      **kwargs):
    try:
        return session.query(model).filter_by(**kwargs).one(), True
    except NoResultFound:
        kwargs.update(create_method_kwargs or {})
        created = getattr(model, create_method, model)(**kwargs)
        try:
            session.add(created)
            session.commit()
            return created, False
        except IntegrityError:
            session.rollback()
            return session.query(model).filter_by(**kwargs).one(), True
```

Here's what's happening. It tries to find the right object, and if it finds it, it returns it. If not, it creates it, adds it to the session, and attempts to commit. In the mean time, if another process has created and committed an object with the same details we filtered by, an `IntegrityError` raises and is caught. This means we should be able to get the newly created object, so we now get that and return it.

You'll notice one major difference from our earlier versions: `session.commit()` is now in the function. I've avoided doing this thus far due to the recommended usage in the SQLAlchemy documentations on [sessions](http://docs.sqlalchemy.org/en/latest/orm/session.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it):

> As a general rule, keep the lifecycle of the session separate and external from functions and objects that access and/or manipulate database data.

The reason we must add this into our function call here, is that if we do the `db.session.commit()` after making several calls to `get_one_or_create()` and the `IntegrityError` was raised, we'd have no idea which created object caused it and we'd have to start the entire transaction over (and we'd have to write logic outside the function to handle all this). Since our `get_one_or_create()` function is written generally for any model and unique keywords, rather than specific logic tied to a specific model, I don't think it seriously conflicts with the SQLAlchemy philosophy.

**UPDATE:** I have recanted here and decided that using `session.flush()` is superior to `session.commit()` for line 13 of the function. See my [newer blog post](http://skien.cc/blog/2014/02/06/sqlalchemy-and-race-conditions-follow-up/) for a detailed explanation of why.

**UPDATE 2:** I've updated using a `{}` as a default value in the function as this is typical Python gotcha. Thanks for the [comment](http://skien.cc/blog/2014/02/06/sqlalchemy-and-race-conditions-follow-up/#comment-1371570667), Nigel! If your curious about this gotcha, check out this [StackOverflow question](http://stackoverflow.com/questions/5712904/empty-dictionary-as-default-value-for-keyword-argument-in-python-function-dicti) and [this blog post](http://pythonconquerstheuniverse.wordpress.com/category/python-gotchas/).

## Final Thoughts

Race conditions and asynchronous programing are difficult, especially when working in a framework that doesn't force you to work or think that way. Flask and certainly Flask-SQLAlchemy aren't extremely well suited to handle this, but also with Flask's synchronous handling of requests, it doesn't become a issue often. When scaling, however, you being to increase the probability of such occurrences happen.

How does this work in Tornado or Twisted? My friend and former colleague [Brian Muller](https://github.com/bmuller) wrote [Twistar](http://findingscience.com/twistar/), a Python implementation of a nonblocking active record pattern interface to relational databases (built to use with Twisted). It's been on my list of packages to read. To some extent, building a webapp in Twisted has a high upfront cost, but it also has this added value of forcing you to think deeper and see these problems before you have a few hundred duplicated entries in your database.

I love Flask and the community, and it has all been very good to me as being quite new to web app development, but part of me wants to start playing around with the JS template systems like [React](http://facebook.github.io/react/). This also makes sense as you start getting into the realm of iOS and Android apps. At some point you have many different "front ends" and your backend is really just serving up data to fill it. At that point, a centralized template system like Jinja makes less sense, and moving from Flask to Twisted makes more sense.
