# CASVAL REM (CASVAL Remote Execution Module)


## Deploy

### Production (on Google App Engine)

```
cd example/gke
terraform init
terraform apply
pipenv run config

# Move config.env to casval/rem
pipenv run freeze
pipenv run deploy
```

### Local Development

```
docker run -e MYSQL_DATABASE=casval -e MYSQL_ROOT_PASSWORD=Passw0rd! -d -p 3306:3306 mysql:5.7 --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
docker run -e PUBLIC_HOSTNAME=localhost -d -p 443:443 -p 9390:9390 mikesplain/openvas:9
pipenv shell
pipenv install -d
pipenv run server
```


## For Developers

### Format Code

```
pipenv run format
```

### Update openvas_lib

CASVAL internally uses [openvas_lib](https://github.com/golismero/openvas_lib) for communicating with remote OpenVAS server(s) through OMP protocol. This library is useful but it doesn't support Python 3.x, so we convert their code with [2to3](https://docs.python.org/3/library/2to3.html) to make them Python 3.x compatible and include them into the root `openvas_lib` directory. If you'd like to update the library with upstream changes, try to do follows. Note that our confirmed revision is the commit [bd650702](https://github.com/golismero/openvas_lib/commit/bd65070246e674e68a4689d929f491f76d32635b) only.

```
export CASVAL_ROOT = {YOUR CASVAL REM ROOT DIR}
cd /tmp
git clone https://github.com/golismero/openvas_lib
cd openvas_lib
2to3 -w .
cp openvas_lib/* $CASVAL_ROOT/openvas_lib
```