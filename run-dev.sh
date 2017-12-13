#!/usr/bin/env sh

# for development use only!
# in prod, modify Caddyfile to your needs and run caddy as a service
caddy & ./app.py
