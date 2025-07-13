#!/bin/bash

# Setup script for secure secret management
set -e

echo "🔐 Setting up secure secret management..."

# Create secrets directory
mkdir -p secrets

# Check if secrets.json exists
if [ ! -f "secrets/secrets.json" ]; then
    echo "📝 Creating secrets.json from template..."
    cp secrets/secrets.json.example secrets/secrets.json
    echo "⚠️  Please edit secrets/secrets.json with your actual credentials"
    echo "   File location: $(pwd)/secrets/secrets.json"
fi

# Setup for different environments
echo "🌍 Choose your deployment environment:"
echo "1) Local Development (file-based secrets)"
echo "2) Kubernetes (k8s secrets)"
echo "3) Cloud (Vault/Azure Key Vault)"
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo "🏠 Setting up local development..."
        # Ensure secrets.json has proper permissions
        chmod 600 secrets/secrets.json
        echo "✅ Local secrets configured"
        echo "📂 Edit: secrets/secrets.json"
        ;;
    2)
        echo "☸️  Setting up Kubernetes secrets..."

        # Check if kubectl is available
        if ! command -v kubectl &> /dev/null; then
            echo "❌ kubectl not found. Please install kubectl first."
            exit 1
        fi

        # Create namespace if it doesn't exist
        kubectl create namespace compliance-sentinel --dry-run=client -o yaml | kubectl apply -f -

        # Create secrets from file
        if [ -f "secrets/secrets.json" ]; then
            echo "Creating Kubernetes secrets..."

            # Extract and create individual secrets
            OPENAI_KEY=$(jq -r '.openai.api_key' secrets/secrets.json)
            PG_HOST=$(jq -r '.database.pg_host' secrets/secrets.json)
            DB_PASS=$(jq -r '.database.pg_password' secrets/secrets.json)

            kubectl create secret generic openai-secret \
                --from-literal=api-key="$OPENAI_KEY" \
                -n compliance-sentinel --dry-run=client -o yaml | kubectl apply -f -

            kubectl create secret generic postgres-secret \
                --from-literal=host="$PG_HOST" \
                --from-literal=password="$DB_PASS" \
                -n compliance-sentinel --dry-run=client -o yaml | kubectl apply -f -

            echo "✅ Kubernetes secrets created"
        else
            echo "❌ secrets/secrets.json not found"
            exit 1
        fi
        ;;
    3)
        echo "☁️  Setting up cloud secret store..."
        echo "📖 Please configure your cloud provider:"
        echo "   - Azure Key Vault: Update dapr/components/secrets.yaml"
        echo "   - AWS Secrets Manager: Add AWS component"
        echo "   - HashiCorp Vault: Configure vault endpoint"
        echo "✅ Cloud setup instructions provided"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

# Install pre-commit if not present
if ! command -v pre-commit &> /dev/null; then
    echo "📋 Installing pre-commit..."
    pip install pre-commit
fi

# Setup pre-commit hooks
echo "🪝 Setting up pre-commit hooks..."
pre-commit install

echo ""
echo "🎉 Secret management setup complete!"
echo ""
echo "📚 Next steps:"
echo "1. Edit secrets/secrets.json with your actual credentials"
echo "2. Test with: dapr run --app-id test --components-path ./dapr/components"
echo "3. Never commit secrets/secrets.json to git"
echo ""
echo "🔒 Security features enabled:"
echo "✅ Pre-commit hooks for secret detection"
echo "✅ .gitignore rules for sensitive files"
echo "✅ CI/CD secret scanning"
echo "✅ Dapr secret store integration"
