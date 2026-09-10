# Выполнено ДЗ № 13

- [x] Основное ДЗ
- [x] Задание со *

## В процессе сделано

- Добавлен манифест [`distroless-nginx-pod.yaml`](kubernetes-debug/distroless-nginx-pod.yaml) с Pod и Service `nginx-distroless`
- Проверен запуск ephemeral container для отладки distroless-контейнера через `kubectl debug`
- Проверен доступ к файловой системе контейнера через `/proc/<PID>/root`
- Проверен перехват HTTP-трафика к nginx через `tcpdump`
- Проверен запуск debug pod для ноды и просмотр логов pod через `/host/var/log/pods`
- Выполнен `strace` корневого процесса nginx из debug pod с профилем `sysadmin`

## Как запустить проект

1. Создать namespace:

   ```bash
   kubectl create namespace nginx-distroless
   ```

2. Применить манифест:

   ```bash
   kubectl apply -f kubernetes-debug/distroless-nginx-pod.yaml
   ```

## Как проверить работоспособность

- Проверить, что Pod и Service созданы:

  ```bash
  kubectl get pod,svc -n nginx-distroless
  ```

- Запустить ephemeral debug container:

  ```bash
  kubectl debug -n nginx-distroless -it pod/nginx-distroless \
    --image=harbor.mvl.test/docker/nicolaka/netshoot \
    --target=nginx-distroless \
    --container=debugger \
    --profile=sysadmin
  ```

- Найти PID процесса nginx и посмотреть файловую систему distroless-контейнера:

  ```bash
  PID=$(pgrep -o nginx)
  ls -la /proc/${PID}/root/etc/nginx
  ```

- Для `strace` корневого процесса nginx нужен debug container в том же pod с профилем `sysadmin`, чтобы были права на `ptrace`. Команда запуска `strace`:

  ```bash
  strace -f -tt -T -s 256 -p 7
  ```

- Запустить `tcpdump` в debug-контейнере:

  ```bash
  tcpdump -nn -q -t -c 20 -i any 'tcp port 80'
  ```

- В отдельном терминале выполнить запросы к nginx через Service `nginx-distroless`:

  ```bash
  kubectl run -n nginx-distroless curl-check \
    --rm -i \
    --restart=Never \
    --image=harbor.mvl.test/docker/curlimages/curl \
    --command -- \
    sh -c '
      for i in $(seq 1 5); do
        curl --fail --silent --show-error \
          --connect-timeout 2 \
          --max-time 5 \
          -o /dev/null \
          -w "http=%{http_code} peer=%{remote_ip} total=%{time_total}s\n" \
          http://nginx-distroless:80/ \
        || exit 1
      done
    '
  ```

- Создать debug pod для ноды, на которой запущен `nginx-distroless`:

  ```bash
  NODE=$(kubectl get pod -n nginx-distroless nginx-distroless -o jsonpath='{.spec.nodeName}')
  kubectl debug node/${NODE} -it \
    --image=harbor.mvl.test/docker/nicolaka/netshoot
  ```

- В debug pod ноды найти и посмотреть логи pod:

  ```bash
  chroot /host
  LOG_FILE=$(find /var/log/pods -path '*/nginx-distroless/*.log' | grep nginx-distroless | head -n 1)
  cat ${LOG_FILE}
  exit
  exit
  ```

## Как удалить ресурсы

```bash
kubectl delete namespace nginx-distroless
```

## Результаты проверки

Вывод `ls -la` для директории `/etc/nginx` отлаживаемого distroless-контейнера:

```text
$ls -la /proc/${PID}/root/etc/nginx
total 48
drwxr-xr-x    3 root     root          4096 Oct  5  2020 .
drwxr-xr-x    1 root     root          4096 Sep 10 19:37 ..
drwxr-xr-x    2 root     root          4096 Oct  5  2020 conf.d
-rw-r--r--    1 root     root          1007 Apr 21  2020 fastcgi_params
-rw-r--r--    1 root     root          2837 Apr 21  2020 koi-utf
-rw-r--r--    1 root     root          2223 Apr 21  2020 koi-win
-rw-r--r--    1 root     root          5231 Apr 21  2020 mime.types
lrwxrwxrwx    1 root     root            22 Apr 21  2020 modules -> /usr/lib/nginx/modules
-rw-r--r--    1 root     root           643 Apr 21  2020 nginx.conf
-rw-r--r--    1 root     root           636 Apr 21  2020 scgi_params
-rw-r--r--    1 root     root           664 Apr 21  2020 uwsgi_params
-rw-r--r--    1 root     root          3610 Apr 21  2020 win-utf
```

