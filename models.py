from pydantic import BaseModel, Field

class Item(BaseModel):
    item_id : int = Field(..., description="商品編號。")
    name : str = Field(..., description="商品名稱。")
    category : str = Field(..., description="商品類別。")
    price : float = Field(..., description="商品價格。", ge=0)
    is_available : bool = Field(..., description="商品是否可購買。")
    description : str = Field(None, description="商品描述。")
    stock : int = Field(..., description="商品庫存數量。", ge=0)

class Order(BaseModel):
    order_id : int = Field(..., description="訂單編號。")
    name : str = Field(..., description="訂購人姓名。")
    item_id : int = Field(..., description="商品編號。")
    item_name : str = Field(..., description="商品名稱。")
    quantity : int = Field(..., description="訂購數量。", ge=1)
    total_price : float = Field(..., description="訂單總價。", ge=0)
    status : str = Field(..., description="訂單狀態。")
    order_date : str = Field(..., description="訂單日期。") 