# 🚀 CI/CD de una aplicación Flask con Docker, GitHub Actions y Microsoft Azure

Implementación de un pipeline de **Integración Continua y Despliegue Continuo (CI/CD)** para automatizar la construcción, publicación y despliegue de una aplicación web desarrollada con Python y Flask, utilizando Docker, GitHub Actions y Microsoft Azure.

El proyecto incorpora autenticación federada mediante **OpenID Connect (OIDC)**, administración de identidades con Microsoft Entra ID y control de acceso mediante RBAC, aplicando el principio de mínimo privilegio.

## 🛠️ Tecnologías utilizadas

| Tecnología | Función |
|---|---|
| Python / Flask | Desarrollo de la aplicación web |
| Docker | Contenerización de la aplicación |
| Docker Buildx | Construcción de imágenes Docker |
| GitHub Actions | Automatización del pipeline CI/CD |
| Azure Container Registry (ACR) | Almacenamiento privado de imágenes Docker |
| Azure App Service | Alojamiento y ejecución de la aplicación |
| Microsoft Entra ID | Administración de identidades |
| OpenID Connect (OIDC) | Autenticación federada sin contraseñas permanentes |
| Azure IAM / RBAC | Gestión de roles y permisos |
| Azure Managed Identity | Autenticación de App Service frente a ACR |

## 🏗️ Arquitectura del proyecto

```text
                  DESARROLLADOR
                       |
                   git push
                       |
                       v
                GITHUB REPOSITORY
                       |
                       v
                 GITHUB ACTIONS
                       |
              +--------+--------+
              |                 |
              v                 v
        BUILD DOCKER       LOGIN AZURE
              |                 |
              |             OIDC TOKEN
              |                 |
              |                 v
              |         MICROSOFT ENTRA ID
              |                 |
              |          SERVICE PRINCIPAL
              |                 |
              +--------+--------+
                       |
                       v
             AZURE CONTAINER REGISTRY
                     AcrPush
                       |
                       | Imagen Docker
                       v
                AZURE APP SERVICE
                Website Contributor
                       |
              Managed Identity
                       |
                     AcrPull
                       |
                       v
              APLICACIÓN FLASK
```

**Flujo general:** GitHub Actions construye y publica la imagen Docker en ACR. Posteriormente, actualiza Azure App Service para desplegar la nueva versión. App Service utiliza su propia identidad administrada para descargar la imagen privada desde ACR.

## ⚙️ Funcionamiento del pipeline CI/CD

El workflow se encuentra en:

`.github/workflows/ci-cd.yml`

Se ejecuta automáticamente cuando se realiza un `push` a la rama `main`.

### Job 1: Build

1. Descarga el código fuente mediante `actions/checkout`.
2. Configura Docker Buildx.
3. Se autentica en Microsoft Azure mediante OIDC.
4. Obtiene un token temporal de acceso a ACR.
5. Inicia sesión en Azure Container Registry.
6. Construye la imagen Docker utilizando el Dockerfile.
7. Publica la imagen con dos etiquetas:
   - `latest`: última imagen publicada.
   - `vN`: versión identificada por el número de ejecución del workflow.
8. Utiliza mecanismos de caché de Docker para optimizar construcciones posteriores.

**Registro de imágenes:**

```text
acronaldapp.azurecr.io/repo/flask-app
```

### Job 2: Deploy

El job `deploy` depende de la finalización exitosa de `build`, mediante `needs: build`.

1. Inicia una nueva sesión autenticada en Azure mediante OIDC.
2. Actualiza Azure App Service con la imagen publicada en ACR.
3. App Service descarga la imagen utilizando su Managed Identity.
4. El contenedor ejecuta la aplicación Flask.

## 🐳 Dockerización de la aplicación

El proyecto utiliza un Dockerfile con **Multi-stage Build**, separando la instalación de dependencias de la imagen final de ejecución.

### Stage 1: Builder

- Utiliza Python Slim.
- Crea un entorno virtual en `/opt/venv`.
- Instala las dependencias definidas en `requirements.txt`.
- Aprovecha la caché de capas de Docker.

### Stage 2: Runner

