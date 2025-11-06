FROM nginx:1.25-alpine

# (Opcional) utilidades básicas
RUN apk add --no-cache curl

# Copiar el nginx.conf al lugar correcto
COPY nginx.conf /etc/nginx/nginx.conf

# Crear directorios esperados
RUN mkdir -p /var/log/nginx /storage

# Ejecutar nginx en foreground
CMD ["nginx", "-g", "daemon off;"]