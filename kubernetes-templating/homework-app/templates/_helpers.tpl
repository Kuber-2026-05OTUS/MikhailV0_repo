{{/* Expand the name of the chart. */}}
{{- define "homework-app.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Create a default fully qualified app name. */}}
{{- define "homework-app.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/* Create chart name and version as used by the chart label. */}}
{{- define "homework-app.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Common labels. */}}
{{- define "homework-app.labels" -}}
{{- with .Values.labels }}
{{- toYaml . }}
{{- end }}
helm.sh/chart: {{ include "homework-app.chart" . }}
{{ include "homework-app.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/* Namespace for namespaced resources. */}}
{{- define "homework-app.namespace" -}}
{{- default .Release.Namespace .Values.namespace }}
{{- end }}

{{/* Selector labels. */}}
{{- define "homework-app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "homework-app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/* Application ServiceAccount name. */}}
{{- define "homework-app.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "homework-app.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/* ConfigMap name. */}}
{{- define "homework-app.configMapName" -}}
{{- default (printf "%s-config" (include "homework-app.fullname" .)) .Values.configMap.name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Init script ConfigMap name. */}}
{{- define "homework-app.initScriptConfigMapName" -}}
{{- default (printf "%s-init-script" (include "homework-app.fullname" .)) .Values.initContainer.scriptConfigMap.name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Application work directory. */}}
{{- define "homework-app.workDir" -}}
{{- .Values.persistence.mountPath | trimSuffix "/" }}
{{- end }}

{{/* Application config directory. */}}
{{- define "homework-app.confDir" -}}
{{- printf "%s/conf" (include "homework-app.workDir" .) }}
{{- end }}

{{/* Application index file path. */}}
{{- define "homework-app.indexFile" -}}
{{- printf "%s/index.html" (include "homework-app.workDir" .) }}
{{- end }}

{{/* PVC name. */}}
{{- define "homework-app.pvcName" -}}
{{- default (printf "%s-pvc" (include "homework-app.fullname" .)) .Values.persistence.name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Gateway name. */}}
{{- define "homework-app.gatewayName" -}}
{{- default (printf "%s-gateway" (include "homework-app.fullname" .)) .Values.gateway.name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* HTTPRoute name. */}}
{{- define "homework-app.httpRouteName" -}}
{{- default (printf "%s-route" (include "homework-app.fullname" .)) .Values.httpRoute.name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Metrics ServiceAccount name. */}}
{{- define "homework-app.metricsServiceAccountName" -}}
{{- default (printf "%s-metrics" (include "homework-app.fullname" .)) .Values.rbac.metricsReader.serviceAccount.name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Pod ServiceAccount name. */}}
{{- define "homework-app.podServiceAccountName" -}}
{{- if .Values.rbac.metricsReader.enabled }}
{{- include "homework-app.metricsServiceAccountName" . }}
{{- else }}
{{- include "homework-app.serviceAccountName" . }}
{{- end }}
{{- end }}

{{/* Metrics ClusterRole name. */}}
{{- define "homework-app.metricsClusterRoleName" -}}
{{- default (printf "%s-metrics-reader" (include "homework-app.fullname" .)) .Values.rbac.metricsReader.clusterRole.name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Metrics ClusterRoleBinding name. */}}
{{- define "homework-app.metricsClusterRoleBindingName" -}}
{{- default (printf "%s-metrics-reader" (include "homework-app.fullname" .)) .Values.rbac.metricsReader.clusterRoleBinding.name | trunc 63 | trimSuffix "-" }}
{{- end }}
