from fastapi import FastAPI
import json

app = FastAPI()

dict_of_tasks = {}
tasks_id_counter = 0

FILE_PATH = "task_storage.json"

def load_tasks_from_file() -> dict:
    global tasks_id_counter
    global dict_of_tasks
    try:
        with open(FILE_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
            dict_of_tasks = {int(k): v for k, v in data.get("tasks", {}).items()}
            tasks_id_counter = data.get("counter", 0)
    except FileNotFoundError:
        with open(FILE_PATH, "w", encoding="utf-8") as file:
            json.dump({
                "tasks": {},
                "counter": tasks_id_counter
            }, file)

def save_tasks_to_file() -> None:
    global tasks_id_counter
    global dict_of_tasks
    with open(FILE_PATH, "w", encoding="utf-8") as file:
        json.dump({
            "tasks": dict_of_tasks,
            "counter": tasks_id_counter
        }, file, ensure_ascii=False, indent=2)

load_tasks_from_file()

@app.get("/tasks")
def get_tasks() -> dict[int, dict[str, str]]:
    return dict_of_tasks

@app.post("/tasks")
def create_task(task: str, status: str = "--New task--") -> dict:
    global tasks_id_counter
    if task not in {t["task"] for t in dict_of_tasks.values()}:
        dict_of_tasks[tasks_id_counter] = {"task" : task, "status" : status}
        save_tasks_to_file()
        tasks_id_counter += 1
        return {
            "task_id": tasks_id_counter - 1,
            "task": task,
            "status": status,
            }
    else:
        return f"Task: {task} already exist!"

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: str, status: str = "--Updated task--") -> dict:
    if task_id in dict_of_tasks:
        dict_of_tasks[task_id] = {"task" : task, "status" : status}
        save_tasks_to_file()
        return {
            "task_id": task_id,
            "task": task,
            "status": status,
            }
    else:
        return f"Error, task with id[{task_id}] not found!"

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int) -> dict:
    if task_id in dict_of_tasks:
        deleted_task = dict_of_tasks.pop(task_id)
        save_tasks_to_file()
        return {
            "task_id": task_id,
            "task": deleted_task["task"],
            "status": "Deleted",
            }
    else:
        return f"Error, task with id[{task_id}] not found!"
