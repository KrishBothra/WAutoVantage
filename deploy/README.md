# BounceCast MiniKube Deployment Guide

<img src="Screencast from 04-30-2025 01_07_58 PM.gif" width="700">

## Prerequisites
- Install [Docker](https://docs.docker.com/engine/install/ubuntu/)
- Install [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/)
- Install [Minikube](https://minikube.sigs.k8s.io/docs/start/?arch=%2Flinux%2Fx86-64%2Fstable%2Fbinary+download)


## Build Docker Image inside Minikube

```bash
minikube start --driver=docker
```
```bash
eval $(minikube docker-env)
docker build -t bounce-cast-server:latest .
```

## Apply Kubernetes Deployment and Service

```bash
kubectl apply -f deploy/deployment.yaml
kubectl apply -f deploy/service.yaml
```

## Check if pods running and service port is correct
```bash
kubectl get pods
kubectl get svc my-service
```

## Launch Chrome WebApp:

```bash
MINIKUBE_IP=$(minikube ip)
google-chrome   --enable-quic   --enable-experimental-web-platform-features   --ignore-certificate-errors   --ignore-certificate-errors-spki-list=ggR1vjmsgl5RdfYS3f5C2nYyZ3LRrjfOyD/Va/JLcXQ=   --origin-to-force-quic-on=${MINIKUBE_IP}:30403   https://${MINIKUBE_IP}:30403/
```
