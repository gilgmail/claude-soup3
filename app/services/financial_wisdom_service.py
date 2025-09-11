"""
財商成長思維文章生成服務
基於現有的 AI 服務，專門針對財商教育文章生成
"""

import re
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

import structlog
from anthropic import AsyncAnthropic

from app.core.config import get_settings

logger = structlog.get_logger()


class AIContentGenerationService:
    """財商文章 AI 生成服務"""
    
    def __init__(self):
        self.config = get_settings()
        if hasattr(self.config, 'anthropic_api_key'):
            self.anthropic_client = AsyncAnthropic(api_key=self.config.anthropic_api_key)
        else:
            # 使用舊的配置結構
            self.anthropic_client = AsyncAnthropic(api_key=self.config.ai_anthropic_api_key)
        
    
    async def generate_financial_article(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """生成財商成長思維文章"""
        try:
            # 構建專業的財商文章提示詞
            prompt = self._build_financial_article_prompt(request)
            
            # 使用 Claude 生成文章
            response = await self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",  # 使用可用的 Claude 3 模型
                max_tokens=4000,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            content = response.content[0].text if response.content else ""
            
            if not content:
                return {
                    'success': False,
                    'error': 'AI 服務返回空內容'
                }
            
            # 解析生成的文章
            article_data = self._parse_financial_article(content, request)
            
            # 評估文章品質
            quality_score = await self._evaluate_article_quality(content)
            article_data['quality_score'] = quality_score
            
            return {
                'success': True,
                'data': article_data
            }
            
        except Exception as e:
            logger.error(f"財商文章生成失敗: {str(e)}")
            return {
                'success': False,
                'error': f'生成失敗: {str(e)}'
            }
    
    def _build_financial_article_prompt(self, request: Dict[str, Any]) -> str:
        """構建財商文章生成提示詞"""
        
        title = request.get('title', '')
        topic = request.get('topic', '')
        target_audience = request.get('target_audience', '一般投資者')
        writing_style = request.get('writing_style', '實用智慧')
        word_count_target = request.get('word_count_target', 1500)
        include_case_study = request.get('include_case_study', True)
        focus_areas = request.get('focus_areas', [])
        
        focus_areas_text = "、".join(focus_areas) if focus_areas else "財富累積、投資理財、風險管理"
        
        prompt = f"""你是一位擁有15年經驗的資深財富教練和商業策略專家。請為「財商成長思維」主題創作一篇深度文章。

文章要求：
- 標題：{title}
- 主題：{topic}
- 目標讀者：{target_audience}
- 寫作風格：{writing_style}
- 目標字數：{word_count_target}字
- 重點領域：{focus_areas_text}
- 包含案例研究：{'是' if include_case_study else '否'}

文章結構要求：
1. **引言** (150字)：說明主題的重要性和緊迫性，以15年財富教練經驗開場
2. **核心概念** (300字)：深入解析理論框架和核心原理
3. **案例研究** (250字)：真實客戶案例或市場實例分析
4. **行動步驟** (200字)：4個具體可執行的實務建議
5. **常見障礙** (100字)：3個主要困難點及解決方案
6. **總結** (150字)：整合要點並提供激勵性結語

寫作風格要求：
- 以資深專家身份撰寫，展現專業權威性
- 語調親切但專業，避免過度學術化
- 提供具體可行的建議，不要空泛理論
- 融入行為經濟學、心理學等相關理論
- 使用真實感強的案例（可以匿名化）
- 結尾包含標籤：#財富思維 #個人成長 #投資理財

請確保文章內容豐富、邏輯清晰、實用性強，能夠真正幫助讀者提升財商思維。"""

        return prompt
    
    def _parse_financial_article(self, content: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """解析生成的財商文章"""
        
        # 使用請求的標題，因為AI不一定按格式生成標題
        title = request.get('title', '財商智慧分享')
        
        # 保留完整內容，不移除任何部分
        article_content = content.strip()
        
        # 生成標準標籤
        keywords = ['財富思維', '個人成長', '投資理財']
        
        # 根據主題添加額外標籤
        topic_lower = request.get('topic', '').lower()
        if '複利' in topic_lower:
            keywords.append('複利效應')
        if '風險' in topic_lower:
            keywords.append('風險管理')
        if '投資' in topic_lower:
            keywords.append('投資策略')
        if '時間' in topic_lower:
            keywords.append('時間管理')
        
        # 保留前5個標籤
        keywords = keywords[:5]
        
        # 計算實際字數
        text_content = re.sub(r'[#*`\-]', '', article_content)
        word_count = len(text_content.replace('\n', '').replace('\r', '').replace(' ', ''))
        
        # 判斷分類
        category = self._categorize_article(article_content, request)
        
        # 生成摘要（取前200字）
        summary = article_content[:200].replace('\n', ' ').strip() + "..."
        
        return {
            'title': title,
            'content': article_content,
            'summary': summary,
            'category': category,
            'keywords': keywords,
            'word_count': word_count,
            'target_audience': request.get('target_audience', '一般投資者'),
            'writing_style': request.get('writing_style', '實用智慧')
        }
    
    def _categorize_article(self, content: str, request: Dict[str, Any]) -> str:
        """根據內容自動分類文章"""
        
        topic = request.get('topic', '').lower()
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ['風險', '管理', '波動', '情緒', '心理']):
            return '風險管理'
        elif any(keyword in content_lower for keyword in ['複利', '規劃', '思維', '認知', '周期']):
            return '思維轉換'
        elif any(keyword in content_lower for keyword in ['收入', '變現', '創業', '技能', '品牌']):
            return '實戰技巧'
        elif any(keyword in content_lower for keyword in ['習慣', '心理', '教育', '傳承', '學習']):
            return '心理素質'
        elif any(keyword in content_lower for keyword in ['財富', '投資', '資產', '配置']):
            return '財富建構'
        else:
            return '財富建構'
    
    async def _evaluate_article_quality(self, content: str) -> float:
        """評估文章品質分數"""
        try:
            # 簡化的品質評估
            score = 8.0  # 基礎分數
            
            # 根據內容長度調整
            if len(content) > 1000:
                score += 0.5
            if len(content) > 2000:
                score += 0.5
                
            # 檢查是否包含案例研究
            if '案例' in content or '實例' in content:
                score += 0.5
                
            # 檢查是否包含行動步驟
            if '步驟' in content or '行動' in content:
                score += 0.5
                
            # 確保分數在合理範圍內
            return min(10.0, max(6.0, score))
            
        except Exception as e:
            logger.warning(f"品質評估失敗: {e}")
            return 8.0
    
    async def improve_article(self, article_content: str, feedback: str) -> Dict[str, Any]:
        """根據反饋改進文章"""
        try:
            improvement_prompt = f"""
            請根據以下反饋改進這篇財商文章：
            
            原文章內容：
            {article_content}
            
            改進建議：
            {feedback}
            
            請保持文章的核心訊息，但根據建議進行相應的修改和優化。
            維持專業的財富教練語調和實用的建議。
            """
            
            response = await self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4000,
                temperature=0.7,
                messages=[
                    {
                        "role": "user", 
                        "content": improvement_prompt
                    }
                ]
            )
            
            improved_content = response.content[0].text if response.content else ""
            
            if improved_content:
                return {
                    'success': True,
                    'improved_content': improved_content
                }
            else:
                return {
                    'success': False,
                    'error': '改進失敗，無法生成改進內容'
                }
                
        except Exception as e:
            logger.error(f"文章改進失敗: {str(e)}")
            return {
                'success': False,
                'error': f'改進失敗: {str(e)}'
            }
    
    async def generate_article_variations(self, base_request: Dict[str, Any], count: int = 3) -> Dict[str, Any]:
        """生成同主題的多個文章變體"""
        try:
            variations = []
            
            for i in range(count):
                # 稍微調整寫作風格和焦點
                variation_request = base_request.copy()
                
                if i == 1:
                    variation_request['writing_style'] = '哲學思辨'
                elif i == 2:
                    variation_request['writing_style'] = '歷史洞察'
                
                # 生成變體
                result = await self.generate_financial_article(variation_request)
                if result.get('success'):
                    variations.append(result['data'])
            
            return {
                'success': True,
                'variations': variations,
                'count': len(variations)
            }
            
        except Exception as e:
            logger.error(f"生成文章變體失敗: {str(e)}")
            return {
                'success': False,
                'error': f'生成變體失敗: {str(e)}'
            }
    
    def get_article_templates(self) -> List[Dict[str, Any]]:
        """獲取可用的文章模板"""
        return [
            {
                'name': '實用智慧型',
                'description': '注重實際應用和操作指南',
                'structure': ['引言', '核心概念', '實務案例', '行動步驟', '常見障礙', '總結'],
                'suitable_for': ['投資新手', '職場人士', '小企業主']
            },
            {
                'name': '哲學思辨型',
                'description': '探討財富的深層意義和人生哲學',
                'structure': ['引言', '哲學思考', '歷史智慧', '現代應用', '反思總結'],
                'suitable_for': ['高淨值人士', '思想家', '人生導師']
            },
            {
                'name': '歷史洞察型',
                'description': '從歷史事件中提取財富管理智慧',
                'structure': ['歷史背景', '事件分析', '教訓提取', '現代應用', '未來展望'],
                'suitable_for': ['歷史愛好者', '策略思考者', '長期投資者']
            },
            {
                'name': '心理分析型',
                'description': '深入分析投資心理和行為模式',
                'structure': ['心理現象', '科學解釋', '案例分析', '改進方法', '行為建議'],
                'suitable_for': ['心理學愛好者', '行為投資者', '自我提升者']
            }
        ]