- Copia el entorno virtual desde el stage anterior.
- Ejecuta la aplicación con un usuario sin privilegios (`appuser`).
- Expone el puerto `5000`.
- Incluye un healthcheck mediante Python.
- Utiliza Gunicorn como servidor WSGI.

Esta estructura permite separar el proceso de construcción del entorno de ejecución y aplicar mejores prácticas de seguridad en contenedores.

## 🔐 Seguridad: OIDC, IAM y RBAC

La autenticación entre GitHub Actions y Azure se realiza mediante **OIDC**, evitando almacenar contraseñas permanentes de un Service Principal en GitHub.

Se configuraron los siguientes componentes:

- **App Registration:** registro de la aplicación en Microsoft Entra ID.
- **Service Principal:** identidad utilizada por GitHub Actions para acceder a Azure.
- **Federated Credential:** relación de confianza entre el repositorio de GitHub y Microsoft Entra ID.
- **Managed Identity:** identidad administrada utilizada por Azure App Service.
- **IAM / RBAC:** asignación de permisos específicos según cada operación.

### Roles configurados

| Identidad | Rol | Alcance | Función |
|---|---|---|---|
| Service Principal de GitHub | `AcrPush` | Azure Container Registry | Publicar imágenes Docker |
| Service Principal de GitHub | `Website Contributor` | Azure App Service | Actualizar el despliegue |
| Managed Identity de App Service | `AcrPull` | Azure Container Registry | Descargar imágenes privadas |

Se aplicó el **principio de mínimo privilegio**, evitando otorgar permisos de Contributor sobre toda la suscripción.

## 🔧 Variables de GitHub Actions

Las variables se configuran en:

**GitHub → Settings → Secrets and variables → Actions → Variables**

| Variable | Descripción |
|---|---|
| `AZURE_CLIENT_ID` | Client ID de la App Registration |
| `AZURE_TENANT_ID` | Identificador del tenant de Microsoft Entra ID |
| `AZURE_SUBSCRIPTION_ID` | Identificador de la suscripción de Azure |
| `ACR_NAME` | Nombre del Azure Container Registry |
| `AZURE_WEBAPP_NAME` | Nombre del Azure App Service |

La imagen se define en el workflow:

```yaml
env:
  IMAGE_NAME: ${{ vars.ACR_NAME }}.azurecr.io/repo/flask-app
```

Para permitir la autenticación OIDC, el workflow requiere:

```yaml
permissions:
  contents: read
  id-token: write
```

## 🧩 Problemas encontrados y soluciones

### Error de autenticación OIDC: AADSTS700213

**Problema:** Microsoft Entra ID rechazaba el token federado presentado por GitHub Actions.

**Causa:** El `subject` del token de GitHub no coincidía exactamente con el registrado en la Federated Credential.

**Solución:** Se actualizó la credencial federada en Microsoft Entra ID para que coincidiera con el identificador del repositorio y la rama `main`.

**Aprendizaje:** La federación OIDC requiere coincidencia entre el emisor, el sujeto y la audiencia del token y la credencial configurada.

### Restricciones regionales de Azure for Students

**Problema:** La suscripción bloqueaba la creación de determinados recursos en algunas regiones de Azure.

**Solución:** Se identificaron las regiones permitidas por la política de la suscripción y se utilizaron ubicaciones compatibles.

**Aprendizaje:** Las políticas de Azure pueden limitar la creación de recursos independientemente de la configuración de la aplicación.

## 📚 Aprendizajes adquiridos

Durante este proyecto reforcé conocimientos prácticos en:

- Diseño e implementación de pipelines CI/CD con GitHub Actions.
- Construcción y publicación de imágenes Docker.
- Uso de Multi-stage Builds y ejecución de contenedores sin privilegios de root.
- Despliegue de aplicaciones contenerizadas en Azure App Service.
- Administración de imágenes privadas con Azure Container Registry.
- Autenticación federada con OIDC y Microsoft Entra ID.
- Configuración de Service Principals y Managed Identities.
- Gestión de permisos mediante IAM y RBAC.
- Diagnóstico de errores de autenticación y configuración Cloud.


