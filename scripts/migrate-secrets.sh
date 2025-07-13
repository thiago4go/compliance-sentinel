#!/bin/bash

# Migration script to secure exposed credentials
set -e

echo "🔄 Migrating exposed credentials to secure storage..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to mask sensitive values
mask_secret() {
    local secret="$1"
    local length=${#secret}
    if [ $length -gt 8 ]; then
        echo "${secret:0:4}****${secret: -4}"
    else
        echo "****"
    fi
}

# Check for exposed credentials in specific files
EXPOSED_FILES=(
    ".amazonq/mcp.json"
    ".env"
    "services/adaptive-interface/.env"
    "services/harvester/.env"
)

echo "🔍 Scanning for exposed credentials..."

FOUND_ISSUES=false

for file in "${EXPOSED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "📁 Checking: $file"
        
        # Check for PostgreSQL credentials
        if grep -q "PG_PASSWORD.*npg_" "$file" 2>/dev/null; then
            echo -e "${RED}❌ Found exposed PG_PASSWORD in $file${NC}"
            FOUND_ISSUES=true
        fi
        
        if grep -q "PG_HOST.*ep-.*\.aws\.neon\.tech" "$file" 2>/dev/null; then
            echo -e "${RED}❌ Found exposed PG_HOST in $file${NC}"
            FOUND_ISSUES=true
        fi
        
        # Check for OpenAI keys
        if grep -q "sk-[a-zA-Z0-9-_]\{20,\}" "$file" 2>/dev/null; then
            echo -e "${RED}❌ Found exposed OpenAI API key in $file${NC}"
            FOUND_ISSUES=true
        fi
        
        # Check for other API keys
        if grep -q "API_KEY.*['\"][a-zA-Z0-9-_]\{20,\}['\"]" "$file" 2>/dev/null; then
            echo -e "${RED}❌ Found exposed API key in $file${NC}"
            FOUND_ISSUES=true
        fi
    fi
done

if [ "$FOUND_ISSUES" = true ]; then
    echo ""
    echo -e "${YELLOW}🚨 CRITICAL: Exposed credentials found!${NC}"
    echo ""
    echo "🛠️ IMMEDIATE ACTIONS REQUIRED:"
    echo ""
    echo "1️⃣ REVOKE compromised credentials:"
    echo "   • Regenerate OpenAI API keys"
    echo "   • Reset PostgreSQL passwords"
    echo "   • Rotate any other exposed secrets"
    echo ""
    echo "2️⃣ SECURE storage setup:"
    
    # Extract credentials for migration (if user confirms)
    read -p "🔒 Do you want to extract credentials to secure storage? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Create secure secrets directory
        mkdir -p services/adaptive-interface/secrets
        
        # Create secrets.json template
        cat > services/adaptive-interface/secrets/secrets.json << 'EOF'
{
  "openai": {
    "api_key": "REPLACE_WITH_NEW_OPENAI_KEY",
    "model": "gpt-4.1-nano"
  },
  "database": {
    "pg_host": "REPLACE_WITH_NEW_PG_HOST",
    "pg_password": "REPLACE_WITH_NEW_PG_PASSWORD",
    "pg_user": "postgres",
    "pg_database": "compliance_db",
    "pg_port": "5432"
  },
  "mcp": {
    "rag_memory_url": "http://localhost:3001",
    "duckduckgo_url": "http://localhost:3002",
    "context7_url": "http://localhost:3003",
    "deepwiki_url": "http://localhost:3004"
  }
}
EOF
        
        # Set proper permissions
        chmod 600 services/adaptive-interface/secrets/secrets.json
        
        echo -e "${GREEN}✅ Created secure secrets template${NC}"
        echo "📝 Edit: services/adaptive-interface/secrets/secrets.json"
        echo ""
    fi
    
    echo "3️⃣ CLEAN exposed files:"
    echo "   • Remove credentials from .amazonq/mcp.json"
    echo "   • Replace with environment variable references"
    echo "   • Add files to .gitignore if not already there"
    echo ""
    echo "4️⃣ PREVENT future exposure:"
    echo "   • Install pre-commit hooks: pre-commit install"
    echo "   • Test with: git add . && git commit -m 'test'"
    echo ""
    echo "5️⃣ UPDATE git history (if already committed):"
    echo "   • Use git-filter-repo or BFG to clean history"
    echo "   • Force push to remove exposed credentials"
    echo ""
    
    # Clean exposed files automatically
    read -p "🧹 Do you want to automatically clean exposed files? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🧹 Cleaning exposed credentials..."
        
        # Clean .amazonq/mcp.json
        if [ -f ".amazonq/mcp.json" ]; then
            # Replace exposed values with environment variable placeholders
            sed -i.bak 's/"PG_PASSWORD": "[^"]*"/"PG_PASSWORD": "${PG_PASSWORD}"/g' .amazonq/mcp.json
            sed -i.bak 's/"PG_HOST": "[^"]*"/"PG_HOST": "${PG_HOST}"/g' .amazonq/mcp.json
            sed -i.bak 's/sk-[a-zA-Z0-9-_]*/${OPENAI_API_KEY}/g' .amazonq/mcp.json
            echo -e "${GREEN}✅ Cleaned .amazonq/mcp.json${NC}"
        fi
        
        # Clean .env files
        for env_file in .env services/adaptive-interface/.env services/harvester/.env; do
            if [ -f "$env_file" ]; then
                # Comment out exposed credentials
                sed -i.bak 's/^OPENAI_API_KEY=sk-/#OPENAI_API_KEY=sk-/g' "$env_file"
                sed -i.bak 's/^PG_PASSWORD=/#PG_PASSWORD=/g' "$env_file"
                sed -i.bak 's/^PG_HOST=.*neon\.tech/#PG_HOST=/g' "$env_file"
                echo -e "${GREEN}✅ Cleaned $env_file${NC}"
            fi
        done
        
        echo -e "${GREEN}✅ Credential cleanup complete${NC}"
    fi
    
else
    echo -e "${GREEN}✅ No exposed credentials found${NC}"
fi

echo ""
echo "🛡️ SECURITY BEST PRACTICES:"
echo ""
echo "FREE SECRET STORAGE OPTIONS:"
echo "• 🏠 Local: File-based secrets (secrets/secrets.json)"
echo "• ☸️  Kubernetes: Built-in secret management"
echo "• 🔒 Git-crypt: Encrypted files in git"
echo "• 🌩️  Cloud: Azure Key Vault free tier"
echo "• 🏢 Self-hosted: HashiCorp Vault"
echo ""
echo "DAPR SECRET STORES (configured in dapr/components/secrets.yaml):"
echo "• local-secret-store (development)"
echo "• kubernetes-secret-store (production)"
echo "• vault-secret-store (enterprise)"
echo ""
echo "🔗 Next steps:"
echo "1. Run: cd services/adaptive-interface && ./scripts/setup-secrets.sh"
echo "2. Test: pre-commit run --all-files"
echo "3. Verify: git status (should show no sensitive files)"
echo ""
echo -e "${GREEN}🎉 Security migration guide complete!${NC}"