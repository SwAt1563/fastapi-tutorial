from fastapi import FastAPI, Query, Path, Body
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl
from typing import Annotated


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
    name: str
    description: str | None = Field(default=None, title="The description of the item", max_length=300)
    price: float = Field(gt=0, description="The price must be greater than zero")
    tax: float | None = None
    tags: set[str] = set()
    image: Image | None = None


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