# kubeadm

Роль `kubeadm_deploy` устанавливает кластер, `kubeadm_upgrade` обновляет его. Для установки используется `install.yml`, для обновления — `upgrade.yml`. Поддерживается Ubuntu 24.04, один control-plane и произвольное число worker-нод; в примере — три.

Задачи `roles/kubeadm_upgrade/tasks/`: `main.yml` — проверки перед обновлением, `control_plane.yml` — control-plane, `worker.yml` — worker, `verify.yml` — итоговая проверка. `serial: 1` для worker-нод задан в `upgrade.yml`.

## 1. Подготовить ВМ и Ansible

На каждую ВМ: 4 vCPU, 8 GB RAM, постоянный внутренний IP-адрес, SSH-доступ с правами sudo, синхронизация времени и доступ к публичным репозиториям пакетов и образов. Разрешить TCP 22 с компьютера администратора, TCP 6443 к control-plane, TCP 10250 от control-plane к узлам, UDP 8472 между узлами.

```bash
cd kubernetes-prod/kubeadm
uv venv --python 3.12
source .venv/bin/activate
uv pip install --requirements requirements.txt
```

## 2. Задать параметры

- `inventory/hosts.yml` — имена узлов, адреса SSH-подключения и `node_ip`.
- `inventory/group_vars/all.yml` — SSH-пользователь, версии компонентов, адрес API и CIDR.

```yaml
kubernetes_version: "1.36.6"
kubernetes_upgrade_version: "1.37.2"
```

Pod/Service CIDR не должны пересекаться с сетью ВМ. При смене версии Flannel обновить также `flannel_checksum`. Если swap управляется отдельными systemd-юнитами или zram, отключить их вручную: роль отключает активный swap и комментирует записи swap в `/etc/fstab`.

## 3. Установить кластер

```bash
ansible-inventory --graph
ansible all -m ping
ansible-playbook install.yml --syntax-check
ansible-playbook install.yml
```

Если sudo требует пароль — добавить `-K`, SSH-ключ при необходимости передать через `--private-key`. Повторный запуск пропускает подготовку уже присоединённых узлов и не повторяет `init`/`join`. Для смены версии существующего кластера используется `upgrade.yml`. Изменение сетей существующего кластера и восстановление после незавершённой установки не автоматизированы.

## 4. Проверить до обновления

На control-plane:

```bash
sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get nodes -o wide
sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get pods -A -o wide
```

## 5. Обновить

Создать резервные копии etcd, `/etc/kubernetes`/PKI и данных приложений, сохранить их вне кластера и проверить возможность восстановления. Задать целевую `kubernetes_upgrade_version` в `inventory/group_vars/all.yml`. Во время обновления единственного control-plane возможна кратковременная недоступность API.

Из каталога `kubeadm` на компьютере администратора:

```bash
ansible-playbook upgrade.yml --syntax-check
ansible-playbook upgrade.yml
```

Порядок: проверка версий и готовности узлов → control-plane → worker-ноды с `serial: 1` → проверка результата. Запускать на всём inventory без `--limit`. Понижение версии и пропуск minor-версий запрещены. При `drain` не используются `--force` и `--delete-emptydir-data`; при ошибке процесс останавливается. Перед повторным запуском устранить причину ошибки, проверить готовность узла и вручную снять cordon с восстановленного узла. Автоматический откат не предусмотрен.

После обновления указать установленную версию также в `kubernetes_version`. Повторный запуск с той же целевой версией пропускает обновление узлов. `upgrade.yml` предназначен для кластеров, установленных ролью `kubeadm_deploy`, без ручного изменения версий отдельных компонентов.

## 6. Проверить после обновления

На control-plane:

```bash
sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get nodes -o wide
sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get --raw='/readyz?verbose'
```

Раздел для результатов до и после обновления: [Проверка](../README.md#проверка). Файлы kubeconfig, bootstrap-токены и резервные копии не должны попадать в Git.
