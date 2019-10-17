---
layout: post
title: Fighting fraud using partially blind signatures
date: 2019-10-17 09:45
comments: false
---

It's not often that I'm able to share my work publically, so it's personally quite exciting to have worked on this project and to see it published on the Facebook engineering blog: [Fighting fraud using partially blind signatures](https://engineering.fb.com/security/partially-blind-signatures/).

Historically, the primary tool for fighting fraud in ad tech was a uniquely identifiable token. If a token you receive back matches a token you generated in the past, you can be almost certain it wasn't faked. However, these tokens enable individual tracking, and, other than blind trust, there is no way to prove that they aren't used that way.

These tokens aren't the only solution, though. Through applied cryptography and some critical insights, we designed a protocol which removes this tracking ability, but maintains the ability to detect a fake token. For my fellow software engineers, we have a prototype up on [GitHub as well.](https://github.com/siyengar/private-fraud-prevention)

This is just the tip of the iceberg when it comes to inventing new privacy preserving technology, and applying it to the digital ad ecosystem, and I'm humbled and proud to be a part of it.
