#!/bin/bash

# Redeploy chaos-platform with local folder mounting
set -e

NAMESPACE="chaos-ops"
RELEASE_NAME="chaos-platform"
CHART_PATH="./helm/chaos-platform"

echo "🚀 Redeploying chaos-platform with local folder mounting..."

# Check if namespace exists
if ! kubectl get namespace $NAMESPACE &> /dev/null; then
    echo "📁 Creating namespace $NAMESPACE..."
    kubectl create namespace $NAMESPACE
fi

# Upgrade/Install the Helm chart
echo "⚡ Upgrading Helm release..."
helm upgrade --install $RELEASE_NAME $CHART_PATH \
    --namespace $NAMESPACE \
    --set localDevelopment.enabled=true \
    --set localDevelopment.hostPath="/home/priyanshupatel/fault-injector" \
    --wait \
    --timeout=300s

echo "✅ Deployment completed!"

# Show pod status
echo "📦 Pod status:"
kubectl get pods -n $NAMESPACE -l app.kubernetes.io/name=chaos-platform

# Get the new pod name
POD_NAME=$(kubectl get pods -n $NAMESPACE -l app.kubernetes.io/name=chaos-platform -o jsonpath='{.items[0].metadata.name}')
echo "🎯 New pod name: $POD_NAME"

# Verify the mount
echo "🔍 Verifying local folder mount..."
kubectl exec -n $NAMESPACE $POD_NAME -- ls -la /opt/airflow/src/pod/ | head -10

echo "🎉 Local src/pod folder is now mounted in the Kubernetes pod!"
echo "📝 Any changes to your local src/pod will be immediately reflected in the pod."
