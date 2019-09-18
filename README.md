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

## Configurations

| Variable Name | Default Value | Description | Note |
| ------------- | ------------- | ----------- | ---- |
| ADMIN_PASSWORD | admin-password | Password for entering CASVAL ORIGIN | <li>Need to set in `app.yaml` for GCP environment</li> |
| CONFIG\_ENV\_FILE\_PATH | config.env | Relative file path of configuration file from the application root directory of CASVAL REM | <li>GCP environment only</li> <li>Need to set in `app.yaml`</li> |
| DB_ENDPOINT | 127.0.0.1 | MySQL server endpoint | <li>Local environment only</li> |
| DB_PORT | 3306 | MySQL server port | <li>Local environment only</li> |
| DB\_INSTANCE\_NAME | - | Google Cloud SQL instance name | <li>GCP environment only</li> <li>Load from terraform state</li> |
| DB_NAME | casval | MySQL database name | <li>Load from terraform state in GCP environment</li> |
| DB_USER | root | MySQL user account name | <li>Load from terraform state in GCP environment</li> |
| DB_PASSWORD | Passw0rd! | MySQL database password | <li>Load from terraform state in GCP environment</li> |
| GCP\_PROJECT\_NAME | - | GCP project name that deploys CASVAL REM | <li>GCP environment only</li> <li>Load from terraform state</li> |
| GCP\_REPORT\_STORAGE\_NAME | - | GCS bucket name that stores raw scan report file | <li>GCP environment only</li> <li>Load from terraform state</li> |
| KUBERNETES\_MASTER\_SERVER | - | Kubernetes master endpoint of the REM's cluster | <li>GCP environment only</li> <li>Load from terraform state</li> |
| KUBERNETES_NAMESPACE | default | Kuberenates namespace name | <li>GCP environment only</li> <li>Need to set in `app.yaml`</li> |
| OPENVAS\_OMP\_ENDPOINT | 127.0.0.1 | OpenVAS OMP server endpoint | <li>Local environment only</li> |
| OPENVAS\_OMP\_PORT | 9390 | OpenVAS OMP server port | <li>Need to set in `app.yaml` for GCP environment</li> |
| OPENVAS\_OMP\_USERNAME | admin | OpenVAS server login user name | <li>Need to set in `app.yaml` for GCP environment</li> |
| OPENVAS\_OMP\_PASSWORD | admin | OpenVAS server login password | <li>Need to set in `app.yaml` for GCP environment</li> |
| OPENVAS\_SCAN\_ENDPOINT | 127.0.0.1 | OpenVAS scan source endpoint | <li>Load from terraform state in GCP environment</li> |
| OPENVAS\_ALIVE\_TEST | Consider Alive | OpenVAS option specifies the method to check if a target is reachable | <li>Need to set in `app.yaml` for GCP environment</li> |
| OPENVAS_PROFILE | Full and very deep | OpenVAS scan configuration profile | <li>Need to set in `app.yaml` for GCP environment</li> |
| PASSWORD_SALT | password-salt | Salt string for password hash |  <li>Need to set in `app.yaml` for GCP environment</li> |
| CORS\_PERMITTED\_ORIGINS | * | Origins that allow to send cross origin requests, that value is set to `Access-Control-Allow-Origin` response header | <li>Need to set in `app.yaml` for GCP environment</li> |
| PERMITTED\_SOURCE\_IP\_RANGES | - | Comma separated source IP address ranges that allows to call restricted APIs | <li>Need to set in `app.yaml` for GCP environment</li> |
| SCAN\_MAX\_PARALLEL\_SESSION | 1 | Max parallel scan session count | <li>Need to set in `app.yaml` for GCP environment</li> |
| JWT\_SECRET\_KEY | super-secret | Secret key used for signing JWT credentials | <li>Need to set in `app.yaml` for GCP environment</li> |

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