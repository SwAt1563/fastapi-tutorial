from fastapi import FastAPI, Query, Path, Body, Cookie, Header, Response, status, Form, File, UploadFile, HTTPException, Depends, Request, BackgroundTasks, WebSocket
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse, ORJSONResponse
from fastapi.encoders import jsonable_encoder
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, EmailStr
from typing import Annotated, Any
from datetime import datetime, time, timedelta
from uuid import UUID
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient

# environment variables
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict



tags_metadata = [
    {
        "name": "users",
        "description": "Operations with users. The **login** logic is also here.",
    },
    {
        "name": "items",
        "description": "Manage items. So _fancy_ they have their own docs.",
        "externalDocs": {
            "description": "Items external docs",
            "url": "https://fastapi.tiangolo.com/",
        },
    },
]

description = """
ChimichangApp API helps you do awesome stuff. 🚀

## Items

You can **read items**.

## Users

You will be able to:

* **Create users** (_not implemented_).
* **Read users** (_not implemented_).
"""
app = FastAPI(
    # openapi_url=None,
    openapi_tags=tags_metadata,
    title="ChimichangApp",
    description=description,
    summary="Deadpool's favorite app. Nuff said.",
    version="0.0.1",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "Deadpoolio the Amazing",
        "url": "http://x-force.example.com/contact/",
        "email": "dp@x-force.example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
        # "identifier": "MIT",
    },
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    from time import time
    start_time = time()
    response = await call_next(request)
    process_time = time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response




# CORS
origins = [

    "http://localhost",
    "http://localhost:8080",
]

