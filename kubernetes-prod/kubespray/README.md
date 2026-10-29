# Kubespray

## Порядок работы

- Код Kubespray и inventory хранятся отдельно: inventory — в этом каталоге, код — в `$HOME/kubespray`.
- Версия Kubespray фиксируется стабильным тегом. Ветки `master` / `main` для развёртывания не используются.
- Перед сменой релиза проверяются изменения `inventory/sample` и совместимость переменных inventory.
- Обновление выполняется последовательно по поддерживаемым релизам Kubespray, Kubernetes — без пропуска minor-версий.
- `cluster.yml` — установка и повторное применение конфигурации; `upgrade-cluster.yml` — rolling upgrade существующего кластера.

## 1. Подготовить inventory и ВМ

Inventory расположен в [`inventory/prod/inventory.yaml`](inventory/prod/inventory.yaml), параметры кластера — в `inventory/prod/group_vars`. Изменения конфигурации вносятся в inventory, не в код Kubespray.

Требуются 6 ВМ с Ubuntu 24.04: 3 control-plane / etcd и 3 worker, каждая — 4 vCPU, 8 GB RAM. Эти узлы не должны входить в кластер из раздела kubeadm.

Адреса и имена в таблице приведены для примера. Перед запуском заменить их значениями выбранного стенда:

| Параметр                 | Пример                                                                                         |
| ------------------------ | ---------------------------------------------------------------------------------------------- |
| control-plane            | `control-01.k8s.example.test` … `control-03.k8s.example.test`, `198.51.100.11`–`198.51.100.13` |
| worker                   | `compute-01.k8s.example.test` … `compute-03.k8s.example.test`, `198.51.100.21`–`198.51.100.23` |
| VIP / DNS-имя API        | `198.51.100.50` / `api.k8s.example.test`                                                       |
| NTP                      | `198.51.100.254`                                                                               |
| Cilium LoadBalancer pool | `198.51.100.100`–`198.51.100.115`                                                              |
| Интерфейс kube-vip       | `eth0`                                                                                         |

Файлы конфигурации относительно `inventory/prod`: `inventory.yaml`, `group_vars/all/all.yml`, `group_vars/k8s_cluster/{k8s-cluster,addons,k8s-net-cilium}.yml`. DNS-имя API должно указывать на VIP.

Требуются SSH-доступ с правами sudo, разрешение имён узлов через DNS или `/etc/hosts`, доступ к публичным репозиториям пакетов и образов. Pod/Service CIDR не должны пересекаться с сетью ВМ/VPN. kube-vip ARP и Cilium L2 требуют подходящей L2-сети.

## 2. Скачать код и выбрать релиз

Команды выполняются на компьютере администратора; нужны Git, `uv` и Python 3.12.

```bash
export REPO='/path/to/MikhailV0_repo'
export INVENTORY="$REPO/kubernetes-prod/kubespray/inventory/prod"
git clone https://github.com/kubernetes-sigs/kubespray.git "$HOME/kubespray"
cd "$HOME/kubespray"
git fetch origin --tags
git tag --sort=-version:refname
git checkout v2.32.0
git describe --tags --always
```

В этом репозитории используется inventory из `inventory/prod`. При создании нового inventory sample копируется **за пределы** клона Kubespray в отдельный каталог:

```bash
# Только при подготовке нового inventory с нуля:
cp -a inventory/sample ../new-cluster-inventory
```

## 3. Подготовить Python-окружение

Из каталога кода Kubespray:

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install --requirements requirements.txt
ansible --version
```

После переключения тега установить зависимости из `requirements.txt` выбранного релиза. При изменении требований к Python пересоздать виртуальное окружение с поддерживаемой версией.

## 4. Проверить и развернуть

```bash
ansible-inventory -i "$INVENTORY/inventory.yaml" --graph
ansible -i "$INVENTORY/inventory.yaml" all -m ping
ansible-playbook -i "$INVENTORY/inventory.yaml" -b cluster.yml
```

Параметры SSH-подключения задаются в inventory или SSH-конфигурации. Если sudo требует пароль — добавить `-K`. Повторное применение конфигурации выполняется той же командой `cluster.yml`.

`kube_version` в inventory не переопределён: применяется значение по умолчанию выбранного тега (`v1.36.4` для `v2.32.0`). При необходимости закрепить поддерживаемую версию явно в `group_vars/k8s_cluster/k8s-cluster.yml`.

## 5. Обновить Kubespray и inventory

Команды ниже показывают переход `v2.31.0 → v2.32.0`; значения тегов должны соответствовать текущему и целевому релизам кластера. Перед обновлением создать резервные копии etcd, PKI и данных приложений, сохранить их вне кластера и проверить возможность восстановления.

```bash
cd "$HOME/kubespray"
git status --short
git describe --tags --always
git fetch origin --tags
git tag --sort=-version:refname
export OLD_TAG=v2.31.0
export NEXT_TAG=v2.32.0
git diff "$OLD_TAG..$NEXT_TAG" -- inventory/sample
git diff "$OLD_TAG..$NEXT_TAG" -- inventory/sample/group_vars
git checkout "$NEXT_TAG"
source .venv/bin/activate
uv pip install --requirements requirements.txt
diff -ruN --exclude=.git --exclude=.ansible --exclude=artifacts --exclude=credentials \
  inventory/sample "$INVENTORY"
```

`diff` возвращает код 1 при наличии отличий — это не ошибка сравнения. Обновить inventory с учётом новых обязательных параметров, устаревших переменных, изменений значений по умолчанию и структуры файлов. Перед сменой тега сохранить локальные изменения и убедиться, что рабочее дерево Kubespray чистое. Секреты и генерируемые файлы не должны попадать в репозиторий inventory.

Если `kube_version` закреплён, указать целевую версию Kubernetes, поддерживаемую выбранным релизом Kubespray. Затем выполнить последовательное обновление существующего кластера:

```bash
ansible-playbook -i "$INVENTORY/inventory.yaml" -b upgrade-cluster.yml
```

Kubespray управляет порядком и размером групп обновления: control-plane — по одному узлу, worker-ноды — группами по `20%` в `v2.32.0`. Для трёх worker-нод это один узел за раз. При ошибке устранить причину перед повторным запуском; понижение версии не является штатным способом отката. Для первичного развёртывания используется `cluster.yml`.

## 6. Проверить результат

На control-plane:

```bash
sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get nodes -o wide
sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get pods -A -o wide
sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get --raw='/readyz?verbose'
sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf -n kube-system \
  rollout status daemonset/cilium --timeout=300s
```

Ожидаются 6 узлов в состоянии `Ready`. kube-proxy не разворачивается: используется Cilium kube-proxy replacement. Раздел для результатов: [Проверка](../README.md#проверка).
