# MySQL operator

Простой учебный оператор на Kopf для ресурса `MySQL` (`mysqls.otus.homework/v1`).

## Сборка

```bash
docker build -t harbor.mvl.test/library/myapp-mysql-operator:0.1.0 . --no-cache
```

## Push в репо

```bash
docker push harbor.mvl.test/library/myapp-mysql-operator:0.1.0
```

## Установка

```bash
kubectl apply -f mysql-operator/manifests/crd.yaml
kubectl apply -f mysql-operator/manifests/rbac.yaml
kubectl apply -f mysql-operator/manifests/deployment.yaml
kubectl apply -f mysql-operator/manifests/mysql.yaml
```

При создании или изменении `MySQL` оператор приводит к нужному состоянию `Deployment`, `Service` типа `ClusterIP`, `Secret`, `PersistentVolume` и `PersistentVolumeClaim`.
Пароль хранится в `Secret` и подключается в Pod через `valueFrom.secretKeyRef`.

Для namespaced-ресурсов (`Deployment`, `Service`, `Secret`, `PVC`) задаются `ownerReferences` на объект `MySQL`.
Для cluster-scoped `PV` `ownerReferences` не задаётся: PV удаляется явно в delete handler оператора.

`Deployment` с одной репликой и ручной `hostPath` PV используется как простой учебный вариант. Для production MySQL обычно лучше использовать `StatefulSet`, headless `Service` и dynamic provisioning через `StorageClass`.

## Ограничение PVC

Оператор создаёт статический `PV` на `hostPath` и привязанный к нему `PVC`. Значение `spec.storage_size` применяется только при первичном создании этих ресурсов.

Если изменить `storage_size` в уже существующем объекте `MySQL`, оператор не изменит размер существующего `PVC`: для статически созданного `PVC` с заранее заданным `volumeName` расширение тома не поддерживается этим учебным оператором. Автоматический resize обычно работает только для dynamically provisioned `PVC`, если `StorageClass` поддерживает `allowVolumeExpansion` и CSI-драйвер умеет расширять тома.

Чтобы применить новый размер в рамках текущей реализации, нужно пересоздать объект `MySQL` вместе с его `PVC`/`PV`. В production-сценариях лучше использовать dynamic provisioning через `StorageClass`, `StatefulSet` и отдельную логику безопасного resize.
