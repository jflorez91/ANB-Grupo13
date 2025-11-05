### Configuración para despliegue de NGINX

## Iniciar como super usuario
```bash
sudo su -
```

## Crear la red externa (solo una vez, si aún no existe)
```bash
docker network create anb-network
```

## Conecta tu contenedor de API a esa red si aún no lo está
```bash
docker network connect --alias api anb-network <nombre_o_id_contenedor_api>
```

## Crea directorios de montajes:
```bash
mkdir -p ANB-Grupo13/aplication/nginx/storage
mkdir -p ANB-Grupo13/aplication/nginx/logs/nginx
```

## Desde ANB-Grupo13/aplication/nginx:
```bash
docker compose -f ./Docker-compose.yml -p nginx up -d --build
```
