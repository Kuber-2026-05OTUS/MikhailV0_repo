# Выполнено ДЗ № 5

- [x] Основное ДЗ
- [x] Задание со *

## В процессе сделано

- Создан манифест [`rbac.yaml`](kubernetes-security/rbac.yaml) — ServiceAccount `monitoring` в namespace `homework`, ClusterRole `metrics-reader` с доступом `get` к endpoint `/metrics` кластера и ClusterRoleBinding `monitoring-metrics-reader`
- В манифесте [`deployment.yaml`](kubernetes-security/deployment.yaml) добавлен `serviceAccountName: monitoring`, чтобы поды Deployment `homework-web` запускались под service account `monitoring`
- В манифесте [`rbac.yaml`](kubernetes-security/rbac.yaml) создан ServiceAccount `cd` в namespace `homework` и RoleBinding `cd-admin`, выдающий ему встроенную роль `admin` в рамках namespace `homework`
- Создан файл [`kubeconfig-cd`](kubernetes-security/kubeconfig-cd) — kubeconfig для service account `cd` с namespace по умолчанию `homework`
- Сгенерирован токен для service account `cd` сроком действия 1 день и сохранён в файл [`token`](kubernetes-security/token)
- **Задание со \***: в манифесте [`deployment.yaml`](kubernetes-security/deployment.yaml) изменён init-контейнер `init-downloader`: образ `busybox:1.36` заменён на `curlimages/curl:8.8.0`, так как BusyBox `wget` не поддерживает параметр `--ca-certificate`. Во время запуска pod init-контейнер через `curl` обращается к Kubernetes API endpoint `/metrics` с использованием service account token и CA-сертификата, сохраняет ответ в файл `metrics.html`, после чего файл доступен через nginx по URL `/metrics.html`

## Как запустить проект

 1. Примените манифесты в порядке:

    ```bash
    kubectl apply -f kubernetes-security/namespace.yaml
    kubectl apply -f kubernetes-security/rbac.yaml
    kubectl apply -f kubernetes-security/storageClass.yaml
    kubectl apply -f kubernetes-security/pvc.yaml
    kubectl apply -f kubernetes-security/cm.yaml
    kubectl apply -f kubernetes-security/deployment.yaml
    kubectl apply -f kubernetes-security/service.yaml
    kubectl apply -f kubernetes-security/gateway.yaml
    kubectl apply -f kubernetes-security/httpRoute.yaml
    ```

 2. При необходимости сгенерируйте новый токен для service account `cd` сроком действия 1 день:

    ```bash
    kubectl create token cd -n homework --duration=24h > kubernetes-security/token
    ```

## Как проверить работоспособность

- Проверить, что service accounts созданы:

   ```bash
   kubectl get serviceaccount -n homework
   ```

- Проверить права service account `monitoring` на доступ к endpoint `/metrics`:

   ```bash
   kubectl auth can-i get /metrics --as=system:serviceaccount:homework:monitoring
   ```

- Проверить, что поды запускаются под service account `monitoring`:

   ```bash
   kubectl get pods -n homework -l app=homework -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.serviceAccountName}{"\n"}{end}'
   ```

- Проверить права service account `cd` в namespace `homework`:

   ```bash
   KUBECONFIG=kubernetes-security/kubeconfig-cd kubectl auth can-i create deployments -n homework
   KUBECONFIG=kubernetes-security/kubeconfig-cd kubectl auth can-i get pods -n homework
   ```

- Проверить статус подов:

   ```bash
   kubectl get pods -n homework
   ```

- Проверить, что init-контейнер отработал и создал файл `metrics.html`:

   ```bash
   kubectl exec -n homework deploy/homework-web -- ls -l /homework/metrics.html
   ```

- Проверить доступность через порт-форвардинг к сервису:

   ```bash
   kubectl port-forward -n homework svc/homework-web 8000:8000
   ```

   Перейти по ссылке <http://localhost:8000/index.html> — должна отобразиться HTML-страница, скачанная init-контейнером
- Проверить доступ к сохранённым метрикам кластера:

   ```bash
   curl http://localhost:8000/metrics.html
   ```

## PR checklist

- [x] Выставлен label с темой домашнего задания
