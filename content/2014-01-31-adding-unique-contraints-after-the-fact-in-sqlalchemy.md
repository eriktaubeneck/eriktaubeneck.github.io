---
layout: post
title: Adding Unique Constraints After the Fact in SQLAlchemy
date: 2014-01-31 16:40
comments: true
categories: [python, SQLAlchemy, alembic, Postgres]
---


In a [previous post](http://skien.cc/blog/2014/01/15/sqlalchemy-and-race-conditions-implementing/), I wrote about writing a `get_one_or_create()` function for SQLAlchemy. Turns out that I had inadvertently created a race condition while horizontally scaling on Heroku. That post explains, in detail, the solution I came up with for moving forward, however I still had duplicate objects in my database that needed to remove. Since I'm on Heroku, I'm using Postgres (although I'm highly opinionated towards using Postgres often), so some of this may be Postgres specific, and I will do my best to note when that's the case.

I'll use the same example models that I used in my previous post. We had `Game` and `GameBeat` models:

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

but had accidentally created multiple `Game` objects with the same `provider_game_id` attribute. At the very least, we would rather have the class definition and database representation put a unique constraint on this attribute so that if we ever attempted to create such a duplicate `Game` object, we'll end up raising a `IntegrityError` and the duplicate won't actually get added to the datastore. (Again, a [previous post](http://skien.cc/blog/2014/01/15/sqlalchemy-and-race-conditions-implementing/) discusses how to handle this).

The class definition updates to:

```
class Game(db.Model):
    __tablename__  = 'games'
    id = db.Column(db.Integer, primary_key=True)
    provider_game_id = db.Column(db.String(255), unique=True)
    provider_game_name = db.Column(db.String(255))
    provider_game_category = db.Column(db.String(255))
```

We still, however need to make the update to our datastore (Postgres, in our case), along with finding and eliminating the duplicates we introduced into the system.

##Using `alembic` to update the datastore

If you're not using [`alembic`](http://alembic.readthedocs.org/en/latest/) with `SQLAlchemy`, you're doing it wrong. OK - that's a bit harsh (and if you're doing it some other way, let me know!), but if you ever plan to change your data model, you'll need to change your datastore along with it, and `alembic` is an excellent tool to help you along. It's version control for your database schema; think Git for your class models.

`alembic` provides the useful `autogenerate` option that can be used like so:

```
$ alembic --autogenerate -m "add unique constraint to Game.provider_game_id"
```

(Some [setup](http://alembic.readthedocs.org/en/latest/tutorial.html#auto-generating-migrations) is required to get this option to work.) You should now have a new file in your `alembic/versions` directory with the name something like `10f2a956bad5_add_unique_constrain.py`. (Your hash at the beginning is going to almost certainly be different.) If you look at the file, you'll notice that it is mostly empty. Unfortunately, `alembic` isn't able to identify newly added unique constraints automatically, so we will have to fill it in.

I found the [documentation](http://alembic.readthedocs.org/en/rel_0_1/ops.html#alembic.op.create_unique_constraint) on adding a unique constraint a bit confusing at first. The function we want to use is `op.create_unique_constraint()`, which takes arguments `name`, `source`, and `local_cols`. At first, I thought `name` was the name of the column which I wanted to make unique, however it's actually the name of the constraint. In my setup (with Postgres), I was able to let `name = None` and have SQLAlchemy and Postgres sort it out. The `source` is just a string of the name of the table, and `local_cols` is where we specify what we want to make unique. The somewhat tricky part here is that we can make a constraint where `(col1,col2)` needs to be unique (not individually unique, but the combination of the two), so this parameter takes a list. In our case, the list will only have a single member, `provider_game_id`. Within the `upgrade` function in our migration file, we can add:

```
def upgrade():
    op.create_unique_constraint(None,
                                "games",
                                ["provider_game_id"])
```
and under the `downgrade` function, we can add:

```
def downgrade():
    op.drop_contraint("provider_game_id",
                      "games",
                       "unique")
```

If there are any existing duplicates and we run this, however, we are going to get an `IntegrityError`. So it's time to seek and destroy.

##Finding Duplicate Entries

As we're debugging the situation, one of the first things we'll want see how many duplicates we have of our object along the `provider_game_id`. I wrote this function do do just that:

```
from sqlalchemy import func

def n_dups(session, cls, attr):
    return session.query(getattr(cls,attr)).group_by(getattr(cls,attr)).\
            having(func.count(getattr(cls,attr)) > 1).count()
```

Running this, we'll use `n_dups(Game, 'provider_game_id')` and likely see something more than zero. All this tells us, however, is how many dups we have along that attribute. We now need to iterate though each duplicated `provider_game_id` and collect all the objects with said `provider_game_id`. Getting the duplicated `provider_game_ids` is similar to above:

```
def get_duplicated_attrs(session, cls, attr):
    return session.query(getattr(cls,attr)).group_by(getattr(cls,attr)).\
            having(func.count(getattr(cls,attr)) > 1).all()
```

So now we can get the duplicated objects:

```
def get_duplicated_objs(session, cls, attr, attr_value, order_by_attr):
    return session.query(cls).filter(getattr(cls,attr) == attr_value)).\
            order_by(order_by_attr).all()
```

The `order_by_attr` is going to come in handy in the next decision when we decide which duplicated objects get the axe.


##Eliminating Duplicate Entries

While there are a few caveats explained below, our alembic migration file is a good place to identify and eliminate any duplicates, for a few reasons:

1. If our database has duplicates on a row we are asking it to add a unique constraint to, we will get an `IntegrityError`, so we are required to do this before the command in the migration that adds the constraint is applied. Adding it here means that we always know it will be run before we try to migrate.
2. I generally don't like to clutter my applications with scripts that are (ideally) only run once, however I also do not want to run something like this in a REPL because you then loose the history of what was run. Adding it here means that we'll not only retain the history, but the exact point in which it was run.
3. It's already built into my build process (which is just a nice perk for me, but running `alembic` in your built process helps you to never forget running your migrations.)

When we delete the duplicate entries in our database, we have to decide on a rule for which one's to delete, and which *one* to keep. (You could also delete all, and then recreate them with your new protections against creating duplicates.) I decided to keep the oldest entry (not for any particularly good reason, except that I had originally created my objects with `created_at` attributes. Our example doesn't have these, so I'll use `id` which is effectively the same thing assuming the `id` is auto incremented.) Inside my alembic migration file, I added the following function

```
from sqlalchemy import func

def remove_duplicates(session, cls, attr):
    duplicates = session.query(getattr(cls,attr)).group_by(getattr(cls,attr)).
                  having(func.count(getattr(cls, attr)) > 1).all()
    n_dups = len(duplicates)
    print '{}.{}: {} duplicates found'.format(cls.__name__, attr, n_dups)
    for duplicate in duplicates:
        objs = session.query(cls).
                filter(getattr(cls,attr) == getattr(duplicate, attr)).
                order_by('id').all()
        map(session.delete, objs[1:])
    session.commit()
    print '{}.{}: {} duplicates removed'.format(cls.__name__, attr, n_dups)
```

Before we can call this function, however, there are a few caveats (which I just ran into the hard way.) First, we will need to import the `db` object and the `Game` object. Typically in Python, we only import things at the top of the file, but in order for things like `alembic history` to work correctly, we need to import these within the `upgrade()` function. That way, they will only be loaded with a migration is being run, and not when the migration file is inspected for things like the version number by other tools.

Second, if you are doing a "dry run" `alembic upgrade head` (i.e. from a newly created DB with no schema), alembic works through all the migration files and issues one SQL statement at the end of the process. This is a problem if you attempt to query on the `Game` object, who's table doesn't exist yet. We can safely assume, however, that if the table doesn't exist yet, it doesn't have any duplicates. Luckily, SQLAlchemy has an `Inspector` object that allows reflection into the existing tables from and engine, and using

```
inspector = Inspector.from_engine(db.engine)
existing_tables = inspector.get_table_names()
```
will do the the trick. Now, within the `upgrade()` function we call our `remove_duplicates` function for the objects and their attributes with duplicates like so:

```
from sqlalchemy.engine.reflection import Inspector

def upgrade():
    from app import db
    from app.models import Game

    inspector = Inspector.from_engine(db.engine)
    existing_tables = inspector.get_table_names()

    if Game.__tablename__ in existing_tables:
        remove_duplicates(db.session, Game, 'provider_game_id')
    op.create_unique_constraint(None,
                                "games",
                                ["provider_game_id"])
```

and our `downgrade` function stays the same as above:

```
def downgrade():
    op.drop_contraint("provider_game_id",
                      "games",
                       "unique")
```

(Note: the import statements that happen outside of the functions can just be placed at the top of the migration file. They shouldn't cause any conflicts.)

Woo! That's it. There are certainly a few *hacks* in here, so as usual, throw some feedback in the comments.
