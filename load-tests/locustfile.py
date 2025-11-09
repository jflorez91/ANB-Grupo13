from locust import HttpUser, task, between
import os

# -------------------------------
# Escenario 1: Listar videos públicos
# -------------------------------
class ANBUserLectura(HttpUser):
    wait_time = between(1, 3)
    token = None

    def on_start(self):
        """Autenticación inicial y almacenamiento del token JWT."""
        credentials = {
            "email": "admin@anb.com",
            "password": "Admin12345"
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
        """Cabeceras con token JWT."""
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(3)
    def listar_videos_publicos(self):
        """Consulta la lista de videos públicos."""
        with self.client.get("/api/public/videos", headers=self._auth_headers(), catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.failure("Ruta /api/public/videos no encontrada.")
            else:
                response.failure(f"Error {response.status_code} al listar videos.")


# -------------------------------
# Escenario 2: Subida concurrente de videos
# -------------------------------
class ANBUserCarga(HttpUser):
    wait_time = between(2, 5)
    token = None

    def on_start(self):
        """Autenticación inicial y almacenamiento del token JWT."""
        credentials = {
            "email": "admin@anb.com",
            "password": "Admin12345"
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
        """Cabeceras con token JWT."""
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task
    def subir_video(self):
        """Simula la carga de un archivo de video pequeño."""
        headers = self._auth_headers()
        video_path = "test_video.mp4"

        # Genera un archivo dummy si no existe
        if not os.path.exists(video_path):
            with open(video_path, "wb") as f:
                f.write(os.urandom(1024 * 1024 * 5))  # 5 MB

        with open(video_path, "rb") as f:
            files = {"file": (video_path, f, "video/mp4")}
            with self.client.post("/api/videos/upload", files=files, headers=headers, catch_response=True) as response:
                if response.status_code in [200, 201]:
                    response.success()
                else:
                    response.failure(f"Error {response.status_code} al subir video.")
