import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Nutrition(BaseModel):
    calories: int = Field(description="ประมาณจำนวนแคลอรี่ (หน่วย kcal)")
    protein: int = Field(description="ประมาณจำนวนโปรตีน (หน่วย กรัม)")

class Recipe(BaseModel):
    recipe_name: str = Field(description="ชื่อเมนูอาหาร (ต้องตรงกับชื่อที่ส่งให้ใน pool)")
    instruction: str = Field(description="ขั้นตอนการทำโดยละเอียดในภาษาไทย")
    nutrition: List[Nutrition]

class RecipeList(BaseModel):
    recommendations: List[Recipe] # = Field(description="รายการเมนูแนะนำ 3 เมนู")


def gemie_menu_recommendation(list_menu):
    
    # กำหนดบทบาทของ AI
    role = """
    คุณคือหัวหน้าเชฟผู้เชี่ยวชาญการทำอาหารทุกประเภทและมีความคิดสร้างสรรค์.
    หน้าที่ของคุณคือการทำเมนูอาหารจากวัตถุดิบที่กำหนดให้ 
    หากวัตถุดิบที่ผู้ใช้ไม่มีให้คุณแนะนำวิธีการดัดแปลงหรือบอกวัตถุดิบทดแทนเพื่อให้ทำเมนูนั้นได้จริง.
    **สำคัญ: คุณต้องตอบเป็นภาษาไทยเท่านั้น**
    """

    # ตั้งค่า Config สำหรับการตอบกลับเป็น JSON List
    config = types.GenerateContentConfig(
        system_instruction=role,
        temperature=0.5, 
        response_mime_type="application/json",
        response_json_schema=RecipeList.model_json_schema(),
    )

    # สร้าง Prompt ที่ส่งเฉพาะข้อมูลที่จำเป็น
    prompt = f"""
    นี่คือรายการเมนู:
    {json.dumps(list_menu, ensure_ascii=False)}

    คำสั่ง: 
    1. เขียนขั้นตอนการปรุง (instruction) ให้ละเอียดและเข้าใจง่ายจากวัตถุดิบที่มีและคุณสามารถแนะนำเครื่องปรุงได้เต็มที่แม้ว่าผู้ใช้จะกำหนดมาให้หรือไม่ก็ตาม
    2. ประมาณค่าสารอาหาร (nutrition) ให้เหมาะสมกับวัตถุดิบที่ใช้
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

    