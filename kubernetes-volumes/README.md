# Выполнено ДЗ № 4

 - [x] Основное ДЗ
 - [x] Задание со *

## В процессе сделано:
 - Создан манифест [`pvc.yaml`](kubernetes-volumes/pvc.yaml) — PersistentVolumeClaim `homework-pvc`, запрашивающий хранилище размером 130M из StorageClass `homework-sc`
 - Создан манифест [`cm.yaml`](kubernetes-volumes/cm.yaml) — ConfigMap `homework-config` с набором пар ключ-значение: `nginx.conf` (конфигурация nginx), `file` (свойства приложения), `log-level`, `max-connections`
 - В манифесте [`deployment.yaml`](kubernetes-volumes/deployment.yaml) том типа `emptyDir` заменён на `persistentVolumeClaim`, ссылающийся на `homework-pvc`. Том монтируется в init-контейнер (скачивает `index.html`) и в основной контейнер (nginx, директория `/homework`)
 - В манифесте [`deployment.yaml`](kubernetes-volumes/deployment.yaml) добавлено монтирование ConfigMap `homework-config` как volume в основной контейнер:
   - `/etc/nginx/conf.d/default.conf` (subPath: `nginx.conf`) — конфигурация nginx
   - `/homework/conf` — директория с файлами ConfigMap, доступная по URL `/conf/file`
 - **Задание со \***: создан манифест [`storageClass.yaml`](kubernetes-volumes/storageClass.yaml) — StorageClass `homework-sc` с provisioner `rancher.io/local-path` и `reclaimPolicy: Retain`. Манифест [`pvc.yaml`](kubernetes-volumes/pvc.yaml) изменён — теперь PVC запрашивает хранилище созданного StorageClass (`storageClassName: homework-sc`)

## Как запустить проект:
 1. Примените манифесты в порядке:
    ```bash
    kubectl apply -f kubernetes-volumes/namespace.yaml
    kubectl apply -f kubernetes-volumes/storageClass.yaml
    kubectl apply -f kubernetes-volumes/pvc.yaml
    kubectl apply -f kubernetes-volumes/cm.yaml
    kubectl apply -f kubernetes-volumes/deployment.yaml
    kubectl apply -f kubernetes-volumes/service.yaml
    kubectl apply -f kubernetes-volumes/gateway.yaml
    kubectl apply -f kubernetes-volumes/httpRoute.yaml
    ```

## Как проверить работоспособность:
 - Проверить, что PVC создан и привязан (Bound):
   ```bash
   kubectl get pvc -n homework
   ```
 - Проверить статус подов:
   ```bash
   kubectl get pods -n homework
   ```
 - Проверить, что init-контейнер отработал и PVC примонтирован:
   ```bash
   kubectl describe pod -n homework -l app=homework
   ```
 - Проверить доступность через порт-форвардинг к сервису:
   ```bash
   kubectl port-forward -n homework svc/homework-web 8000:8000
   ```
   Перейти по ссылке http://localhost:8000/index.html — должна отобразиться HTML-страница, скачанная init-контейнером
 - Проверить доступ к содержимому ConfigMap, обратившись в браузере по URL `/conf/file`:
   ```
   http://localhost:8000/conf/file
   ```

## PR checklist:
 - [x] Выставлен label с темой домашнего задания
