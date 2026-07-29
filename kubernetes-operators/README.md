# Выполнено ДЗ № 7

 - [x] Основное ДЗ
 - [x] Задание со *
 - [x] Задание со **

## В процессе сделано:

- Создан манифест [`crd-mysql.yaml`](kubernetes-operators/crd-mysql.yaml) — CustomResourceDefinition `mysqls.otus.homework` для namespaced-ресурса `MySQL` группы `otus.homework`, версии `v1`, с обязательными строковыми полями `image`, `database`, `password`, `storage_size`
- Создан манифест [`mysql-rbac.yaml`](kubernetes-operators/mysql-rbac.yaml) — ServiceAccount `mysql-operator`, ClusterRole и ClusterRoleBinding для работы оператора с Kubernetes API
- **Задание со \***: в [`mysql-rbac.yaml`](kubernetes-operators/mysql-rbac.yaml) описан минимальный набор прав для доступа к CRD `mysqls.otus.homework`, `Deployment`, `Service`, `PV` и `PVC` без выдачи кластерных прав `cluster-admin`
- Создан манифест [`mysql-operator.yaml`](kubernetes-operators/mysql-operator.yaml) — Deployment оператора с `serviceAccountName: mysql-operator` и образом `roflmaoinmysoul/mysql-operator:1.0.0`
- Создан манифест [`mysql-instance.yaml`](kubernetes-operators/mysql-instance.yaml) — валидный кастомный ресурс `kind: MySQL`, на основании которого оператор создаёт MySQL Deployment, Service, PV и PVC
- Создан манифест [`storageClass.yaml`](kubernetes-operators/storageClass.yaml) — StorageClass `standard` на базе `rancher.io/local-path` с `reclaimPolicy: Retain`; он нужен для готового образа `roflmaoinmysoul/mysql-operator:1.0.0`, потому что в операторе захардкожено имя StorageClass/PV `standard`
- **Задание со \*\***: реализован собственный учебный оператор в каталоге [`mysql-operator`](kubernetes-operators/mysql-operator/):
  - код оператора находится в [`operator.py`](kubernetes-operators/mysql-operator/app/operator.py)
  - оператор написан на Kopf и Python Kubernetes Client
  - при создании, обновлении или возобновлении объекта `MySQL` создаёт/актуализирует `Deployment`, `Service` типа `ClusterIP`, `Secret`, `PersistentVolume` и `PersistentVolumeClaim`
  - при удалении объекта `MySQL` удаляет созданные для него `Deployment`, `Service`, `Secret`, `PVC` и `PV`
  - пароль базы хранится в Kubernetes Secret и передаётся в контейнер через `secretKeyRef`
  - для namespaced-ресурсов используются `ownerReferences`, а cluster-scoped `PV` удаляется явно в delete handler

## Как запустить проект:

### 1. Запуск оператора из готового образа

1. Примените манифесты в порядке:

   ```bash
   kubectl apply -f kubernetes-operators/storageClass.yaml
   kubectl apply -f kubernetes-operators/crd-mysql.yaml
   kubectl apply -f kubernetes-operators/mysql-rbac.yaml
   kubectl apply -f kubernetes-operators/mysql-operator.yaml
   kubectl apply -f kubernetes-operators/mysql-instance.yaml
   ```

2. После применения кастомного ресурса `MySQL` оператор должен создать связанные ресурсы для MySQL:
   - `Deployment` с образом из `spec.image`
   - `Service` типа `ClusterIP`
   - `PersistentVolume`
   - `PersistentVolumeClaim`

### 2. Запуск собственного оператора из задания со **

1. Соберите Docker-образ оператора:

   ```bash
   docker build -t harbor.mvl.test/library/myapp-mysql-operator:0.1.0 kubernetes-operators/mysql-operator/ --no-cache
   ```

2. Опубликуйте образ в registry:

   ```bash
   docker push harbor.mvl.test/library/myapp-mysql-operator:0.1.0
   ```

3. Примените манифесты собственного оператора:

   ```bash
   kubectl apply -f kubernetes-operators/mysql-operator/manifests/crd.yaml
   kubectl apply -f kubernetes-operators/mysql-operator/manifests/rbac.yaml
   kubectl apply -f kubernetes-operators/mysql-operator/manifests/operator.yaml
   kubectl apply -f kubernetes-operators/mysql-operator/manifests/mysql-app.yaml
   ```

## Как проверить работоспособность:

- Проверить, что CRD создан:

  ```bash
  kubectl get crd mysqls.otus.homework
  kubectl explain mysql.spec
  ```

- Проверить, что оператор запущен:

  ```bash
  kubectl get deploy,pods -n default -l app=mysql-operator
  kubectl logs -n default deploy/mysql-operator
  ```

- Проверить, что кастомный ресурс создан:

  ```bash
  kubectl get mysqls -n default
  kubectl describe mysql mysql-instance -n default
  ```

- Проверить, что оператор создал ресурсы для MySQL:

  ```bash
  kubectl get deploy,svc,pvc,pv -n default
  kubectl get pods -n default -l app=mysql
  ```

- Проверить, что Deployment использует образ, указанный в `spec.image` кастомного ресурса:

  ```bash
  kubectl get deploy mysql-instance -n default -o jsonpath='{.spec.template.spec.containers[0].image}'
  ```

- Проверить права service account из задания со *:

  ```bash
  kubectl auth can-i get mysqls.otus.homework --as=system:serviceaccount:default:mysql-operator
  kubectl auth can-i create deployments.apps --as=system:serviceaccount:default:mysql-operator
  kubectl auth can-i create services --as=system:serviceaccount:default:mysql-operator
  kubectl auth can-i create persistentvolumes --as=system:serviceaccount:default:mysql-operator
  kubectl auth can-i create persistentvolumeclaims --as=system:serviceaccount:default:mysql-operator
  ```

- Проверить удаление ресурсов при удалении кастомного объекта:

  ```bash
  kubectl delete -f kubernetes-operators/mysql-instance.yaml
  kubectl get deploy,svc,pvc,pv -n default
  ```

  После удаления объекта `MySQL` связанные `Deployment`, `Service`, `PV` и `PVC` должны быть удалены оператором.

## Структура собственного оператора:

```text
kubernetes-operators/mysql-operator/
├── Dockerfile                  # Сборка образа оператора
├── pyproject.toml              # Python-зависимости: kopf и kubernetes client
├── README.md                   # Краткое описание собственного оператора
├── app/
│   └── operator.py             # Логика reconcile/delete для ресурса MySQL
└── manifests/
    ├── crd.yaml                # CRD mysqls.otus.homework/v1
    ├── mysql-app.yaml          # Пример кастомного ресурса MySQL
    ├── operator.yaml           # Deployment собственного оператора
    └── rbac.yaml               # Минимальные RBAC-права оператора
```

## PR checklist:

 - [x] Выставлен label с темой домашнего задания
