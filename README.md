# Выполнено ДЗ № 6

- [x] Основное ДЗ
- [x] Задание со *

## В процессе сделано:

### Helm-чарт homework-app

- Создан Helm-чарт [`homework-app`](kubernetes-templating/homework-app/), позволяющий деплоить приложение, разработанное в ДЗ 1–5
- Все основные параметры вынесены в [`values.yaml`](kubernetes-templating/homework-app/values.yaml) и конфигурируются через шаблоны:
  - Имена объектов, имена контейнеров, образы, хосты, порты, количество реплик — заданы как переменные в шаблонах
  - Репозиторий (`image.repository`) и тег (`image.tag`) образа разделены на два независимых параметра
  - Пробы (startup, readiness, liveness) включаются/отключаются через параметры `probes.*.enabled` в values.yaml
- В [`_helpers.tpl`](kubernetes-templating/homework-app/templates/_helpers.tpl) реализованы best-practice именования объектов через `homework-app.fullname`, `homework-app.name` и другие helper-функции
- В [`NOTES.txt`](kubernetes-templating/homework-app/templates/NOTES.txt) выводится сообщение после установки релиза с адресом для обращения к сервису (`http://homework.otus/`)
- Добавлена сервис-зависимость — [valkey](https://valkey.io/) (community-чарт `valkey:0.10.0`), включаемая через `valkey.enabled: true` в values.yaml
- Чарт включает шаблоны: Deployment, Service, Gateway, HTTPRoute, HPA, PVC, ConfigMap, ServiceAccount, ClusterRole, ClusterRoleBinding

### Установка Kafka из Bitnami Helm-чарта

- **Kafka в namespace `prod`** (файл [`kafka-values-prod.yaml`](kubernetes-templating/kafka-values-prod.yaml)):
  - 3 controller + 3 broker (суммарно 5 брокеров, как того требует controller-only архитектура Bitnami-чарта)
  - Версия Kafka: `3.5.2` (образ `bitnamilegacy/kafka:3.5.2`)
  - Протокол `SASL_PLAINTEXT` для клиентских и межброкерных взаимодействий
  - Включён SASL с механизмом `PLAIN`, заданы пользователи и пароли для inter-broker, controller и client

- **Kafka в namespace `dev`** (файл [`kafka-values-dev.yaml`](kubernetes-templating/kafka-values-dev.yaml)):
  - 1 controller + 1 broker
  - Последняя доступная версия Kafka (образ `bitnamilegacy/kafka:latest`)
  - Протокол `PLAINTEXT` для всех listener'ов, авторизация отключена

### Helmfile

- Создан [`helmfile.yaml`](kubernetes-templating/helmfile.yaml), описывающий оба сценария установки Kafka:
  - Релиз `kafka-prod` в namespace `prod` с values из `kafka-values-prod.yaml`, версия чарта `25.3.5`
  - Релиз `kafka-dev` в namespace `dev` с values из `kafka-values-dev.yaml`
  - Настроен репозиторий `bitnami` (https://charts.bitnami.com/bitnami)
  - Общие настройки: `wait: true`, `timeout: 600`, `atomic: true`, `cleanupOnFail: true`

## Как запустить проект

### 1. Установка приложения через Helm-чарт

```bash
helm upgrade --install homework-app kubernetes-templating/homework-app/ --dependency-update --create-namespace --namespace homework
```

### 2. Установка Kafka через Helmfile

```bash
# Установка helmfile (если ещё не установлен):
# https://github.com/helmfile/helmfile#installation

# Применение всех релизов (prod + dev):
helmfile -f kubernetes-templating/helmfile.yaml apply

# Или установка конкретного релиза:
helmfile -f kubernetes-templating/helmfile.yaml -l name=kafka-prod apply
helmfile -f kubernetes-templating/helmfile.yaml -l name=kafka-dev apply
```

## Как проверить работоспособность:

### Проверка Helm-чарта homework-app

- Проверить статус релиза:
  ```bash
  helm list -n homework
  helm status homework-app -n homework
  ```

- Проверить, что все ресурсы созданы:
  ```bash
  kubectl get all,gateway,httproute,pvc,cm,sa,clusterrole,clusterrolebinding -n homework
  ```

- Проверить доступность приложения (после настройки DNS или /etc/hosts):
  ```bash
  curl http://homework.otus/
  curl http://homework.otus/metrics.html
  ```

- Проверить работу проб:
  ```bash
  kubectl describe pod -n homework -l app.kubernetes.io/instance=homework-app
  ```

- Проверить зависимость valkey:
  ```bash
  kubectl get pods -n homework -l app.kubernetes.io/name=valkey
  ```

### Проверка Kafka

- Проверить статус релизов:
  ```bash
  helm list -n prod
  helm list -n dev
  ```

- Проверить поды Kafka:
  ```bash
  kubectl get pods -n prod
  kubectl get pods -n dev
  ```

- Проверить, что в prod используется SASL_PLAINTEXT:
  ```bash
  kubectl get cm -n prod kafka-prod-config -o yaml | grep -A5 listener
  ```

- Проверить, что в dev используется PLAINTEXT:
  ```bash
  kubectl get cm -n dev kafka-dev-config -o yaml | grep -A5 listener
  ```

- Проверить версию Kafka в prod:
  ```bash
  kubectl get pods -n prod -l app.kubernetes.io/name=kafka -o jsonpath='{.items[0].spec.containers[0].image}'
  ```

## Структура чарта homework-app:

```
kubernetes-templating/homework-app/
├── Chart.yaml              # Метаданные чарта, зависимости (valkey)
├── Chart.lock              # Lock-файл зависимостей
├── values.yaml             # Конфигурация по умолчанию
├── .helmignore             # Игнорируемые файлы при упаковке
└── templates/
    ├── _helpers.tpl        # Helper-функции для именования
    ├── NOTES.txt           # Сообщение после установки
    ├── deployment.yaml     # Deployment с пробами, init-контейнером, PVC, ConfigMap
    ├── service.yaml        # Service типа ClusterIP
    ├── gateway.yaml        # Gateway API Gateway
    ├── httproute.yaml      # HTTPRoute с rewrite-правилами
    ├── hpa.yaml            # HorizontalPodAutoscaler
    ├── pvc.yaml            # PersistentVolumeClaim
    ├── cm.yaml             # ConfigMap (nginx.conf + init-скрипт)
    ├── serviceaccount.yaml # ServiceAccount
    ├── clusterRole.yaml    # ClusterRole для доступа к /metrics
    └── clusterRoleBinding.yaml  # ClusterRoleBinding
```

## PR checklist:

 - [x] Выставлен label с темой домашнего задания
