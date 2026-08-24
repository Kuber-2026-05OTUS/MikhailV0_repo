# Выполнено ДЗ № 12

- [x] Основное ДЗ

## В процессе сделано:

- Создан S3 bucket в Yandex Cloud Object Storage по инструкции: https://yandex.cloud/ru/docs/storage/quickstart
- Создан ServiceAccount, выданы права на доступ к Object Storage, сгенерированы статические ключи доступа.
- Установлен CSI driver [`yandex-cloud/k8s-csi-s3`](https://github.com/yandex-cloud/k8s-csi-s3) через Helm.
- Secret `csi-s3-secret` и StorageClass `csi-s3` создаются chart'ом автоматически; ключи передаются из переменных окружения.
- Добавлен [`pvc.yaml`](kubernetes-csi/pvc.yaml) — PVC `csi-s3-pvc` со StorageClass `csi-s3`.
- Добавлен [`deployment.yaml`](kubernetes-csi/deployment.yaml) — Deployment `csi-s3-writer`, который монтирует PVC в `/mnt/s3-data` и пишет туда файлы.

## Как запустить проект:

Задать ключи доступа:

```bash
export OBJECT_STORAGE_ACCESS_KEY_ID="real-access-key"
export OBJECT_STORAGE_SECRET_ACCESS_KEY="real-secret-key"
```

Установить CSI driver:

```bash
helm repo add yandex-s3 https://yandex-cloud.github.io/k8s-csi-s3/charts
helm repo update

helm upgrade --install csi-s3 yandex-s3/csi-s3 \
  --namespace kube-system \
  --set secret.accessKey="${OBJECT_STORAGE_ACCESS_KEY_ID}" \
  --set secret.secretKey="${OBJECT_STORAGE_SECRET_ACCESS_KEY}"
```

Проверить, что chart создаёт Secret и StorageClass:

```bash
kubectl get secret csi-s3-secret -n kube-system
kubectl get storageclass csi-s3
```

Применить манифесты:

```bash
kubectl apply -f kubernetes-csi/pvc.yaml
kubectl apply -f kubernetes-csi/deployment.yaml
```

## Как проверить работоспособность:

Проверить PVC и pod:

```bash
kubectl get pvc csi-s3-pvc -n default
kubectl get pods -n default -l app=csi-s3-writer
```

Проверить запись в примонтированную директорию:

```bash
kubectl exec -n default deployment/csi-s3-writer -- ls -la /mnt/s3-data
kubectl exec -n default deployment/csi-s3-writer -- sh -c 'tail -n 5 /mnt/s3-data/writer-*.log'
```

Проверить `ReadWriteMany`:

```bash
kubectl scale deployment/csi-s3-writer -n default --replicas=3
kubectl get pods -n default -l app=csi-s3-writer
```

В Object Storage должны появиться файлы:

- `writer-<pod-name>.log`
- `last-write-<pod-name>.txt`

Скриншот проверки через GUI:

![Object Storage bucket](kubernetes-csi/screenshots/backet-gui.png)

Проверка через CLI:

```bash
# настройка awscli: https://yandex.cloud/ru/docs/storage/quickstart/quickstart-aws-cli
aws s3 ls s3://<bucket-name>/
```

## Приложенные манифесты для проверки ДЗ:

- [`pvc.yaml`](kubernetes-csi/pvc.yaml)
- [`deployment.yaml`](kubernetes-csi/deployment.yaml)
- [`backet-gui.png`](kubernetes-csi/screenshots/backet-gui.png)

## PR checklist:

- [x] Выставлен label с темой домашнего задания