"""
max_age - Sets a maximum time in seconds for browsers to cache CORS responses. Defaults to 600.

allow_credentials - Indicate that cookies should be supported for cross-origin requests. 
Defaults to False. Also, allow_origins cannot be set to ['*'] for credentials to be allowed, origins must be specified.
"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Test
client = TestClient(app)

@app.get("/")
async def read_root():
    return {"Hello": "World"}


# it should be in sperate file
# https://fastapi.tiangolo.com/tutorial/testing/
def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}


# this will override the '/items/{item_id}' route
# just of this specific route otherwire the second route will be used
@app.get("/items/favorite", tags=["items"])
async def read_item():
    return {"item": "override"}

# bool: can be true, True, yes, 1 or on
@app.get("/items/{item_id}")
async def read_item(item_id: str, query_param_optional: bool | None = None):
    if query_param_optional:
        return {"item_id": item_id, "query_param_optional": query_param_optional}
    return {"item_id": item_id}


@app.get("/file/{file_path:path}")
async def read_file(file_path: str):
    return {"file_path": file_path}


class CNNModel(str, Enum):
    resnet = "resnet"
    alexnet = "alexnet"
    lenet = "lenet"
   

@app.get("/model/{model_name}")
async def get_model(model_name: CNNModel):
    if model_name == CNNModel.resnet:
        return {"model_name": model_name, "message": "Deep Residual Learning for Image Recognition"}
    if model_name.value == "alexnet":
        return {"model_name": model_name, "message": "ImageNet Classification with Deep Convolutional Neural Networks"}
    return {"model_name": model_name, "message": "LeNet-5: Gradient-Based Learning Applied to Document Recognition"}


# Query Parameters
# http://127.0.0.1:8000/items/?skip=0&limit=10
@app.get("/items")
async def read_item(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}

@app.get("/required_params")
async def read_item(q: str):
    return {"query": q}

class Image(BaseModel):
    url: HttpUrl
    name: str

# Request Body
class Item(BaseModel):
    name: str = Field(examples=["Qutaiba", "ahmad"])
    description: str | None = Field(default=None, title="The description of the item", max_length=300)
    price: float = Field(gt=0, description="The price must be greater than zero")
    tax: float | None = None
    tags: set[str] = set()
    image: Image | None = None
  

    model_config = {
        "json_schema_extra":{
            "examples": [
                {
                    "name": "Foo",
                    "description": "A very nice Item",
                    "price": 35.4,
                    "tax": 3.2,
                    "tags": ["rock", "metal", "bar"],
                    "image": {
                        "url": "http://example.com/baz.jpg",
                        "name": "The Foo live"
                    }
                }
                
            ]
        }
    }

       


@app.post("/items/")
async def create_item(item: Item):
    item_dict = item.dict()
    if item.tax:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})
    return item_dict
    
@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    return {"item_id": item_id, **item.model_dump()}


# Query Parameter List / Multiple Values
@app.get("/list/")
async def read_list(q: Annotated[str | None, Query(min_length=3, max_length=50)] = None):
    query_items = {"q": q}
    return query_items


# Query Parameter List / Multiple Values
@app.get("/list2/")
async def read_list(q: Annotated[list[str] | None, Query(title="how are you")]):
    query_items = {"q": q}
    return query_items

# Path Parameters
@app.get("/path/{item_id}")
async def read_item(item_id: Annotated[str, Path(title="test", description="The ID of the item to get")], q: str = None):
    return {"item_id": item_id, "q": q}


# Request Body + Path Parameters
@app.put("/item/{item_id}")
async def update_item(item_id: int, item: Annotated[Item | None, Body(embed=True)], q: str | None = None):
    return {"item_id": item_id, **item.model_dump(), "q": q}


@app.post("/images/multiple/")
async def create_multiple_images(images: list[Image]):
    return images

@app.post("/index-weights/")
async def create_index_weights(weights: dict[int, float]):
    return weights


@app.put("/update/{item_id}")
async def update_item(item_id: UUID, start_datetime: Annotated[datetime, Body()], end_datetime: Annotated[datetime, Body()], process_time: Annotated[timedelta, Body()], repeat_at: Annotated[time | None, Body()] = None):
    start_process_time = start_datetime + process_time
    return {"item_id": item_id, "start_datetime": start_datetime, "end_datetime": end_datetime, "process_time": process_time, "start_process_time": start_process_time, "repeat_at": repeat_at}


@app.get("/cookie/")
async def read_cookie(ads_id: Annotated[str | None, Cookie()] = None ):
    return {"ads_id": ads_id}

@app.get("/header/")
async def read_header(user_agent: Annotated[str | None, Header()] = None):
    return {"User-Agent": user_agent}

# response model
@app.get("/response_model/")
async def read_response_model() -> Item:
    return Item(name="Foo", price=35.4)

@app.get("/response_model_param/", response_model=Item)
async def read_response_model_param() -> Any:
    return Item(name="Foo", price=3533.4)


class BaseUser(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None

class UserIn(BaseUser):
    password: str


@app.post("/user/")
async def create_user(user: UserIn) -> BaseUser:
    return user

# @app.post("/user/", response_model=BaseUser)
# async def create_user(user: UserIn) -> Any:
#     return user

@app.get('/teleport/')
async def get_teleport() -> RedirectResponse:
    return RedirectResponse(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")

@app.get('/portal/', response_class=Response)
async def get_portal(tele: bool = False) -> Any:
    if tele:
        return RedirectResponse(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    return JSONResponse(content={"message": "Welcome to the portal"})


# # fail
# @app.get("/portal")
# async def get_portal(teleport: bool = False) -> Response | dict:
#     if teleport:
#         return RedirectResponse(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
#     return {"message": "Here's your interdimensional portal."}

# # success
# @app.get("/portal", response_model=None)
# async def get_portal(teleport: bool = False) -> Response | dict:
#     if teleport:
#         return RedirectResponse(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
#     return {"message": "Here's your interdimensional portal."}



items = {
    "foo": {"name": "Foo", "price": 50.2},
    "bar": {"name": "Bar", "description": "The bartenders", "price": 62, "tax": 20.2},
    "baz": {"name": "Baz", "description": None, "price": 50.2, "tax": 10.5, "tags": []},
}

# response_model_exclude_unset: exclude the fields that are not set
@app.get("/get_items/{item_id}", response_model=Item, response_model_exclude_unset=True)
async def read_items(item_id: str):
    return items[item_id]

# @app.get(
#     "/items/{item_id}/name",
#     response_model=Item,
#     response_model_include=["name", "description"],
# )
# async def read_item_name(item_id: str):
#     return items[item_id]


# @app.get("/items/{item_id}/public", response_model=Item, response_model_exclude=["tax"])
# async def read_item_public_data(item_id: str):
#     return items[item_id]


# keyword-weights
@app.get("/keyword-weights/", response_model=dict[str, float])
async def read_keyword_weights():
    return {"foo": 2.3, "bar": 3.4}


# status code
@app.get("/status_code/{item_id}", status_code=status.HTTP_200_OK)
async def read_item_status_code(item_id: str):
    if item_id not in items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found", headers={"X-Error": "There goes my error"})
    return items[item_id]

# form
@app.post("/login/")
async def login(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    return {"username": username}


# file upload
@app.post("/uploadfile/")
async def create_upload_file(file: Annotated[UploadFile, Form(description="The file to upload")]):
    data = await file.read()
    print(data)
    return {"filename": file.filename}

# multiple files
@app.post("/multiple_files/")
async def create_upload_files(files: list[UploadFile]):
    return {"filenames": [file.filename for file in files]}

# FILE FORM HTML
@app.get("/file_form/")
async def get_file():
    content = """
    <body>
