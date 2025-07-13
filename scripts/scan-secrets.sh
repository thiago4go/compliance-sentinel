#!/bin/bash

# Custom secret scanner for pre-commit hook
set -e

echo "🔍 Running custom secret scan..."

# Patterns to detect
PATTERNS=(
    "PG_PASSWORD.*['\"].*['\"]"
    "PG_HOST.*ep-.*\.aws\.neon\.tech"
    "sk-[a-zA-Z0-9_-]{20,}"
    "API_KEY.*['\"][a-zA-Z0-9_-]{20,}['\"]"
    "SECRET.*['\"][a-zA-Z0-9_-]{20,}['\"]"
    "TOKEN.*['\"][a-zA-Z0-9_-]{20,}['\"]"
    "PASSWORD.*['\"][^'\"]{8,}['\"]"
    "aws_access_key_id"
    "aws_secret_access_key"
    "private_key"
    "-----BEGIN.*PRIVATE KEY-----"
)

# Files to check (staged for commit)
FILES=$(git diff --cached --name-only --diff-filter=ACM)

if [ -z "$FILES" ]; then
    echo "✅ No staged files to scan"
    exit 0
fi

VIOLATIONS=0

# Files to exclude from scanning (security scripts themselves)
EXCLUDE_FILES=(
    "scripts/scan-secrets.sh"
    "scripts/migrate-secrets.sh"
    "services/adaptive-interface/scripts/setup-secrets.sh"
    ".github/workflows/security-scan.yml"
)

for file in $FILES; do
    if [ -f "$file" ]; then
        # Skip security scripts themselves
        skip_file=false
        for exclude in "${EXCLUDE_FILES[@]}"; do
            if [[ "$file" == "$exclude" ]]; then
                skip_file=true
                break
            fi
        done
        
        if [ "$skip_file" = true ]; then
            echo "Skipping security script: $file"
            continue
        fi
        
        echo "Scanning: $file"

        for pattern in "${PATTERNS[@]}"; do
            if grep -E "$pattern" "$file" >/dev/null 2>&1; then
                echo "❌ SECURITY VIOLATION in $file:"
                echo "   Pattern detected: $pattern"
                grep -n -E "$pattern" "$file" || true
                echo ""
                VIOLATIONS=$((VIOLATIONS + 1))
            fi
        done
    fi
done

if [ $VIOLATIONS -gt 0 ]; then
    echo ""
    echo "🚫 COMMIT BLOCKED: $VIOLATIONS security violations found!"
    echo ""
    echo "Solutions:"
    echo "1. Remove hardcoded secrets from code"
    echo "2. Use environment variables or secret stores"
    echo "3. Add sensitive files to .gitignore"
    echo "4. Use git-crypt for encrypted storage"
    echo ""
    exit 1
fi

echo "✅ No secrets detected - commit allowed"
exit 0