Для выполнения `strace` корневого процесса nginx debug container запускался в том же pod с `--profile=sysadmin`. Профиль нужен, чтобы debug container получил права, достаточные для подключения к процессу nginx через `ptrace`.

Вывод `strace` после нескольких запросов `curl` к Service `nginx-distroless`:

```text
$ strace -f -tt -T -s 256 -p 7
strace: Process 7 attached
19:51:36.429388 epoll_wait(8, [{events=EPOLLIN, data=0x7b01fb778010}], 512, -1) = 1 <19.487049>
19:51:55.916663 accept4(6, {sa_family=AF_INET, sin_port=htons(38230), sin_addr=inet_addr("10.233.66.162")}, [112 => 16], SOCK_NONBLOCK) = 3 <0.000037>
19:51:55.919723 epoll_ctl(8, EPOLL_CTL_ADD, 3, {events=EPOLLIN|EPOLLRDHUP|EPOLLET, data=0x7b01fb7781e0}) = 0 <0.000018>
19:51:55.919833 epoll_wait(8, [{events=EPOLLIN, data=0x7b01fb7781e0}], 512, 60000) = 1 <0.000009>
19:51:55.919999 recvfrom(3, "GET / HTTP/1.1\r\nHost: nginx-distroless\r\nUser-Agent: curl/8.22.0\r\nAccept: */*\r\n\r\n", 1024, 0, NULL, NULL) = 80 <0.000033>
19:51:55.920222 stat("/usr/share/nginx/html/index.html", {st_mode=S_IFREG|0644, st_size=612, ...}) = 0 <0.000028>
19:51:55.920375 openat(AT_FDCWD, "/usr/share/nginx/html/index.html", O_RDONLY|O_NONBLOCK) = 11 <0.000055>
19:51:55.920532 fstat(11, {st_mode=S_IFREG|0644, st_size=612, ...}) = 0 <0.000105>
19:51:55.920734 writev(3, [{iov_base="HTTP/1.1 200 OK\r\nServer: nginx/1.18.0\r\nDate: Thu, 10 Sep 2026 19:51:55 GMT\r\nContent-Type: text/html\r\nContent-Length: 612\r\nLast-Modified: Tue, 21 Apr 2020 12:43:12 GMT\r\nConnection: keep-alive\r\nETag: \"5e9eea60-264\"\r\nAccept-Ranges: bytes\r\n\r\n", iov_len=238}], 1) = 238 <0.000359>
19:51:55.921390 sendfile(3, 11, [0] => [612], 612) = 612 <0.000054>
19:51:55.921576 write(5, "10.233.66.162 - - [11/Sep/2026:03:51:55 +0800] \"GET / HTTP/1.1\" 200 612 \"-\" \"curl/8.22.0\" \"-\"\n", 94) = 94 <0.000182>
19:51:55.921881 close(11)               = 0 <0.000075>
19:51:55.922100 setsockopt(3, SOL_TCP, TCP_NODELAY, [1], 4) = 0 <0.000078>
19:51:55.922288 epoll_wait(8, [{events=EPOLLIN|EPOLLRDHUP, data=0x7b01fb7781e0}], 512, 65000) = 1 <0.000573>
19:51:55.923118 recvfrom(3, "", 1024, 0, NULL, NULL) = 0 <0.000270>
19:51:55.923585 close(3)                = 0 <0.000143>
19:51:55.923854 epoll_wait(8, [{events=EPOLLIN, data=0x7b01fb778010}], 512, -1) = 1 <0.009429>
19:51:55.933510 accept4(6, {sa_family=AF_INET, sin_port=htons(38238), sin_addr=inet_addr("10.233.66.162")}, [112 => 16], SOCK_NONBLOCK) = 3 <0.000146>
19:51:55.933771 epoll_ctl(8, EPOLL_CTL_ADD, 3, {events=EPOLLIN|EPOLLRDHUP|EPOLLET, data=0x7b01fb7781e1}) = 0 <0.000033>
19:51:55.934293 epoll_wait(8, [{events=EPOLLIN, data=0x7b01fb7781e1}], 512, 60000) = 1 <0.000092>
19:51:55.934533 recvfrom(3, "GET / HTTP/1.1\r\nHost: nginx-distroless\r\nUser-Agent: curl/8.22.0\r\nAccept: */*\r\n\r\n", 1024, 0, NULL, NULL) = 80 <0.000038>
19:51:55.934775 stat("/usr/share/nginx/html/index.html", {st_mode=S_IFREG|0644, st_size=612, ...}) = 0 <0.000050>
19:51:55.935048 openat(AT_FDCWD, "/usr/share/nginx/html/index.html", O_RDONLY|O_NONBLOCK) = 11 <0.000035>
19:51:55.935177 fstat(11, {st_mode=S_IFREG|0644, st_size=612, ...}) = 0 <0.000061>
19:51:55.935404 writev(3, [{iov_base="HTTP/1.1 200 OK\r\nServer: nginx/1.18.0\r\nDate: Thu, 10 Sep 2026 19:51:55 GMT\r\nContent-Type: text/html\r\nContent-Length: 612\r\nLast-Modified: Tue, 21 Apr 2020 12:43:12 GMT\r\nConnection: keep-alive\r\nETag: \"5e9eea60-264\"\r\nAccept-Ranges: bytes\r\n\r\n", iov_len=238}], 1) = 238 <0.000184>
19:51:55.935780 sendfile(3, 11, [0] => [612], 612) = 612 <0.000052>
```