<form action="/uploadfile/" enctype="multipart/form-data" method="post">
<input name="files" type="file">
<input type="submit">
</form>
<form action="/multiple_files/" enctype="multipart/form-data" method="post">
<input name="files" type="file" multiple>
<input type="submit">
</form>
</body>
    """
    return HTMLResponse(content=content)


# Custom Exception

class UnicornException(Exception):
    def __init__(self, name: str):
        self.name = name

@app.exception_handler(UnicornException)
async def unicorn_exception_handler(request, exc):
    return JSONResponse(
        status_code=418,
        content={"message": f"Oops! {exc.name} did something. There goes a rainbow..."},
    )

@app.get("/unicorns/{name}", response_model=dict[str, str])
async def read_unicorn(name: str):
    if name == "yolo":
        raise UnicornException(name=name)
    return {"unicorn_name": name}


# tags for docs
@app.get("/tags/", tags=["tags"])
async def read_tags():
    return [{"name": "Foo"}]

# class Tags(Enum):
#     items = "items"
#     users = "users"


# @app.get("/items/", tags=[Tags.items])
# async def get_items():
#     return ["Portal gun", "Plumbus"]



# summary and description
@app.get("/summary/", summary="This is a summary")
async def read_summary():
    """
    This is a description

    - **name**: The name of the item
    - **description**: The description of the item
    - **price**: The price of the item
    """
    return {"summary": "This is a summary"}


# deprecated
@app.get("/deprecated/", deprecated=True)
async def read_deprecated():
    return {"deprecated": "This is deprecated"}


# encoding
@app.put("/encoding/{item_id}")
async def update_item(item_id: str, item: Item):
    json_compatible_item_data = jsonable_encoder(item) # convert Pydantic to json (sometime datetime need to convert to string)
    return {"item_id": item_id, "item_data": json_compatible_item_data}


# put and patch
# exp: "baz": {"name": "Baz", "description": None, "price": 50.2, "tax": 10.5, "tags": []},
@app.put("/put/{item_id}")
async def update_item(item_id: str, item: Item):
    update_item_encoded = jsonable_encoder(item)
    items[item_id] = update_item_encoded
    return update_item_encoded

@app.patch("/patch/{item_id}")
async def patch_item(item_id: str, item: Item):
    update_item_encoded = jsonable_encoder(item)
    items[item_id] = update_item_encoded
    return update_item_encoded



# SLEEP

# in sequence
@app.get("/sleep1/")
async def sleep1():
    from time import sleep
    print("sleeping")
    sleep(5)
    print("awake")
    return {"message": "I'm back!"}

# in concurrency
@app.get("/sleep2/")
async def sleep2():
    import asyncio
    print("sleeping")
    await asyncio.sleep(5) # just function that need 5 seconds
    print("awake")
    return {"message": "I'm back!"}

# in parallel
@app.get("/sleep3/")
def sleep3():
    from time import sleep
    print("sleeping")
    sleep(20)
    print("awake")
    return {"message": "I'm back!"}



# Dependency Injection
async def common_parameters(q: str | None = None, skip: int = 0, limit: int = 10):
    return {"q": q, "skip": skip, "limit": limit}

CommonDep = Annotated[dict, Depends(common_parameters)]
@app.get("/dependency/")
async def read_dependency(commons: CommonDep):
    
    return commons

# class Dependency

class ProductParams:
    def __init__(self, q: str | None = None, skip: int = 0, limit: Annotated[int, Body()] = 10):
        self.q = q
        self.skip = skip
        self.limit = limit


@app.get("/dependency2/")
async def read_dependency2(product_params: Annotated[ProductParams, Depends()]):
    return {"q": product_params.q, "skip": product_params.skip, "limit": product_params.limit}
        

# pydantic dependency | not good if you want to use Body, and other fields
class ItemParams(BaseModel):
    q: str | None = None
    skip: int = 0
    limit: int = 10


@app.get("/dependency3/")
async def read_dependency3(item_params: Annotated[ItemParams, Depends()]):
    return item_params.model_dump()


# sub-dependency
async def query_extractor(q: str | None = None):
    return q

async def query_or_cookie_extractor(q: Annotated[str, Depends(query_extractor)], last_query: Annotated[str | None, Cookie()] = None):
    if not q:
        return last_query
    return q

@app.get("/dependency4/")
async def read_dependency4(query_or_default: str = Depends(query_or_cookie_extractor)):
    return {"q_or_cookie": query_or_default}


# Dependencies in path operation decorators

async def verify_token(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")


async def verify_key(x_key: Annotated[str, Header()]):
    if x_key != "fake-super-secret-key":
        raise HTTPException(status_code=400, detail="X-Key header invalid")
    return x_key


@app.get("/items_dep/", dependencies=[Depends(verify_token), Depends(verify_key)])
async def read_items_dep():
    return [{"item": "Foo"}, {"item": "Bar"}]




# Bigger Applications - Multiple Files
# https://fastapi.tiangolo.com/tutorial/bigger-applications/


# Global Dependencies
# app = FastAPI(dependencies=[Depends(verify_token), Depends(verify_key)])



# Dependencies with yield

async def get_db():
    db = {"db_connection": "db_connection"}
    try:
        yield db
    finally:
        # db.close()
        pass

@app.get("/db/")
async def read_db(db: Annotated[dict, Depends(get_db)]):
    return db

# context managers

class MyContextManger:
    def __init__(self):
        # self.db = DBSession()
        print("init")
    def __enter__(self):
        print("enter")
        # return self.db
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        print("exit")
        # self.db.close()
        return True
    
@app.get("/context_manager/")
async def read_context_manager():
    with MyContextManger() as cm:
        print("inside")
        return {"message": "Hello"}
    

# security

# OAuth2PasswordBearer
# But if your API was located at https://example.com/api/v1/, then it would refer to https://example.com/api/v1/token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/security/")
async def read_security(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}


# Get current user

class UserData(BaseModel):
    username: str
    email: EmailStr | None = None
    full_name: str | None = None
    disabled: bool = False

def get_fake_user(token: str):
    return UserData(username=token + "user")

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = get_fake_user(token)
    return user
    

@app.get("/security2/")
async def read_security2(current_user: Annotated[UserData, Depends(get_current_user)]):
    return current_user

# background tasks

def write_notification(email: str, message=""):
    with open("log.txt", mode="w") as email_file:
        content = f"notification for {email}: {message}"
        email_file.write(content)

@app.post("/send-notification/{email}")
async def send_notification(email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(write_notification, email, message="some notification")
    return {"message": "Message sent in the background"}


# ORJSONResponse

# app = FastAPI(default_response_class=ORJSONResponse)
"""
Performance: orjson is faster at serializing Python data structures to JSON and deserializing JSON to Python objects.
This can significantly improve the performance of web applications that rely heavily on JSON for their API responses.
"""

# @app.get("/items/")
# async def read_items():
#     return [{"item_id": "Foo"}]


# use request
@app.get("/request")
def read_root(item_id: str, request: Request):
    client_host = request.client.host
    return {"client_host": client_host, "item_id": item_id}


# WebSockets
html = """

