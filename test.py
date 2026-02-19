from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List
import json


class Nutrition(BaseModel):
    calories: int = Field(description="Number of calories.")
    protein: int = Field(description="Number of protein.")

class Recipe(BaseModel):
    recipe_name: str = Field(description="Name of the recipe.")
    instruction: str
    nutrition: List[Nutrition]

role = """
    You are the head chef, an expert in all types of dishes, whether it's boiling, stir-frying, curries, frying, or Thai, Japanese, and others.
    You can prepare meals from the available ingredients to match the specified time as closely as possible.
    You will respond in Thai.
"""

with open('MenuBase.json', 'r', encoding='utf-8') as file:
    data = json.load(file)
    
menu_base = data['Food type']['curries']
user = "{'ingredients': [เนื้อไก่ 500 g, พริกแกงเขียวหวาน, กะทิ, มะเขือเปราะ]}"

config = types.GenerateContentConfig(
    system_instruction = role,
    temperature = 1, # ความคิดสร้างสรรค์น้อย=เร็ว 0 to 2
    response_mime_type = "application/json",
    response_json_schema = Recipe.model_json_schema(),
)

prompt = f"Please find a food menu from {menu_base} with ingredients similar to what the user provides {user} . If it can't be found, create a new menu based on what the user gives, you have 40 minutes."

client = genai.Client(api_key="")

response = client.models.generate_content(
    model = "gemini-3-flash-preview",
    contents = prompt,
    config = config,
)

result = Recipe.model_validate_json(response.text)
print("\n Bot :", result)