Вывод `tcpdump`, подтверждающий сетевые обращения к nginx:

```text
$tcpdump -nn -q -t -c 20 -i any 'tcp port 80'
tcpdump: WARNING: any: That device doesn't support promiscuous mode
(Promiscuous mode not supported on the "any" device)
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on any, link-type LINUX_SLL2 (Linux cooked v2), snapshot length 262144 bytes
eth0  In  IP 10.233.66.128.58820 > 10.233.64.224.80: tcp 0
eth0  Out IP 10.233.64.224.80 > 10.233.66.128.58820: tcp 0
eth0  In  IP 10.233.66.128.58820 > 10.233.64.224.80: tcp 0
eth0  In  IP 10.233.66.128.58820 > 10.233.64.224.80: tcp 80
eth0  Out IP 10.233.64.224.80 > 10.233.66.128.58820: tcp 0
eth0  Out IP 10.233.64.224.80 > 10.233.66.128.58820: tcp 238
eth0  Out IP 10.233.64.224.80 > 10.233.66.128.58820: tcp 612
eth0  In  IP 10.233.66.128.58820 > 10.233.64.224.80: tcp 0
eth0  In  IP 10.233.66.128.58820 > 10.233.64.224.80: tcp 0
eth0  In  IP 10.233.66.128.58820 > 10.233.64.224.80: tcp 0
eth0  Out IP 10.233.64.224.80 > 10.233.66.128.58820: tcp 0
eth0  In  IP 10.233.66.128.58820 > 10.233.64.224.80: tcp 0
eth0  In  IP 10.233.66.128.58828 > 10.233.64.224.80: tcp 0
eth0  Out IP 10.233.64.224.80 > 10.233.66.128.58828: tcp 0
eth0  In  IP 10.233.66.128.58828 > 10.233.64.224.80: tcp 0
eth0  In  IP 10.233.66.128.58828 > 10.233.64.224.80: tcp 80
eth0  Out IP 10.233.64.224.80 > 10.233.66.128.58828: tcp 0
eth0  Out IP 10.233.64.224.80 > 10.233.66.128.58828: tcp 238
eth0  Out IP 10.233.64.224.80 > 10.233.66.128.58828: tcp 612
eth0  In  IP 10.233.66.128.58828 > 10.233.64.224.80: tcp 0
20 packets captured
48 packets received by filter
0 packets dropped by kernel
```

