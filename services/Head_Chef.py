import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Nutrition(BaseModel):
    calories: int = Field(description="จำนวนแคลอรี่ (หน่วย kcal)")
    protein: int = Field(description="จำนวนโปรตีน (หน่วย กรัม)")

class Recipe(BaseModel):
    recipe_name: str = Field(description="ชื่อเมนูอาหาร (ต้องตรงกับชื่อที่ส่งให้ใน pool)")
    instruction: str = Field(description="ขั้นตอนการทำโดยละเอียดในภาษาไทย")
    nutrition: List[Nutrition]

class RecipeList(BaseModel):
    recommendations: List[Recipe] = Field(description="รายการเมนูแนะนำ 3 เมนู")


def gemie_menu_recommendation(user_ingredients, menu_pool, time_limit):
    
    # กำหนดบทบาทของ AI
    role = """
    คุณคือหัวหน้าเชฟผู้เชี่ยวชาญการทำอาหารทุกประเภท 
    หน้าที่ของคุณคือเลือกเมนูที่เหมาะสมที่สุด 3 เมนูจากรายการเมนู (Menu Pool) ที่กำหนดให้ 
    โดยพิจารณาจากวัตถุดิบที่ผู้ใช้มี (User Ingredients) และข้อจำกัดด้านเวลา 
    หากวัตถุดิบที่ผู้ใช้มีไม่ครบตามเมนูในระบบ ให้คุณแนะนำวิธีการดัดแปลงหรือใช้วัตถุดิบทดแทนเพื่อให้ทำเมนูนั้นได้จริง
    **สำคัญ: คุณต้องตอบเป็นภาษาไทยเท่านั้น**
    """

    # ตั้งค่า Config สำหรับการตอบกลับเป็น JSON List
    config = types.GenerateContentConfig(
        system_instruction=role,
        temperature=0.7, 
        response_mime_type="application/json",
        response_json_schema=RecipeList.model_json_schema(),
    )

    # สร้าง Prompt ที่ส่งเฉพาะข้อมูลที่จำเป็น
    prompt = f"""
    นี่คือรายการเมนูในระบบที่คุณสามารถเลือกได้:
    {json.dumps(menu_pool, ensure_ascii=False)}

    วัตถุดิบที่ผู้ใช้มี: {user_ingredients}
    เวลาที่มี: {time_limit} นาที

    คำสั่ง: 
    1. เลือกเมนูที่ดีที่สุด 3 เมนูจากรายการด้านบนที่เข้ากับวัตถุดิบของผู้ใช้
    2. เขียนขั้นตอนการปรุง (instruction) ให้ละเอียดและเข้าใจง่าย
    3. คำนวณค่าสารอาหาร (nutrition) ให้เหมาะสมกับวัตถุดิบที่ใช้
    """

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model='gemini-3-flash-preview',
        contents=prompt,
        config=config,
    )

    # ตรวจสอบและแปลงผลลัพธ์
    result = RecipeList.model_validate_json(response.text)
    
    return result.model_dump()['recommendations']

    