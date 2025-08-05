from fastapi import FastAPI
import json
from dotenv import load_dotenv
import os
import requests

load_dotenv()

app = FastAPI()

class CloudflareLLM:
    def __init__(self):
        self.account_id =os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        self.model = "@cf/meta/llama-3-8b-instruct"
        self.url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{self.model}"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
    
    def ask_model(self, task_text: str) -> str:
        prompt = f"Как решить задачу: {task_text}?"
        payload = {
            "messages": [
            {"role": "system", "content": "Ты помощник, который объясняет, как решать задачи."},
            {"role": "user", "content": task_text}
            ]
        }
        response = requests.post(self.url, headers=self.headers, json=payload)
        if response.status_code == 200:
            return response.json()["result"]["response"]
        else:
            raise Exception(f"Cloudflare API Error: {response.status_code} {response.text}")
        

class TaskStorage:

    def __init__(self):
        self.dict_of_tasks = {}
        self.tasks_id_counter = 0
        self.filename = "task_storage.json"

        self.GIST_ID = os.getenv("GIST_ID")
        self.GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
        self.url = f"https://api.github.com/gists/{self.GIST_ID}"
        self.headers = {"Authorization": f"token {self.GITHUB_TOKEN}"}

        self.load_tasks_from_gist()

        self.llm = CloudflareLLM()


    def load_tasks_from_gist(self) -> None:
        response = requests.get(self.url, headers=self.headers)
        if response.status_code == 200:
            content = response.json()["files"][self.filename]["content"]
            try:
                data = json.loads(content)
                self.dict_of_tasks = {int(k): v for k, v in data.get("tasks", {}).items()}
                self.tasks_id_counter = data.get("counter", 0)
            except json.JSONDecodeError:
                self.dict_of_tasks = {}
                self.tasks_id_counter = 0
                self.save_tasks_to_gist()


    def save_tasks_to_gist(self) -> None:
        load_data = {
            "files": {
                self.filename: {
                    "content": json.dumps({
                        "tasks": self.dict_of_tasks,
                        "counter": self.tasks_id_counter
                    }, ensure_ascii=False, indent=2)
                }
            }
        }
        response = requests.patch(self.url, headers=self.headers, json=load_data)
        if response.status_code != 200:
            raise Exception(f"Failed to update Gist: {response.status_code} {response.text}")


    def storage_get(self) -> dict[int, dict[str, str]]:
        return self.dict_of_tasks
    

    def storage_create(self, task: str, status: str = "--New task--") -> dict:
        if task not in {t["task"] for t in self.dict_of_tasks.values()}:
            if not task.strip():
                return {"error": "Task text cannot be empty"}
            try:
                explanation = self.llm.ask_model(task)
                task_with_explanation = f"{task}\n\nAI Suggestion: {explanation}"
            except Exception as e:
                task_with_explanation = f"{task}\n\n[AI Error: {e}]"
            self.dict_of_tasks[self.tasks_id_counter] = {"task" : task_with_explanation, "status" : status}
            self.save_tasks_to_gist()
            self.tasks_id_counter += 1
            return {
                "task_id": self.tasks_id_counter - 1,
                "task": task_with_explanation,
                "status": status,
                }
        else:
            return {"error": f"Task '{task}' already exists!"}
    
    def storage_update(self, task_id: int, task: str, status: str = "--Updated task--") -> dict:
        if task_id in self.dict_of_tasks:
            self.dict_of_tasks[task_id] = {"task" : task, "status" : status}
            self.save_tasks_to_gist()
            return {
                "task_id": task_id,
                "task": task,
                "status": status,
                }
        else:
            return {"error": f"task with id[{task_id}] not found!"}
        
    def storage_delete(self, task_id: int) -> dict:
        if task_id in self.dict_of_tasks:
            deleted_task = self.dict_of_tasks.pop(task_id)
            self.save_tasks_to_gist()
            return {
                "task_id": task_id,
                "task": deleted_task["task"],
                "status": "Deleted",
                }
        else:
            return {"error": f"task with id[{task_id}] not found!"}
    
t = TaskStorage()

@app.get("/tasks")
def get_tasks() -> dict[int, dict[str, str]]:
    return t.storage_get()

@app.post("/tasks")
def create_task(task: str, status: str = "--New task--") -> dict:
    return t.storage_create(task, status)

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: str, status: str = "--Updated task--") -> dict:
    return t.storage_update(task_id, task, status)

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int) -> dict:
    return t.storage_delete(task_id)
