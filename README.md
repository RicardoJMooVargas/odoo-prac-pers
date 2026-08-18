# Odoo Development Project

Entorno Dockerizado para desarrollo y despliegue de módulos Odoo personalizados.

## Estructura

```
.
├── addons/               # Módulos propios (montados en /mnt/extra-addons)
│   └── mi_empresa/       # Módulo de ejemplo
├── config/
│   └── odoo.conf         # Configuración de Odoo
├── docker-compose.yml
├── .env                  # Variables locales (NO se sube al repo)
├── .env.example          # Plantilla de variables de entorno
└── README.md
```

## Inicio rápido

### 1. Configura tus variables de entorno

```ash
cp .env.example .env
# Edita .env con tus credenciales
```

### 2. Levanta el entorno de desarrollo

```bash
docker compose up -d
```

Accede en: **http://localhost:8069**

---

## Modos de ejecución

### Desarrollo (.env)

```env
APP_ENV=develop
ODOO_EXTRA_ARGS=--dev=all
```

- Hot-reload de módulos al guardar cambios
- Assets sin minificar (fácil debug de JS/CSS)
- Modo debug activado automáticamente

### Producción (Dokploy / servidor)

En el panel de Dokploy configura las variables de entorno:

```env
APP_ENV=production
ODOO_EXTRA_ARGS=           # vacío: sin flags de debug
DB_USER=odoo_prod
DB_PASSWORD=TU_PASSWORD_SEGURO
```

---

## Comandos útiles

| Acción | Comando |
|---|---|
| Levantar | docker compose up -d |
| Ver logs | docker compose logs -f odoo |
| Reiniciar Odoo | docker compose restart odoo |
| Actualizar módulo | docker compose exec odoo odoo -u mi_empresa -d odoo --stop-after-init |
| Instalar módulo | docker compose exec odoo odoo -i mi_empresa -d odoo --stop-after-init |
| Bajar todo | docker compose down |
| Limpiar volúmenes | docker compose down -v ⚠️ borra la BD |

---

## Crear un nuevo módulo

```bash
docker compose exec odoo odoo scaffold mi_nuevo_modulo /mnt/extra-addons
```

Esto genera el esqueleto del módulo directamente en ./addons/mi_nuevo_modulo/.

---

## Despliegue en Dokploy

1. Apunta tu repositorio en Dokploy.
2. Configura las variables de entorno en el panel (sin subir .env).
3. Dokploy ejecuta docker compose up -d automáticamente.