Команда получения логов pod с distroless nginx через debug pod ноды:

```bash
chroot /host
LOG_FILE=$(find /var/log/pods -path '*/nginx-distroless/*.log' | grep nginx-distroless | head -n 1)
cat ${LOG_FILE}
```

Логи pod с distroless nginx:

```text
root@worker-01:/# cat ${LOG_FILE}
2026-09-10T22:39:54.7957228+03:00 stdout F 10.233.66.18 - - [11/Sep/2026:03:39:54 +0800] "GET / HTTP/1.1" 200 612 "-" "curl/8.22.0" "-"
2026-09-10T22:39:54.808115085+03:00 stdout F 10.233.66.18 - - [11/Sep/2026:03:39:54 +0800] "GET / HTTP/1.1" 200 612 "-" "curl/8.22.0" "-"
2026-09-10T22:39:54.818517485+03:00 stdout F 10.233.66.18 - - [11/Sep/2026:03:39:54 +0800] "GET / HTTP/1.1" 200 612 "-" "curl/8.22.0" "-"
2026-09-10T22:39:54.829027494+03:00 stdout F 10.233.66.18 - - [11/Sep/2026:03:39:54 +0800] "GET / HTTP/1.1" 200 612 "-" "curl/8.22.0" "-"
2026-09-10T22:39:54.838343226+03:00 stdout F 10.233.66.18 - - [11/Sep/2026:03:39:54 +0800] "GET / HTTP/1.1" 200 612 "-" "curl/8.22.0" "-"
2026-09-10T22:41:29.288292+03:00 stdout F 10.233.66.162 - - [11/Sep/2026:03:41:29 +0800] "GET / HTTP/1.1" 200 612 "-" "curl/8.22.0" "-"
2026-09-10T22:41:29.302984369+03:00 stdout F 10.233.66.162 - - [11/Sep/2026:03:41:29 +0800] "GET / HTTP/1.1" 200 612 "-" "curl/8.22.0" "-"
2026-09-10T22:41:29.314865593+03:00 stdout F 10.233.66.162 - - [11/Sep/2026:03:41:29 +0800] "GET / HTTP/1.1" 200 612 "-" "curl/8.22.0" "-"
2026-09-10T22:41:29.325943656+03:00 stdout F 10.233.66.162 - - [11/Sep/2026:03:41:29 +0800] "GET / HTTP/1.1" 200 612 "-" "curl/8.22.0" "-"
2026-09-10T22:41:29.337382916+03:00 stdout F 10.233.66.162 - - [11/Sep/2026:03:41:29 +0800] "GET / HTTP/1.1" 200 612 "-" "curl/8.22.0" "-"
2026-09-10T22:42:46.550357905+03:00 stdout F 10.233.66.128 - - [11/Sep/2026:03:42:46 +0800] "GET / HTTP/1.1" 200 612 "-" "curl/8.22.0" "-"
2026-09-10T22:42:46.562447097+03:00 stdout F 10.233.66.128 - - [11/Sep/2026:03:42:46 +0800] "GET / HTTP/1.1" 200 612 "-" "curl/8.22.0" "-"
2026-09-10T22:42:46.572273188+03:00 stdout F 10.233.66.128 - - [11/Sep/2026:03:42:46 +0800] "GET / HTTP/1.1" 200 612 "-" "curl/8.22.0" "-"
2026-09-10T22:42:46.582281756+03:00 stdout F 10.233.66.128 - - [11/Sep/2026:03:42:46 +0800] "GET / HTTP/1.1" 200 612 "-" "curl/8.22.0" "-"
2026-09-10T22:42:46.591303963+03:00 stdout F 10.233.66.128 - - [11/Sep/2026:03:42:46 +0800] "GET / HTTP/1.1" 200 612 "-" "curl/8.22.0" "-"

```

## Приложенные манифесты для проверки ДЗ

- [`distroless-nginx-pod.yaml`](kubernetes-debug/distroless-nginx-pod.yaml)

## PR checklist:

- [x] Выставлен label с темой домашнего задания
