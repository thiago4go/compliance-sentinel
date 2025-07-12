#!/bin/bash

# Deployment script for Compliance Sentinel MCP Server
set -e

echo "🚀 Deploying Compliance Sentinel MCP Server to Kubernetes..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed or not in PATH"
    exit 1
fi

# Check if we can connect to the cluster
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster"
    exit 1
fi

echo "✅ Connected to Kubernetes cluster"

# Apply the deployment
echo "📦 Applying Kubernetes manifests..."
kubectl apply -f k8s-deployment.yaml

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/compliance-sentinel-mcp

# Get deployment status
echo "📊 Deployment Status:"
kubectl get deployment compliance-sentinel-mcp
kubectl get pods -l app=compliance-sentinel-mcp
kubectl get service compliance-sentinel-mcp-service

# Show logs from one pod
echo "📝 Recent logs from one pod:"
POD_NAME=$(kubectl get pods -l app=compliance-sentinel-mcp -o jsonpath='{.items[0].metadata.name}')
kubectl logs $POD_NAME --tail=10

echo "✅ Deployment completed successfully!"
echo ""
echo "🔗 To access the service:"
echo "   Port forward: kubectl port-forward service/compliance-sentinel-mcp-service 8080:80"
echo "   Then visit: http://localhost:8080"
echo ""
echo "📊 To check status:"
echo "   kubectl get pods -l app=compliance-sentinel-mcp"
echo "   kubectl logs -l app=compliance-sentinel-mcp"
echo ""
echo "🗑️  To delete:"
echo "   kubectl delete -f k8s-deployment.yaml"
