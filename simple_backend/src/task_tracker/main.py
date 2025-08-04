from fastapi import FastAPI
import json
from dotenv import load_dotenv
import os
import requests

load_dotenv()

app = FastAPI()


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


    def load_tasks_from_gist(self) -> None:
        response = requests.get(self.url, headers=self.headers)
        if response.status_code == 200:
            content = json.loads(response.json()["files"][self.filename]["content"])
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
            self.dict_of_tasks[self.tasks_id_counter] = {"task" : task, "status" : status}
            self.save_tasks_to_gist()
            self.tasks_id_counter += 1
            return {
                "task_id": self.tasks_id_counter - 1,
                "task": task,
                "status": status,
                }
        else:
            return f"Task: {task} already exist!"
    
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
            return f"Error, task with id[{task_id}] not found!"
        
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
            return f"Error, task with id[{task_id}] not found!"
    
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
