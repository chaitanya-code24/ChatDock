from fastapi import FastAPI


app = FastAPI()
food_item = {
    'indian' :["biryani", "paneer butter masala", "dal makhani"],
    'chinese' :["noodles", "manchurian", "spring rolls"],
    'italian' :["pizza", "pasta", "lasagna"]   
}
@app.get("/getitem/{cuisine}")
async def get_item(cuisine):
    return food_item.get(cuisine, "Cuisine not found")