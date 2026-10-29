# ДЗ № 14 — Развёртывание и обновление Kubernetes

- [X] Основное ДЗ
- [X] Задание со *

## В процессе сделано

- Роль `kubeadm_deploy` подготавливает Ubuntu 24.04, устанавливает containerd, kubeadm, kubelet, kubectl и Flannel, выполняет `init` и `join`.
- Роль `kubeadm_upgrade` обновляет Kubernetes `1.36.6 → 1.37.2`: сначала control-plane, затем worker-ноды с `drain` / `uncordon`.
- Inventory Kubespray описывает HA-кластер: 3 control-plane / etcd и 3 worker, Cilium и kube-vip.

## Как запустить проект

1. Основное ДЗ: [kubeadm/README.md](kubeadm/README.md) — 1 control-plane и 3 worker.
2. Задание со *: [kubespray/README.md](kubespray/README.md) — отдельный HA-кластер.

На каждой ВМ: 4 vCPU, 8 GB RAM. IP-адреса и имена узлов в inventory приведены для примера.

## Проверка

IP-адреса в выводах приведены для примера.

На control-plane каждого кластера:

```bash
sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get nodes -o wide
sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get pods -A -o wide
```

### kubeadm — до обновления

```bash
root@master-01:~# kubectl --kubeconfig /etc/kubernetes/admin.conf get nodes -o wide
NAME        STATUS   ROLES           AGE     VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION              CONTAINER-RUNTIME
master-01   Ready    control-plane   2m41s   v1.36.6   192.0.2.10    <none>        Ubuntu 24.04.5 LTS   6.8.0-146-generic (amd64)   containerd://2.4.2
worker-01   Ready    <none>          2m27s   v1.36.6   192.0.2.11    <none>        Ubuntu 24.04.5 LTS   6.8.0-146-generic (amd64)   containerd://2.4.2
worker-02   Ready    <none>          2m27s   v1.36.6   192.0.2.12    <none>        Ubuntu 24.04.5 LTS   6.8.0-146-generic (amd64)   containerd://2.4.2
worker-03   Ready    <none>          2m27s   v1.36.6   192.0.2.13    <none>        Ubuntu 24.04.5 LTS   6.8.0-146-generic (amd64)   containerd://2.4.2

```

### kubeadm — после обновления

```bash
root@master-01:~# kubectl --kubeconfig /etc/kubernetes/admin.conf get nodes -o wide
NAME        STATUS   ROLES           AGE   VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION              CONTAINER-RUNTIME
master-01   Ready    control-plane   12m   v1.37.2   192.0.2.10    <none>        Ubuntu 24.04.5 LTS   6.8.0-146-generic (amd64)   containerd://2.4.2
worker-01   Ready    <none>          12m   v1.37.2   192.0.2.11    <none>        Ubuntu 24.04.5 LTS   6.8.0-146-generic (amd64)   containerd://2.4.2
worker-02   Ready    <none>          12m   v1.37.2   192.0.2.12    <none>        Ubuntu 24.04.5 LTS   6.8.0-146-generic (amd64)   containerd://2.4.2
worker-03   Ready    <none>          12m   v1.37.2   192.0.2.13    <none>        Ubuntu 24.04.5 LTS   6.8.0-146-generic (amd64)   containerd://2.4.2
```

### Kubespray

```bash
root@control-01:~# kubectl get nodes -o wide
NAME                          STATUS   ROLES           AGE     VERSION   INTERNAL-IP    EXTERNAL-IP   OS-IMAGE             KERNEL-VERSION              CONTAINER-RUNTIME
compute-01.k8s.example.test   Ready    worker          7m35s   v1.36.4   198.51.100.21  <none>        Ubuntu 24.04.5 LTS   6.8.0-146-generic (amd64)   containerd://2.3.5
compute-02.k8s.example.test   Ready    worker          7m35s   v1.36.4   198.51.100.22  <none>        Ubuntu 24.04.5 LTS   6.8.0-146-generic (amd64)   containerd://2.3.5
compute-03.k8s.example.test   Ready    worker          7m35s   v1.36.4   198.51.100.23  <none>        Ubuntu 24.04.5 LTS   6.8.0-146-generic (amd64)   containerd://2.3.5
control-01.k8s.example.test   Ready    control-plane   8m57s   v1.36.4   198.51.100.11  <none>        Ubuntu 24.04.5 LTS   6.8.0-146-generic (amd64)   containerd://2.3.5
control-02.k8s.example.test   Ready    control-plane   8m22s   v1.36.4   198.51.100.12  <none>        Ubuntu 24.04.5 LTS   6.8.0-146-generic (amd64)   containerd://2.3.5
control-03.k8s.example.test   Ready    control-plane   7m58s   v1.36.4   198.51.100.13  <none>        Ubuntu 24.04.5 LTS   6.8.0-146-generic (amd64)   containerd://2.3.5

```

## PR checklist

- [ ] Приложены результаты выполнения.
- [ ] Выставлен label с темой домашнего задания.
