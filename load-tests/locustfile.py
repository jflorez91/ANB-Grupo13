from locust import HttpUser, task, between
import random
import json
import os

class ANBUser(HttpUser):
    wait_time = between(1, 3)
    token = None

    def on_start(self):
        """
        Se ejecuta al iniciar la simulación para cada usuario virtual.
        Autentica al usuario y almacena el token JWT.
        """
        credentials = {
            "email": "admin@anb.com",
            "password": "Admin123!"
        }

        with self.client.post("/api/auth/login", json=credentials, catch_response=True) as response:
            if response.status_code == 200:
                try:
                    self.token = response.json().get("access_token")
                    if self.token:
                        response.success()
                    else:
                        response.failure("No se obtuvo el token JWT.")
                except Exception as e:
                    response.failure(f"Error procesando respuesta de login: {e}")
            else:
                response.failure(f"Error de inicio de sesión: {response.status_code} {response.text}")

    def _auth_headers(self):
        """Genera las cabeceras con token JWT."""
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(3)
    def listar_jugadores(self):
        """Consulta la lista de jugadores."""
        with self.client.get("/api/jugadores", headers=self._auth_headers(), catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.failure("Ruta /api/jugadores no encontrada.")
            else:
                response.failure(f"Error {response.status_code} al listar jugadores.")

    @task(2)
    def ver_rankings(self):
        """Consulta los rankings de jugadores."""
        with self.client.get("/api/rankings", headers=self._auth_headers(), catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.failure("Ruta /api/rankings no encontrada.")
            else:
                response.failure(f"Error {response.status_code} en rankings.")

    @task(1)
    def subir_video(self):
        """Simula la subida de un video corto (fake)."""
        fake_video_path = os.path.join(os.getcwd(), "fake_video.mp4")
        # Crear un archivo temporal si no existe
        if not os.path.exists(fake_video_path):
            with open(fake_video_path, "wb") as f:
                f.write(os.urandom(1024))  # 1 KB aleatorio

        files = {"file": open(fake_video_path, "rb")}
        data = {"titulo": f"jugada_{random.randint(1,1000)}", "descripcion": "Simulación de prueba de carga"}

        with self.client.post("/api/videos/upload", headers=self._auth_headers(), files=files, data=data, catch_response=True) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 403:
                response.failure("Token no autorizado o sin permisos.")
            else:
                response.failure(f"Error {response.status_code} al subir video.")
