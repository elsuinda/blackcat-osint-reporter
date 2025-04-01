# BLACK CAT - OSINT Reporter

![BLACK CAT Logo](app/static/img/logo.png)

BLACK CAT - OSINT Reporter es una herramienta colaborativa para generación de reportes de inteligencia de fuentes abiertas (OSINT) con integración LDAP/Active Directory.

## Características Principales

- Generación colaborativa de reportes OSINT
- Integración con LDAP/Active Directory
- Exportación a PDF y Word
- Gestión de usuarios y permisos
- Interfaz web responsive
- Sistema de logs y auditoría
- Configuración personalizable

## Requisitos del Sistema

- Python 3.8+
- MariaDB/MySQL
- LDAP (opcional)
- Nginx (para producción)

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/elsuinda/blackcat-osint-reporter.git
cd blackcat-osint-reporter
```

## Configuración
1. Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:
```
SECRET_KEY=tu_clave_secreta
DATABASE_URL=mysql+pymysql://usuario:contraseña@localhost/nombre_bd
LDAP_SERVER=ldap://servidor-ldap
LDAP_BIND_PASSWORD=contraseña_ldap
FLASK_PORT=5000
USE_SSL=true
```
2. Para habilitar HTTPS, configura `USE_SSL=true`.

## Usuario Predeterminado
Al iniciar el programa por primera vez, se creará automáticamente un usuario administrador con las siguientes credenciales:

- **Usuario**: `admin`
- **Contraseña**: `SecretPassword`

Este usuario tiene permisos para personalizar el programa, configurar LDAP y gestionar otros usuarios. Se recomienda cambiar la contraseña después de la instalación.

## Personalización
1. **Logos y Favicon**: Reemplaza los archivos en `app/static/img/` con tus propios logos y favicon.
2. **Sonidos**: Coloca archivos `.mp3` o `.wav` en la carpeta `media/` para personalizar los sonidos de exportación.
