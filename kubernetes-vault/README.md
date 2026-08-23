# Выполнено ДЗ № 11

- [x] Основное ДЗ

## В процессе сделано

- Установлен Consul в HA-режиме на 3 реплики как backend-хранилище Vault.
- Установлен Vault в HA-режиме на 3 реплики с Consul storage backend.
- Выполнены init и unseal Vault.
- В Vault создан KV mount `otus`, секрет `otus/cred` и policy `otus-policy`.
- Настроена Kubernetes-аутентификация Vault через ServiceAccount `vault-auth`.
- Установлен External Secrets Operator.
- Созданы `SecretStore` и `ExternalSecret`, синхронизирующие секрет из Vault в Kubernetes Secret `otus-cred`.

## Как запустить проект

Все команды выполняются из директории `kubernetes-vault`.

### 1. Скачать Helm-чарты

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo add external-secrets https://charts.external-secrets.io
helm repo update
```

```bash
helm pull hashicorp/consul --version 2.0.3 --untar
helm pull hashicorp/vault --version 0.34.1 --untar
helm pull external-secrets/external-secrets --version 2.9.0 --untar
```

### 2. Установить Consul

Values: `custom-сonsul-2.0.3.yaml`.

```bash
helm upgrade --install consul ./consul \
  --namespace consul --create-namespace \
  --values ./custom-сonsul-2.0.3.yaml
```

Проверка:

```bash
kubectl -n consul get pods
```

### 3. Установить Vault

Values: `custom-vault-0.34.1.yaml`.

```bash
helm upgrade --install vault ./vault \
  --namespace vault --create-namespace \
  --values ./custom-vault-0.34.1.yaml
```

Проверка:

```bash
kubectl -n vault get pods
kubectl -n vault exec vault-0 -- vault status
```

### 4. Инициализировать и распечатать Vault

```bash
kubectl -n vault exec vault-0 -- vault operator init -key-shares=3 -key-threshold=2
```

Сохранить `Initial Root Token` и минимум 2 unseal key. Далее распечатать все pod'ы Vault:

```bash
read -rs UNSEAL_KEY_1
read -rs UNSEAL_KEY_3
```

Распечатать только sealed pod'ы:

```bash
for pod in $(kubectl -n vault get pods \
  -l app.kubernetes.io/name=vault,component=server,vault-sealed=true \
  -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}'); do
  for key in "$UNSEAL_KEY_1" "$UNSEAL_KEY_3"; do
    kubectl -n vault exec -i "$pod" -- vault operator unseal "$key"
  done
done
```

### 5. Подготовить Vault CLI

```bash
wget https://hashicorp-releases.yandexcloud.net/vault/2.0.4/vault_2.0.4_linux_amd64.zip
unzip vault_2.0.4_linux_amd64.zip
sudo install -m 0755 -o root -g root vault /usr/local/bin/vault
```

```bash
export VAULT_ADDR='http://vault.mvl.test'
vault login
```

### 6. Создать KV mount, секрет и policy

```bash
vault secrets enable -path=otus -version=1 kv
vault kv put -mount=otus cred username=otus password=asajkjkahs
vault policy write otus-policy ./policy.hcl
```

Проверка:

```bash
vault kv get -mount=otus cred
vault read otus/cred
```

### 7. Настроить Kubernetes auth в Vault

Манифест: `vault-auth.yaml`.

```bash
kubectl apply -f vault-auth.yaml
```

```bash
kubectl get sa vault-auth -n vault
kubectl get clusterrolebinding vault-auth-delegator
kubectl auth can-i create tokenreviews --as=system:serviceaccount:vault:vault-auth
```

```bash
vault auth enable kubernetes
vault auth list
```

Выполнять с компьютера администратора кластера:

```bash
export TOKEN_REVIEWER_JWT=$(kubectl -n vault get secret vault-auth-token \
  -o jsonpath='{.data.token}' | base64 -d)

export KUBE_CA_CERT=$(kubectl -n vault get secret vault-auth-token \
  -o jsonpath='{.data.ca\.crt}' | base64 -d)

export KUBE_HOST=$(kubectl config view --raw --minify \
  -o jsonpath='{.clusters[0].cluster.server}')
```

```bash
vault write auth/kubernetes/config \
  token_reviewer_jwt="$TOKEN_REVIEWER_JWT" \
  kubernetes_host="$KUBE_HOST" \
  kubernetes_ca_cert="$KUBE_CA_CERT"
```

```bash
vault write auth/kubernetes/role/otus \
  bound_service_account_names=vault-auth \
  bound_service_account_namespaces=vault \
  policies=otus-policy \
  ttl=24h
```

Проверка получения Vault token по JWT ServiceAccount:

```bash
export SA_JWT=$(kubectl -n vault get secret vault-auth-token \
  -o jsonpath='{.data.token}' | base64 -d)

vault write auth/kubernetes/login \
  role=otus \
  jwt="$SA_JWT"
```

### 8. Установить External Secrets Operator

Values: `custom-external-secrets-2.9.0.yaml`.

```bash
helm upgrade --install external-secrets ./external-secrets \
  --namespace vault --create-namespace \
  --values ./custom-external-secrets-2.9.0.yaml
```

Проверка:

```bash
kubectl -n vault get pods \
  -l app.kubernetes.io/instance=external-secrets
kubectl get crd | grep external-secrets.io
```

### 9. Создать SecretStore и ExternalSecret

Манифесты:

- `secretstore-vault.yaml`
- `externalsecret-otus-cred.yaml`

```bash
kubectl apply -f secretstore-vault.yaml
kubectl apply -f externalsecret-otus-cred.yaml
```

## Как проверить работоспособность

### SecretStore

```bash
kubectl -n vault get secretstore vault
kubectl -n vault describe secretstore vault
```

Ожидаемый статус:

```text
Status:
  Conditions:
    Reason:  Valid
    Status:  True
    Type:    Ready
```

### ExternalSecret

```bash
kubectl -n vault get externalsecret otus-cred
kubectl -n vault describe externalsecret otus-cred
```

Ожидаемый статус:

```text
Status:
  Conditions:
    Reason:  SecretSynced
    Status:  True
    Type:    Ready
```

### Kubernetes Secret

```bash
kubectl -n vault get secret otus-cred
```

Проверить ключи `username` и `password`:

```bash
kubectl -n vault get secret otus-cred \
  -o jsonpath='{.data.username}' | base64 -d; echo

kubectl -n vault get secret otus-cred \
  -o jsonpath='{.data.password}' | base64 -d; echo
```

Ожидаемые значения:

```text
otus
asajkjkahs
```

## PR checklist

- [x] Выставлен label с темой домашнего задания


