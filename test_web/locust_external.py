from locust import HttpUser, TaskSet, task, between

class FrontendTasks(TaskSet):
    @task(1)
    def load_homepage(self):
        self.client.get("/")

class BackendTasks(TaskSet):
    @task(1)
    def get_mahasiswa(self):
        self.client.get("/mahasiswa")
    
    @task(2)
    def create_mahasiswa(self):
        self.client.post("/mahasiswa/create", json={
            "nim": "1234567890",
            "jurusan": "Teknik Informatika",
            "notelp": "081234567890",
            "email": "example@example.com",
            "alamat": "Jl. Contoh No. 123"
        })

class FrontendUser(HttpUser):
    tasks = [FrontendTasks]
    wait_time = between(1, 5)
    host = "https://pplfe-production-79c8.up.railway.app"

class BackendUser(HttpUser):
    tasks = [BackendTasks]
    wait_time = between(1, 5)
    host = "https://pplbe-production-290a.up.railway.app"
