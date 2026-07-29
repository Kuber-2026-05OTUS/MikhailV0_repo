import kopf
from kubernetes import client, config
from kubernetes.client.rest import ApiException

GROUP = "otus.homework"
VERSION = "v1"
PLURAL = "mysqls"
STORAGE_CLASS = "mysql-local"


def load_config():
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config()


def ensure(create_func, patch_func, name, create_body, patch_body=None):
    try:
        create_func(body=create_body)
    except ApiException as error:
        if error.status != 409:
            raise
        patch_func(name=name, body=patch_body or create_body)


def ensure_static_pvc(core, namespace, name, create_body, labels, owners):
    try:
        core.create_namespaced_persistent_volume_claim(namespace, body=create_body)
    except ApiException as error:
        if error.status != 409:
            raise
        core.patch_namespaced_persistent_volume_claim(
            name,
            namespace,
            body={"metadata": {"labels": labels, "ownerReferences": owners}},
        )


def delete_if_exists(delete_func):
    try:
        delete_func()
    except ApiException as error:
        if error.status != 404:
            raise


def selector(name):
    return {"app": "mysql", "mysql.otus.homework/name": name}


def labels(name):
    return selector(name) | {"app.kubernetes.io/managed-by": "mysql-operator"}


def owner_reference(name, uid):
    return [
        {
            "apiVersion": f"{GROUP}/{VERSION}",
            "kind": "MySQL",
            "name": name,
            "uid": uid,
            "controller": True,
            "blockOwnerDeletion": True,
        }
    ]


@kopf.on.create(GROUP, VERSION, PLURAL)
@kopf.on.update(GROUP, VERSION, PLURAL)
@kopf.on.resume(GROUP, VERSION, PLURAL)
def reconcile_mysql(spec, name, namespace, uid, **_):
    load_config()

    image = spec.get("image", "mysql:8.0")
    database = spec.get("database", "app")
    password = spec["password"]
    storage_size = spec.get("storage_size", "1Gi")

    pv_name = f"{namespace}-{name}-pv"
    pvc_name = f"{name}-pvc"
    secret_name = f"{name}-secret"
    object_labels = labels(name)
    pod_selector = selector(name)
    owners = owner_reference(name, uid)

    core = client.CoreV1Api()
    apps = client.AppsV1Api()

    pv = {
        "apiVersion": "v1",
        "kind": "PersistentVolume",
        "metadata": {"name": pv_name, "labels": object_labels},
        "spec": {
            "capacity": {"storage": storage_size},
            "accessModes": ["ReadWriteOnce"],
            "persistentVolumeReclaimPolicy": "Delete",
            "storageClassName": STORAGE_CLASS,
            "hostPath": {"path": f"/tmp/mysql-operator/{namespace}-{name}"},
        },
    }
    ensure(
        core.create_persistent_volume,
        core.patch_persistent_volume,
        pv_name,
        pv,
        {"metadata": {"labels": object_labels}, "spec": {"capacity": {"storage": storage_size}}},
    )

    pvc = {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {
            "name": pvc_name,
            "namespace": namespace,
            "labels": object_labels,
            "ownerReferences": owners,
        },
        "spec": {
            "accessModes": ["ReadWriteOnce"],
            "storageClassName": STORAGE_CLASS,
            "volumeName": pv_name,
            "resources": {"requests": {"storage": storage_size}},
        },
    }
    ensure_static_pvc(
        core,
        namespace,
        pvc_name,
        pvc,
        object_labels,
        owners,
    )

    secret = {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {
            "name": secret_name,
            "namespace": namespace,
            "labels": object_labels,
            "ownerReferences": owners,
        },
        "type": "Opaque",
        "stringData": {"root-password": password},
    }
    ensure(
        lambda body: core.create_namespaced_secret(namespace, body),
        lambda name, body: core.patch_namespaced_secret(name, namespace, body),
        secret_name,
        secret,
        {"metadata": {"labels": object_labels, "ownerReferences": owners}, "stringData": {"root-password": password}},
    )

    service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": object_labels,
            "ownerReferences": owners,
        },
        "spec": {
            "type": "ClusterIP",
            "selector": pod_selector,
            "ports": [{"name": "mysql", "port": 3306, "targetPort": 3306}],
        },
    }
    ensure(
        lambda body: core.create_namespaced_service(namespace, body),
        lambda name, body: core.patch_namespaced_service(name, namespace, body),
        name,
        service,
        {
            "metadata": {"labels": object_labels, "ownerReferences": owners},
            "spec": {"selector": pod_selector, "ports": [{"name": "mysql", "port": 3306, "targetPort": 3306}]},
        },
    )

    pod_template = {
        "metadata": {"labels": object_labels},
        "spec": {
            "securityContext": {"fsGroup": 999},
            "containers": [
                {
                    "name": "mysql",
                    "image": image,
                    "imagePullPolicy": "IfNotPresent",
                    "ports": [{"containerPort": 3306}],
                    "env": [
                        {
                            "name": "MYSQL_ROOT_PASSWORD",
                            "valueFrom": {
                                "secretKeyRef": {"name": secret_name, "key": "root-password"}
                            },
                        },
                        {"name": "MYSQL_DATABASE", "value": database},
                    ],
                    "resources": {
                        "requests": {"cpu": "100m", "memory": "256Mi"},
                        "limits": {"cpu": "500m", "memory": "512Mi"},
                    },
                    "securityContext": {
                        "allowPrivilegeEscalation": False,
                        "readOnlyRootFilesystem": False,
                    },
                    "readinessProbe": {"tcpSocket": {"port": 3306}, "initialDelaySeconds": 20, "periodSeconds": 10},
                    "livenessProbe": {"tcpSocket": {"port": 3306}, "initialDelaySeconds": 60, "periodSeconds": 20},
                    "volumeMounts": [{"name": "data", "mountPath": "/var/lib/mysql"}],
                }
            ],
            "volumes": [{"name": "data", "persistentVolumeClaim": {"claimName": pvc_name}}],
        },
    }
    deployment = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": object_labels,
            "ownerReferences": owners,
        },
        "spec": {
            "replicas": 1,
            "selector": {"matchLabels": pod_selector},
            "template": pod_template,
        },
    }
    ensure(
        lambda body: apps.create_namespaced_deployment(namespace, body),
        lambda name, body: apps.patch_namespaced_deployment(name, namespace, body),
        name,
        deployment,
        {
            "metadata": {"labels": object_labels, "ownerReferences": owners},
            "spec": {"replicas": 1, "template": pod_template},
        },
    )

    return {"deployment": name, "service": name, "secret": secret_name, "pv": pv_name, "pvc": pvc_name}


@kopf.on.delete(GROUP, VERSION, PLURAL)
def delete_mysql(name, namespace, **_):
    load_config()

    core = client.CoreV1Api()
    apps = client.AppsV1Api()
    pv_name = f"{namespace}-{name}-pv"
    pvc_name = f"{name}-pvc"
    secret_name = f"{name}-secret"

    delete_if_exists(lambda: apps.delete_namespaced_deployment(name, namespace))
    delete_if_exists(lambda: core.delete_namespaced_service(name, namespace))
    delete_if_exists(lambda: core.delete_namespaced_secret(secret_name, namespace))
    delete_if_exists(lambda: core.delete_namespaced_persistent_volume_claim(pvc_name, namespace))
    delete_if_exists(lambda: core.delete_persistent_volume(pv_name))
