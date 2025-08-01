from fastapi import FastAPI
import json

app = FastAPI()

dict_of_tasks = {}
tasks_id_counter = 0

@app.get("/tasks")
def get_tasks():
    return dict_of_tasks

@app.post("/tasks")
def create_task(task: str, status: str = "--New task--"):
    global tasks_id_counter
    if task not in {t["task"] for t in dict_of_tasks.values()}:
        dict_of_tasks[tasks_id_counter] = {"task" : task, "status" : status}
        tasks_id_counter += 1
        return f"Created id[{tasks_id_counter - 1}]: task: {task}, status: {status}"

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: str, status: str = "--Updated task--"):
    if task_id in dict_of_tasks:
        dict_of_tasks[task_id] = {"task" : task, "status" : status}
        return f"{dict_of_tasks[task_id]} updated!"
    else:
        return f"Error, task with id[{task_id}] did not found!"

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    if task_id in dict_of_tasks:
        dict_of_tasks.pop(task_id)
        return f"Task with id[{task_id}] deleted!"
    else:
        return f"Error, task with id[{task_id}] did not found!"
