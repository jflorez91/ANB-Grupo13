# Grupo 13

## 👥 Equipo de desarrollo 

| Nombre | Correo |
|--------|--------|
|Jerson Alonso Florez Rojas | ja.florezr1@uniandes.edu.co|
|Esteban Leal Barrios | e.leal1@uniandes.edu.co |
|Juan David Castañeda Aguirre| jd.castanedaa1@uniandes.edu.co|

## Video de entrega
- **Semana 7 y 8**
  
[https://www.youtube.com/watch?v=-bOvWrIPFUE](https://youtu.be/emWp7y9celw)

## Documentación entrega 5
Para esta entrega se implementaron los servicios de autoescalado para los ambientes de tipo web y los ambientes de tipo worker, utilizando grupos de Auto Scaling.
Además, se implementó un balanceador de carga para el grupo de la capa web, con el fin de distribuir las solicitudes y controlar la ejecución de los servicios API que realizan el guardado de datos en el sistema.

Todo lo anterior está integrado con una instancia EC2 que cumple la función de gateway mediante NGINX, la cual constituye el punto de entrada de las peticiones que llegan al servidor.

<img width="335" height="380" alt="image" src="https://github.com/user-attachments/assets/7df13064-cbb9-4d9a-9d8c-1f33dda48a56" />

A nivel de bases de datos se implementó el servicio de Amazon RDS con un motor MySQL, que permite almacenar la información de cada una de las peticiones recibidas desde la capa web.

Dado que es necesario contar con un servicio para alojar los videos cargados y procesados, se implementó un bucket de Amazon S3, el cual permite mantener los servicios conectados y centralizar el almacenamiento de estos archivos.

Ambos servicios son de gran importancia para el correcto funcionamiento de la aplicación.

### Nuevas funcionalidades

Como nuevos servicios implementados, contamos con Amazon Simple Queue Service (SQS), el cual nos permite crear colas de procesamiento para una de las partes más importantes de nuestro desarrollo: el procesamiento de videos.

Este sistema de colas SQS permite validar, a través de la base de datos, los nuevos registros ingresados que se encuentran pendientes por ser procesados. El servicio se encarga de invocar alguna instancia worker, la cual inicia el proceso de ajuste del video y lo carga considerando los parámetros de durabilidad, tamaño y marca.

<img width="801" height="382" alt="image" src="https://github.com/user-attachments/assets/0976676b-769c-433e-ab01-e539a0204108" />
