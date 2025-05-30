import json
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List

app = FastAPI()

DB_FILE = "users.txt"


class UserCreate(BaseModel):
    name: str
    email: str

class User(UserCreate):
    id: int


def load_users_from_file() -> List[User]:
    try:
        with open(DB_FILE, "r") as f:
            users_data = json.load(f)
            return [User(**data) for data in users_data]
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_users_to_file(users: List[User]):
    with open(DB_FILE, "w") as f:
        users_data = [user.model_dump() for user in users]
        json.dump(users_data, f, indent=4)


users = load_users_from_file()
next_id = len(users) + 1 if users else 1


@app.post("/users/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(user_data: UserCreate):
    global next_id
    new_user = User(id=next_id, **user_data.model_dump())

    users.append(new_user)
    save_users_to_file(users)
    next_id += 1
    return new_user


@app.get("/users/", response_model=List[User])
def read_users():
    return users


@app.get("/users/{user_id}", response_model=User)
def read_user(user_id: int):
    for user in users:
        if user.id == user_id:
            return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, user_data: UserCreate):
    for index, user in enumerate(users):
        if user.id == user_id:
            updated_user = User(id=user_id, **user_data.model_dump())
            users[index] = updated_user
            save_users_to_file(users)
            return updated_user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int):
    user_to_remove = None
    for user in users:
        if user.id == user_id:
            user_to_remove = user
            break

    if user_to_remove is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    users.remove(user_to_remove)
    save_users_to_file(users)
    return