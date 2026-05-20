#!/usr/bin/env bash
# Empaqueta y despliega los tres Lambdas de Jarbis.
# Uso: bash deploy.sh
# Requisito: AWS CLI configurado, funciones Lambda ya creadas.

set -e

HANDLER_FUNCTION="jarbis-handler"
AGENT_FUNCTION="jarbis-agent"
DISPATCHER_FUNCTION="jarbis-reminder-dispatcher"
REGION="us-east-1"
BUILD_DIR="build"
ZIP_FILE="jarbis.zip"

echo "==> Limpiando build anterior..."
python -c "import shutil, os; shutil.rmtree('$BUILD_DIR', ignore_errors=True); os.makedirs('$BUILD_DIR')"
rm -f "$ZIP_FILE"

echo "==> Instalando dependencias con Docker (Linux x86_64)..."
WIN_PWD=$(pwd -W)
MSYS_NO_PATHCONV=1 docker run --rm --entrypoint pip \
  -v "${WIN_PWD}/requirements.txt:/requirements.txt" \
  -v "${WIN_PWD}/${BUILD_DIR}:/build" \
  public.ecr.aws/lambda/python:3.12 \
  install -r /requirements.txt -t /build --quiet

echo "==> Copiando fuentes..."
cp *.py "$BUILD_DIR/"
cp -r tools "$BUILD_DIR/tools"

echo "==> Creando zip..."
python -c "
import zipfile, os, sys
build = sys.argv[1]
out = sys.argv[2]
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(build):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for file in files:
            if file.endswith('.pyc'):
                continue
            full = os.path.join(root, file)
            arcname = os.path.relpath(full, build)
            zf.write(full, arcname)
print('Zip creado:', out)
" "$BUILD_DIR" "$ZIP_FILE"

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

echo "==> Desplegando $DISPATCHER_FUNCTION..."
aws lambda update-function-code \
  --function-name "$DISPATCHER_FUNCTION" \
  --zip-file "fileb://$ZIP_FILE" \
  --region "$REGION" \
  --output text --query "FunctionName"

echo "==> Listo."
