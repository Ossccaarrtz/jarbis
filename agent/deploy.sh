#!/usr/bin/env bash
# Empaqueta y despliega ambos Lambdas.
# Uso: bash deploy.sh
# Requisito: AWS CLI configurado, ambas funciones Lambda ya creadas.

set -e

HANDLER_FUNCTION="jarbis-handler"
AGENT_FUNCTION="jarbis-agent"
REGION="us-east-1"
BUILD_DIR="build"
ZIP_FILE="jarbis.zip"

echo "==> Limpiando build anterior..."
rm -rf "$BUILD_DIR" "$ZIP_FILE"
mkdir "$BUILD_DIR"

echo "==> Instalando dependencias..."
pip install -r requirements.txt -t "$BUILD_DIR" --quiet

echo "==> Copiando fuentes..."
cp *.py "$BUILD_DIR/"
cp -r tools "$BUILD_DIR/tools"

echo "==> Creando zip..."
cd "$BUILD_DIR"
zip -r "../$ZIP_FILE" . -q
cd ..

echo "==> Desplegando $HANDLER_FUNCTION..."
aws lambda update-function-code \
  --function-name "$HANDLER_FUNCTION" \
  --zip-file "fileb://$ZIP_FILE" \
  --region "$REGION" \
  --output text --query "FunctionName"

echo "==> Desplegando $AGENT_FUNCTION..."
aws lambda update-function-code \
  --function-name "$AGENT_FUNCTION" \
  --zip-file "fileb://$ZIP_FILE" \
  --region "$REGION" \
  --output text --query "FunctionName"

echo "==> Listo."