<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>

"""

@app.get("/connect")
async def get_connect():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")


# Test websockets
# @app.websocket("/ws")
# async def websocket(websocket: WebSocket):
#     await websocket.accept()
#     await websocket.send_json({"msg": "Hello WebSocket"})
#     await websocket.close()

# def test_websocket():
#     client = TestClient(app)
#     with client.websocket_connect("/ws") as websocket:
#         data = websocket.receive_json()
#         assert data == {"msg": "Hello WebSocket"}


# Lifespan Events
"""
Because this code is executed before the application starts taking requests, and right after it finishes handling requests,
it covers the whole application lifespan (the word "lifespan" will be important in a second 😉).

Use Case
Let's start with an example use case and then see how to solve it with this.

Let's imagine that you have some machine learning models that you want to use to handle requests. 🤖

The same models are shared among requests, so, it's not one model per request, or one per user or something similar.

Let's imagine that loading the model can take quite some time, because it has to read a lot of data from disk. So you don't want to do it for every request.

You could load it at the top level of the module/file, but that would also mean that it would load the model even if you are just running a simple automated test, then that test would be slow because it would have to wait for the model to load before being able to run an independent part of the code.

That's what we'll solve, let's load the model before the requests are handled, but only right before the application starts receiving requests, not while the code is being loaded

"""

# from contextlib import asynccontextmanager

# from fastapi import FastAPI


# def fake_answer_to_everything_ml_model(x: float):
#     return x * 42


# ml_models = {}


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Load the ML model
#     ml_models["answer_to_everything"] = fake_answer_to_everything_ml_model
#     yield
#     # Clean up the ML models and release the resources
#     ml_models.clear()


# app = FastAPI(lifespan=lifespan)


# @app.get("/predict")
# async def predict(x: float):
#     result = ml_models["answer_to_everything"](x)
#     return {"result": result}



# async testing
"""
# https://fastapi.tiangolo.com/advanced/async-tests/

import pytest
from httpx import AsyncClient

from .main import app


@pytest.mark.anyio
async def test_root():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Tomato"}


"""




class Settings(BaseSettings):
    KEY: str


    model_config = SettingsConfigDict(env_file=".env")



@lru_cache
def get_settings():
    return Settings()


@app.get("/info")
async def info(settings: Annotated[Settings, Depends(get_settings)]):
    return {
        "app_name": settings.KEY,
    }