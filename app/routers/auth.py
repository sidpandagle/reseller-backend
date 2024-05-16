from fastapi import APIRouter, Depends, HTTPException
from ..utils.auth import AuthDetails, AuthHandler

router = APIRouter()


auth_handler = AuthHandler()
users = [
    {
        "username": "admin",
        "password": "$2b$12$3wxlo4o69vfgVrc4CKTg0ee/7.mmz2HTo1kjUfmssHsznUhMZyYee",
    }
]


@router.post("/register", status_code=201)
def register(auth_details: AuthDetails):
    if any(x["username"] == auth_details.username for x in users):
        raise HTTPException(status_code=400, detail="Username is taken")
    hashed_password = auth_handler.get_password_hash(auth_details.password)
    users.append({"username": auth_details.username, "password": hashed_password})
    return {"message": "Registration Success", "data": users[len(users) - 1]}


@router.post("/login")
def login(auth_details: AuthDetails):
    user = None
    for x in users:
        if x["username"] == auth_details.username:
            user = x
            break

    if (user is None) or (
        not auth_handler.verify_password(auth_details.password, user["password"])
    ):
        raise HTTPException(status_code=401, detail="Invalid username and/or password")
    token = auth_handler.encode_token(user["username"])
    return {"token": token}


@router.get("/unprotected")
def unprotected():
    return {"hello": "world"}


@router.get("/protected")
def protected(username=Depends(auth_handler.auth_wrapper)):
    return {"name": username}
