import logging
import os
import json
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class AIGenerator:
    """AI orqali prezentatsiya matnlarini yaratish"""
    
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
    
    async def generate_presentation(self, topic: str, author: str, slides_count: int) -> list:
        """
        Prezentatsiya uchun matnlar yaratish
        
        Args:
            topic: Prezentatsiya mavzusi
            author: Muallif ismi
            slides_count: Slaydlar soni
            
        Returns:
            list: Har bir slayd uchun {title, content} dict
        """
        try:
            # Promptni tayyorlash
            prompt = f"""Siz professional prezentatsiya mutaxassisiz. 
            
Mavzu: {topic}
Muallif: {author}
Slaydlar soni: {slides_count}

Quyidagi tuzilmada JSON formatida prezentatsiya yarating:

1. Birinchi slayd - sarlavha slayd:
   - title: Prezentatsiya mavzusi
   - content: Muallif ismi va qisqa ta'rif

2. Keyingi slaydlar - asosiy kontent:
   - Har bir slayd uchun qisqa sarlavha (3-7 so'z)
   - Har bir slayd uchun mazmunli paragraf (50-150 so'z)
   - Mantiqiy tartibda: kirish, asosiy qismlar, xulosa

3. Oxirgi slayd - yakun:
   - title: "Xulosa" yoki "E'tiboringiz uchun rahmat"
   - content: Asosiy xulosalar

MUHIM:
- Matnlar ravon, tabiiy, odam yozgandek bo'lsin
- Har bir slayd mustaqil va tushunarli bo'lsin
- Texnik terminlar izohlansin
- JSON formatida javob bering

JSON formati:
{{
  "slides": [
    {{
      "title": "Sarlavha",
      "content": "Matn"
    }}
  ]
}}"""

            # AI dan javob olish
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Siz professional prezentatsiya yaratuvchisiz. Faqat JSON formatda javob bering."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            # Javobni parse qilish
            content = response.choices[0].message.content.strip()
            
            # JSON formatini tozalash (agar ``` bilan o'ralgan bo'lsa)
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            content = content.strip()
            
            # JSON parse
            result = json.loads(content)
            slides = result.get('slides', [])
            
            # Slaydlar sonini tekshirish va to'ldirish
            if len(slides) < slides_count:
                logger.warning(f"AI {len(slides)} slayd yaratdi, {slides_count} kerak edi")
                # Yetishmayotgan slaydlarni qo'shish
                for i in range(len(slides), slides_count):
                    slides.append({
                        "title": f"Qo'shimcha ma'lumot {i - len(slides) + 1}",
                        "content": f"{topic} haqida qo'shimcha tafsilotlar va ma'lumotlar."
                    })
            elif len(slides) > slides_count:
                # Ortiqcha slaydlarni olib tashlash
                slides = slides[:slides_count]
            
            logger.info(f"{len(slides)} slayd muvaffaqiyatli yaratildi")
            return slides
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse xatolik: {e}")
            # Rezerv slaydlar yaratish
            return self._create_fallback_slides(topic, author, slides_count)
            
        except Exception as e:
            logger.error(f"AI generatsiya xatolik: {e}")
            # Rezerv slaydlar yaratish
            return self._create_fallback_slides(topic, author, slides_count)
    
    def _create_fallback_slides(self, topic: str, author: str, slides_count: int) -> list:
        """Xatolik yuz berganda rezerv slaydlar yaratish"""
        slides = []
        
        # Sarlavha slayd
        slides.append({
            "title": topic,
            "content": f"Muallif: {author}\n\nBu prezentatsiya {topic} mavzusida tayyorlangan."
        })
        
        # Asosiy slaydlar
        sections = [
            "Kirish",
            "Asosiy tushunchalar",
            "Tahlil",
            "Natijalar",
            "Xulosa"
        ]
        
        for i in range(1, slides_count - 1):
            section = sections[min(i - 1, len(sections) - 1)]
            slides.append({
                "title": f"{section} {i}",
                "content": f"{topic} bo'yicha {section.lower()} qismi. Bu yerda asosiy ma'lumotlar va tafsilotlar keltirilgan."
            })
        
        # Yakun slayd
        slides.append({
            "title": "E'tiboringiz uchun rahmat!",
            "content": f"{topic} mavzusidagi prezentatsiya yakunlandi.\n\nSavollaringiz bo'lsa, so'rang!"
        })
        
        return slides[:slides_count]
