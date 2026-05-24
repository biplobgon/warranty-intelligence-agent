{{/* Common labels */}}
{{- define "warranty-intel.labels" -}}
app.kubernetes.io/name: {{ include "warranty-intel.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: warranty-intelligence-agent
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
{{- end -}}

{{- define "warranty-intel.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "warranty-intel.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name (include "warranty-intel.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "warranty-intel.selectorLabels" -}}
app.kubernetes.io/name: {{ include "warranty-intel.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
