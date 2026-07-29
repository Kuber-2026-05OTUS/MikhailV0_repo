# Выполнено ДЗ № 7

- [x] Основное ДЗ

## В процессе сделано

- Подготовлен кастомный образ nginx `harbor.mvl.test/library/nginx-custom-mon:1.0.1` на базе внутреннего образа `harbor.mvl.test/docker/nginx:1.31.3`.
- В [`nginx/default.conf`](nginx/default.conf) настроен endpoint `/basic_status` с директивой `stub_status`, на котором nginx отдаёт служебные метрики.
- В [`nginx/Dockerfile`](nginx/Dockerfile) добавлена замена стандартного конфига nginx на кастомный [`nginx/default.conf`](nginx/default.conf).
- Образ собран и опубликован во внутренний registry `harbor.mvl.test`.
- Установлен Prometheus Operator через Helm-чарт `kube-prometheus-stack`, скачанный из OCI registry `ghcr.io/prometheus-community/charts`.
- Для установки Prometheus Operator использован файл [`prom/values_custom_prom.yaml`](prom/values_custom_prom.yaml), который применяется поверх дефолтного [`values.yaml`](prom/values.yaml) и снижает потребление ресурсов компонентами мониторинга.
- Создан namespace [`ns.yaml`](ns.yaml) `nginx-monitoring`.
- Создан Deployment [`deployment.yaml`](deployment.yaml) с nginx и `nginx-prometheus-exporter`, который собирает данные с `http://127.0.0.1/basic_status` и отдаёт их в формате Prometheus на порту `9113`.
- Создан Service [`svc.yaml`](svc.yaml) типа `ClusterIP` с портами `http` и `metrics`.
- Создан ServiceMonitor [`servicemonitor.yaml`](servicemonitor.yaml), описывающий сбор метрик Prometheus с порта `metrics` по пути `/metrics`.

## Как запустить проект

1. Собрать кастомный образ nginx:

   ```bash
   cd kubernetes-monitoring
   docker build -t harbor.mvl.test/library/nginx-custom-mon:1.0.1 --no-cache nginx/
   ```

2. Опубликовать образ в registry:

   ```bash
   docker push harbor.mvl.test/library/nginx-custom-mon:1.0.1
   ```

3. Выбрать нужную версию Helm-чарта `kube-prometheus-stack` из списка версий:

   <https://github.com/prometheus-community/helm-charts/pkgs/container/charts%2Fkube-prometheus-stack>

4. Скачать выбранную версию чарта из OCI registry:

   ```bash
   helm pull oci://ghcr.io/prometheus-community/charts/kube-prometheus-stack \
     --version <VERSION> \
     --untar
   ```

5. Перейти в каталог распакованного чарта и установить Prometheus Operator с дефолтными значениями и дополнительными параметрами из [`prom/values_custom_prom.yaml`](prom/values_custom_prom.yaml):

   ```bash
   helm upgrade --install kps . -f values.yaml -f values_custom_prom.yaml --dependency-update --create-namespace --namespace monitoring
   ```

6. Применить манифесты nginx и ServiceMonitor:

   ```bash
   kubectl apply -f kubernetes-monitoring/ns.yaml
   kubectl apply -f kubernetes-monitoring/deployment.yaml
   kubectl apply -f kubernetes-monitoring/svc.yaml
   kubectl apply -f kubernetes-monitoring/servicemonitor.yaml
   ```

## Как проверить работоспособность

- Проверить, что Prometheus Operator установлен:

  ```bash
  kubectl get pods -n monitoring
  kubectl get crd | grep servicemonitors.monitoring.coreos.com
  ```

- Проверить, что приложение nginx запущено:

  ```bash
  kubectl get pods,svc,servicemonitor -n nginx-monitoring
  ```

- Проверить endpoint nginx `stub_status`:

  ```bash
  kubectl port-forward -n nginx-monitoring svc/nginx-stub-status 8080:80
  curl http://localhost:8080/basic_status
  ```

  В ответе должны отображаться значения `Active connections`, `server accepts handled requests`, `Reading`, `Writing`, `Waiting`.

- Проверить метрики exporter-а:

  ```bash
  kubectl port-forward -n nginx-monitoring svc/nginx-stub-status 9113:9113
  curl http://localhost:9113/metrics
  ```

  В ответе должны быть метрики nginx в формате Prometheus, например `nginx_connections_active`.

- Проверить, что ServiceMonitor создан и выбирает нужный Service:

  ```bash
  kubectl describe servicemonitor nginx-stub-status -n nginx-monitoring
  kubectl get svc nginx-stub-status -n nginx-monitoring --show-labels
  ```

- Проверить target в Prometheus UI:

  ```bash
  kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
  ```

  После этого открыть <http://localhost:9090/targets> и убедиться, что target для `nginx-stub-status` находится в состоянии `UP`.

## PR checklist

- [x] Выставлен label с темой домашнего задания

