# Выполнено ДЗ № 3

 - [x] Основное ДЗ
 - [x] Задание со *

## В процессе сделано:
 - Изменена readiness-проба в [`deployment.yaml`](kubernetes-networks/deployment.yaml) с `exec` (проверка наличия файла через `test -f`) на `httpGet`, вызывающую URL `/index.html` на порту 8000
 - Создан манифест [`service.yaml`](kubernetes-networks/service.yaml), описывающий сервис типа `ClusterIP`, который направляет трафик на поды, управляемые Deployment `homework-web`
 - Установлен в кластер Gateway API контроллер Traefik
 - Создан манифест [`gateway.yaml`](kubernetes-networks/gateway.yaml), описывающий объект Gateway с одним listener (протокол HTTP, порт 8000) и явным разрешением доступа ко всем namespaces (`allowedRoutes.namespaces.from: All`)
 - Создан манифест [`httpRoute.yaml`](kubernetes-networks/httpRoute.yaml), описывающий объект HTTPRoute, направляющий все HTTP-запросы к хосту `homework.otus` на ранее созданный сервис `homework-web:8000`
 - **Задание со \***: доработан [`httpRoute.yaml`](kubernetes-networks/httpRoute.yaml) — добавлено rewrite-правило (`URLRewrite` с `ReplaceFullPath`), чтобы обращение по адресу `http://homework.otus/homepage` форвардилось на `http://homework.otus/index.html`

## Как запустить проект:
 1. Установите кластер Kubernetes любым удобным способом, без Ingress-контроллера. Для LoadBalancer настройте MetalLB или Cilium (L2 или BGP — не важно)
 2. Установите в кластер CRD Gateway API:
    ```bash
    kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.5.1/standard-install.yaml
    ```
 3. Добавьте Helm-репозиторий Traefik и обновите его:
    ```bash
    helm repo add traefik https://traefik.github.io/charts && helm repo update
    ```
 4. Установите Traefik с поддержкой Gateway API:
    ```bash
    helm upgrade --install traefik traefik/traefik \
      -n traefik \
      --create-namespace \
      --reset-values \
      --set providers.kubernetesGateway.enabled=true \
      --set providers.kubernetesCRD.enabled=false \
      --set providers.kubernetesIngress.enabled=false \
      --set service.spec.type=LoadBalancer \
      --set ports.web.port=8000 \
      --set ports.web.exposedPort=80 \
      --set gateway.listeners.web.port=8000
    ```
 5. Пометьте ноды, на которых будут запускаться поды:
    ```bash
    kubectl label node <node-name> homework=true
    ```
 6. Примените манифесты в порядке:
    ```bash
    kubectl apply -f kubernetes-networks/namespace.yaml
    kubectl apply -f kubernetes-networks/deployment.yaml
    kubectl apply -f kubernetes-networks/service.yaml
    kubectl apply -f kubernetes-networks/gateway.yaml
    kubectl apply -f kubernetes-networks/httpRoute.yaml
    ```

## Как проверить работоспособность:
 - Для доступа по FQDN `homework.otus` необходимо настроить разрешение имени. Выберите один из способов:
   - **Локальный hosts**: добавьте запись в `/etc/hosts` (Linux/macOS) или `C:\Windows\System32\drivers\etc\hosts` (Windows):
     ```
     <gateway-ip> homework.otus
     ```
   - **Временная DNS-запись**: если в сети используется DNS-сервер, добавьте A-запись `homework.otus → <gateway-ip>`
 - Проверить статус подов, сервиса, Gateway и HTTPRoute:
   ```bash
   kubectl get pods,svc,gateway,httproute -n homework
   ```
 - Проверить доступность через порт-форвардинг к сервису:
   ```bash
   kubectl port-forward -n homework svc/homework-web 8000:8000
   ```
   Перейти по ссылке http://localhost:8000/index.html — должна отобразиться HTML-страница
 - Проверить маршрутизацию через Gateway:
   ```bash
   curl http://homework.otus/index.html
   ```
 - Проверить rewrite-правило (задание со *):
   ```bash
   curl http://homework.otus/homepage
   ```
   Должен вернуться тот же HTML, что и при запросе `/index.html`

## PR checklist:
 - [x] Выставлен label с темой домашнего задания
