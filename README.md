<img src="ui/src/assets/logo-grey.svg" width="300">

A <u>cas</u>ual <u>v</u>ulnerability <u>a</u>n<u>al</u>yzer, that makes platform security audit more casual.

![screenshot](https://user-images.githubusercontent.com/3012367/57343095-df6f2f80-717c-11e9-8e18-f7b6b7276836.gif)

## How to Deploy

Get all the stuff at first.

```
git clone https://github.com/recruit-tech/casval
```

### Local development environment

In `casval/rem`, run the following commands.

```
docker run -e MYSQL_DATABASE=casval -e MYSQL_ROOT_PASSWORD=Passw0rd! -d -p 3306:3306 mysql:5.7 --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
docker run -e PUBLIC_HOSTNAME=localhost -d -p 443:443 -p 9390:9390 mikesplain/openvas:9
pipenv install -d
pipenv run server
```

Also, run the following commands for invoking cron-like periodic task.

```
pipenv run cron
```

In `casval/admin-ui`, run the following commands.

```
npm ci
npm run serve
```

In `casval/ui`, run the following commands.

```
npm ci
npm run serve
```

Done, visit `http://localhost:8100/` on your browser. The default administrator password is `admin-password`.

### Production environment (on GCP)

In `casval/rem`, you need to set your GCP project name to `example.tf`.

```
variable "project" {
  default = "{YOUR_PROJECT_NAME}"
}
```

Run the following commands for building cloud infrastructure on your GCP project.

```
terraform init
terraform apply -auto-approve
```

Also, run the following commands for deploying the API server to Google App Engine.

```
pipenv install
pipenv run config
pipenv run freeze
pipenv run deploy
```

In `casval/admin-ui`, run the following commands for deploying administrator front-end user interface.

```
npm ci
npm run build
gcloud -q app deploy
```

In `casval/ui`, run the following commands for deploying end-user's front-end user interface.

```
npm ci
npm run build
gcloud -q app deploy
```

Back to `casval`, run the following commands for setup URL routers and cron scheduled tasks.

```
gcloud -q app deploy dispatch.yaml
gcloud -q app deploy cron.yaml
```

Done, visit the GAE endpoint on your browser. The default administrator password is `admin-password`.

## For Developers

When you reflect upstream changes to your environment, you need to set following remote repositories at `casval/`.

```
git remote add rem git@github.com:recruit-tech/casval-rem.git
git remote add ui git@github.com:recruit-tech/casval-ui.git
git remote add admin-ui git@github.com:recruit-tech/casval-admin-ui.git
```