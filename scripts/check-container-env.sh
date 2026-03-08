#!/bin/bash
# Check current environment variables in Azure Container App

set -e

# Configuration - UPDATE THESE VALUES
RESOURCE_GROUP="feedbackforge-rg"  # Replace with your resource group name
CONTAINER_APP_NAME="feedbackforge-backend"

# Colors for output
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${YELLOW}================================${NC}"
echo -e "${YELLOW}Current Environment Variables${NC}"
echo -e "${YELLOW}================================${NC}"
echo -e "${YELLOW}Resource Group:${NC} $RESOURCE_GROUP"
echo -e "${YELLOW}Container App:${NC} $CONTAINER_APP_NAME"
echo -e "${YELLOW}================================${NC}"
echo ""

# Get environment variables
az containerapp show \
    --name "$CONTAINER_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query "properties.template.containers[0].env" \
    --output table

echo ""
echo -e "${GREEN}To update variables, run: ./scripts/set-container-env.sh${NC}"
