---
layout: post
title: Unpythonic Python
date: 2014-04-09 03:09:54 -0400
comments: true
---

##FizzBuzz

When I applied to [Hacker School](http://www.hackerschool.com), one of the application question was FizzBuzz:

> Write a program that prints out the numbers 1 to 100 (inclusive). If the number is divisible by 3, print *Fizz* instead of the number. If it's divisible by 5, print *Buzz*. If it's divisible by both 3 and 5, print *FizzBuzz*. You can use any language.

(Hacker School has since updated the question slightly, likely to make it more difficult to solve via Google. I've left out the updated version intentionally to minimize my effect on Googlability.)

This problem is fairly straight forward, and a good bite size problem to use as an example for different languages and programming styles; it's similar to "Hello, World!" and "Fibonacci".

## Some Unpythonic Python

I looked at this problem today while showing a friend the Hacker School application, and started thinking about the many ways to tackle the problem just in Python alone. Python, specifically with [PEP 8](http://legacy.python.org/dev/peps/pep-0008/), lays out the ideal way to write *Pythonic Python*. But Python doesn't enforce *Pythonic Python*, so I started thinking, what other kinds of Python could I write this in.

**Warning: Very Unpythonic Python ahead.** However, all code should work (with Python 2.7.5).

Feel free to [tweet me](https://twitter.com/taubeneck) or comment with suggested fixes, or new additions.
<!-- more -->

### Pythonic Python

``` python
def fizzbuzz(number):
    if number % 3 == 0 and number % 5 == 0:
        return 'FizzBuzz'
    elif number % 3 == 0:
        return 'Fizz'
    elif number % 5 == 0:
        return 'Buzz'
    else:
        return number

for number in range(1, 101):
    print fizzbuzz(number)
```

### Lispy Python

``` python
fizzbuzz = lambda n: 'FizzBuzz' if n % 3 == 0 and n % 5 == 0 else None
fizz = lambda n: 'Fizz' if n % 3 == 0 else None
buzz = lambda n: 'Buzz' if n % 5 == 0 else None
fizz_andor_maybenot_buzz = lambda n: fizzbuzz(n) or fizz(n) or buzz(n) or str(n)

print reduce(lambda m,n: m+'\n'+n, map(fizz_andor_maybenot_buzz, range(1, 101)))
```

### Javacious Python

``` python
import sys

class Value(object):
    def __init__(self,value):
        self.setValue(value)

    def setValue(self,value):
        self.value = value

    def getValue(self):
        return self.value

    def toString(self):
        return self.getValue().__str__()

class FizzBuzz(object):
    def __init__(self, n):
        if n % 15 == 0:
            value = 'FizzBuzz';
        elif n % 3 == 0:
            value = 'Fizz';
        elif n % 5 == 0:
            value = 'Buzz';
        else:
            value = str(n);
        self.setValue(value);

    def setValue(self,value):
        self.value = Value(value);

    def getValue(self):
        return self.value;

class FizzBuzzRunner(object):
    def __init__(self, n):
        self.setN(n)

    def setN(self, n):
        self.n = n

    def run(self):
        for i in range(1,self.n):
            sys.stdout.write(FizzBuzz(i).getValue().toString()+'\n');

if __name__ == '__main__':
    n = 101;
    FizzBuzzRunner(n).run()
```

###C-ly Python

``` python
def main():
    i = 0;
    value = '';

    while i < 100:
        i += 1
        if i % 15 == 0:
            value = 'FizzBuzz';
        elif i % 3 == 0:
            value = 'Fizz';
        elif i % 5 == 0:
            value = 'Buzz';
        else:
            value = str(i);
        print value;

    return 0;

main();
```

### Clojurly Python

``` python
def fizzbuzz(n):
    return 'FizzBuzz' if n % 3 == 0 and n % 5 == 0 else None

def fizz(n):
    return 'Fizz' if n % 3 == 0 else None

def buzz(n):
    return 'Buzz' if n % 5 == 0 else None

def fizz_andor_maybenot_buzz(n):
    print fizzbuzz(n) or fizz(n) or buzz(n) or str(n)

map(fizz_andor_maybenot_buzz, xrange(1, 101))
```
