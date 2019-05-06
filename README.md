```
git clone https://github.com/recruit-tech/casval
git remote add rem git@github.com:recruit-tech/casval-rem.git
git remote add ui git@github.com:recruit-tech/casval-ui.git
git remote add admin-ui git@github.com:recruit-tech/casval-admin-ui.git
```

```
cd rem
terraform init
terraform apply -auto-approve
pipenv run config
pipenv run freeze
pipenv run deploy
```

```
cd ui
npm ci
npm run build
gcloud -q app deploy
```

```
cd admin-ui
npm ci
npm run build
gcloud -q app deploy
```

```
gcloud -q app deploy dispatch.yaml
gcloud -q app deploy cron.yaml
```
