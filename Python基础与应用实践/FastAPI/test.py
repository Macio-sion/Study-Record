"""
@Author : Administrator
@Company : 
@Date : 2026/7/18 9:32
@Desc :
@Version : 1.0
"""
from fastapi import FastAPI, Path, Query
from pydantic import BaseModel, Field

from projects.unname.model.user import User

app = FastAPI(

)

class UserDTO(BaseModel):
    username: str = Field(...)
    age: int = Field(...)

users = [
    {"username": "test1", "age": 1},
    {"username": "test2", "age": 2},
]

@app.post("/users/user_create")
def create_user(user: UserDTO):
    new_user = {
        "username": user.username,
        "age": user.age,
    }
    users.append(new_user)
    return users


@app.get("/users/get_user_info")
def get_user_info(uid: int = Query(...), username: str = Query(...)):
    return {
        "uid": uid,
        "username": username
    }

@app.get("/users/{user_id}")
def get_user_by_username(user_id: int = Path(...)):
    return {"userid": user_id}

