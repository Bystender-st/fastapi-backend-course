from fastapi import FastAPI
import json

app = FastAPI()

class TaskStorage:

    def __init__(self):
        self.dict_of_tasks = {}
        self.tasks_id_counter = 0
        self.FILE_PATH = "task_storage.json"

        self.load_tasks_from_file()


    def load_tasks_from_file(self) -> None:
        try:
            with open(self.FILE_PATH, "r", encoding="utf-8") as file:
                data = json.load(file)
                self.dict_of_tasks = {int(k): v for k, v in data.get("tasks", {}).items()}
                self.tasks_id_counter = data.get("counter", 0)
        except FileNotFoundError:
            self.save_tasks_to_file()


    def save_tasks_to_file(self) -> None:
        with open(self.FILE_PATH, "w", encoding="utf-8") as file:
            json.dump({
                "tasks": self.dict_of_tasks,
                "counter": self.tasks_id_counter
            }, file, ensure_ascii=False, indent=2)
    

    def storage_get(self) -> dict[int, dict[str, str]]:
        return self.dict_of_tasks
    

    def storage_create(self, task: str, status: str = "--New task--") -> dict:
        if task not in {t["task"] for t in self.dict_of_tasks.values()}:
            self.dict_of_tasks[self.tasks_id_counter] = {"task" : task, "status" : status}
            self.save_tasks_to_file()
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
            self.save_tasks_to_file()
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
            self.save_tasks_to_file()
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
