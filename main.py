from fastapi import FastAPI, Query, Path, Body, Cookie, Header, Response, status, Form, File, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, EmailStr
from typing import Annotated, Any
from datetime import datetime, time, timedelta
from uuid import UUID


app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello": "World"}


# this will override the '/items/{item_id}' route
# just of this specific route otherwire the second route will be used
@app.get("/items/favorite")
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

