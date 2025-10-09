#!/bin/bash

# Sync local src/pod folder to Kubernetes pod
# Usage: ./sync-to-k8s.sh [pod-name] [namespace]

set -e

# Default values
DEFAULT_NAMESPACE="chaos-ops"
DEFAULT_POD_PREFIX="chaos-platform"

# Parse arguments
POD_NAME=${1:-""}
NAMESPACE=${2:-$DEFAULT_NAMESPACE}

# Function to get the current pod name
get_pod_name() {
    if [ -n "$POD_NAME" ]; then
        echo "$POD_NAME"
        return
    fi
    
    echo "🔍 Finding chaos-platform pod in namespace $NAMESPACE..."
    POD_NAME=$(kubectl get pods -n $NAMESPACE -l app.kubernetes.io/name=chaos-platform -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -z "$POD_NAME" ]; then
        echo "❌ No chaos-platform pod found in namespace $NAMESPACE"
        echo "Available pods:"
        kubectl get pods -n $NAMESPACE
        exit 1
    fi
    
    echo "📦 Found pod: $POD_NAME"
    echo "$POD_NAME"
}

# Function to sync files
sync_files() {
    local pod_name=$1
    local namespace=$2
    
    echo "🚀 Syncing src/pod folder to pod $pod_name in namespace $namespace..."
    
    # Check if local src/pod exists
    if [ ! -d "src/pod" ]; then
        echo "❌ Local src/pod directory not found. Please run this script from the project root."
        exit 1
    fi
    
    # Create a temporary tar file
    echo "📦 Creating archive of src/pod..."
    tar -czf /tmp/pod-sync.tar.gz -C src pod/
    
    # Copy to pod
    echo "📤 Copying files to pod..."
    kubectl cp /tmp/pod-sync.tar.gz $namespace/$pod_name:/tmp/pod-sync.tar.gz
    
    # Extract in pod
    echo "📂 Extracting files in pod..."
    kubectl exec -n $namespace $pod_name -- bash -c "
        cd /opt/airflow/src && 
        rm -rf pod_backup && 
        cp -r pod pod_backup 2>/dev/null || true &&
        tar -xzf /tmp/pod-sync.tar.gz && 
        rm /tmp/pod-sync.tar.gz &&
        echo '✅ Files extracted successfully'
    "
    
    # Cleanup local temp file
    rm -f /tmp/pod-sync.tar.gz
    
    echo "🎉 Sync completed successfully!"
    echo "📁 Files are now available at /opt/airflow/src/pod in the pod"
}

# Function to watch for changes and auto-sync
watch_and_sync() {
    local pod_name=$1
    local namespace=$2
    
    echo "👀 Starting file watcher for src/pod..."
    echo "Press Ctrl+C to stop watching"
    
    if ! command -v inotifywait &> /dev/null; then
        echo "⚠️  inotifywait not found. Installing inotify-tools..."
        echo "Run: sudo apt-get install inotify-tools (Ubuntu/Debian) or brew install fswatch (macOS)"
        exit 1
    fi
    
    while inotifywait -r -e modify,create,delete,move src/pod/; do
        echo "🔄 Changes detected, syncing..."
        sync_files $pod_name $namespace
        echo "⏳ Waiting for next change..."
    done
}

# Main execution
main() {
    echo "🚀 Kubernetes Pod Sync Tool"
    echo "=========================="
    
    POD_NAME=$(get_pod_name)
    
    case "${3:-sync}" in
        "watch")
            watch_and_sync $POD_NAME $NAMESPACE
            ;;
        "sync"|*)
            sync_files $POD_NAME $NAMESPACE
            ;;
    esac
}

# Show usage if help requested
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "Usage: $0 [pod-name] [namespace] [action]"
    echo ""
    echo "Arguments:"
    echo "  pod-name   : Kubernetes pod name (auto-detected if not provided)"
    echo "  namespace  : Kubernetes namespace (default: chaos-ops)"
    echo "  action     : 'sync' (default) or 'watch' for continuous sync"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Auto-detect pod and sync once"
    echo "  $0 chaos-platform-xxx chaos-ops      # Sync to specific pod"
    echo "  $0 '' chaos-ops watch                # Auto-detect pod and watch for changes"
    exit 0
fi

main "$@"
