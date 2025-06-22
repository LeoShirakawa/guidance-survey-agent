from app.tools.search_tool import search_discovery_engine
from vertexai.generative_models import GenerativeModel
import json
from io import BytesIO
import base64
import re
import os
import pandas as pd
import docx
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

# --- Configuration ---
EVALUATOR_MODEL_NAME = "gemini-2.5-pro"

def clean_markdown(text):
    """Removes common markdown formatting."""
    text = re.sub(r'###\s?', '', text)
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'\*', '', text)
    text = re.sub(r'📈|📉|🎯', '', text) # Remove emojis
    return text.strip()

class ReportParserAgent:
    """
    Agent responsible for parsing the user-uploaded report.
    """
    def run(self, file_content: bytes, file_name: str) -> str:
        print(f"Running Report Parser Agent for file: {file_name}")
        _, extension = os.path.splitext(file_name)
        text = ""
        try:
            if extension == '.pdf':
                reader = PdfReader(BytesIO(file_content))
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            elif extension == '.docx':
                doc = docx.Document(BytesIO(file_content))
                for para in doc.paragraphs:
                    text += para.text + "\n"
            elif extension == '.xlsx':
                df = pd.read_excel(BytesIO(file_content))
                text = df.to_string()
            elif extension == '.csv':
                text = pd.read_csv(BytesIO(file_content)).to_string()
            elif extension == '.txt':
                text = file_content.decode('utf-8')
            else:
                return f"サポートされていないファイル形式です: {extension}"
            return text
        except Exception as e:
            print(f"Error parsing file {file_name}: {e}")
            return f"ファイルの解析中にエラーが発生しました: {e}"


class GuidanceRetrieverAgent:
    """
    Agent responsible for retrieving relevant guidance from Discovery Engine.
    """
    def run(self, query: str) -> dict:
        print(f"Running Guidance Retriever Agent with query: {query}")
        return search_discovery_engine(query)


class ComplianceEvaluatorAgent:
    """
    Agent responsible for evaluating the report against the retrieved guidance.
    """
    def __init__(self):
        self.model = GenerativeModel(EVALUATOR_MODEL_NAME)

    def run(self, report_text: str, retrieved_data: dict) -> list:
        """
        Compares the report against the guidance and generates a structured evaluation table.
        """
        print("Running Compliance Evaluator Agent...")
        guidance_context = retrieved_data.get("context", "ガイダンスが見つかりませんでした。")
        citations = retrieved_data.get("citations", [])
        citation_text = "\n".join([f"- {c.get('title', 'N/A')} (Page: {c.get('page_number', 'N/A')}, URI: {c.get('uri', 'N/A')})" for c in citations])
        if not citation_text:
            citation_text = "なし"

        evaluation_prompt = f"""
        あなたは、企業のサステナビリティレポートをTNFDフレームワークに基づき評価する、世界トップクラスの専門アナリストです。
        以下の「評価対象レポート」を、「参照ガイダンス」および「参照元ドキュメント」と徹底的に比較分析し、TNFDが要求する「14の開示推奨項目」のそれぞれについて、評価結果をJSON形式で出力してください。

        **参照ガイダンス (Vertex AI Searchによる検索結果):**
        ---
        {guidance_context}
        ---
        **参照元ドキュメント:**
        ---
        {citation_text}
        ---
        **評価対象レポート:**
        ---
        {report_text}
        ---

        **評価と出力の要件:**
        以下の14項目すべてについて、評価を生成してください。
        1.  **ガバナンス - A. 取締役会の監督**: 自然関連課題に関する取締役会の監督体制
        2.  **ガバナンス - B. 経営者の役割**: 経営者の役割と報告体制
        3.  **ガバナンス - C. 人権方針とステークホルダー・エンゲージメント**: 人権方針とエンゲージメント活動
        4.  **戦略 - A. 短期・中期・長期の自然関連課題**: 期間ごとのリスクと機会
        5.  **戦略 - B. ビジネスモデル等へのインパクト**: ビジネスモデル、バリューチェーン、戦略、財務計画への影響
        6.  **戦略 - C. 戦略のレジリエンス**: シナリオ分析を考慮した戦略の強靭性
        7.  **戦略 - D. 優先地域**: 優先地域における資産や活動の場所
        8.  **リスクとインパクトの管理 - A(i). 直接操業におけるプロセス**: 直接操業における特定・評価・優先順位付けのプロセス
        9.  **リスクとインパクトの管理 - A(ii). バリューチェーンにおけるプロセス**: バリューチェーンにおける特定・評価・優先順位付けのプロセス
        10. **リスクとインパクトの管理 - B. 管理するためのプロセス**: リスクと機会を管理するプロセス
        11. **リスクとインパクトの管理 - C. 全体リスク管理への統合**: 全社的リスク管理への統合
        12. **測定指標とターゲット - A. リスクと機会を評価・管理するための測定指標**: リスクと機会に関する測定指標
        13. **測定指標とターゲット - B. 依存とインパクトを評価・管理するための測定指標**: 依存とインパクトに関する測定指標
        14. **測定指標とターゲット - C. ターゲットと目標、および実績**: 設定した目標と実績

        **出力形式**:
        必ず以下のJSON形式のリストで出力してください。他のテキストは一切含めないでください。
        各項目の`reference`フィールドには、**「参照元ドキュメント」リストの中から、その評価の根拠として最も関連性の高いものを1つだけ選び、そのタイトルとページ番号を記述してください。**
        ```json
        [
          {{
            "classification": "ガバナンス",
            "item": "A. 取締役会の監督",
            "score": "4.2/5.0",
            "good_point": "優れている点を具体的に記述",
            "improvement_point": "不足している点や改善点を具体的に指摘",
            "reference": "タイトル (Page: ページ番号)"
          }}
        ]
        ```
        """
        try:
            response = self.model.generate_content(contents=[evaluation_prompt])
            json_text = response.text.strip().replace("```json", "").replace("```", "")
            evaluation_list = json.loads(json_text)
            # Clean markdown from generated text
            for item in evaluation_list:
                item["good_point"] = clean_markdown(item.get("good_point", ""))
                item["improvement_point"] = clean_markdown(item.get("improvement_point", ""))
            return evaluation_list
        except Exception as e:
            print(f"Error during compliance evaluation: {e}")
            return [{"classification": "エラー", "item": "評価エラー", "score": "0/5.0", "good_point": "N/A", "improvement_point": f"LLMによる評価中にエラーが発生しました: {e}", "reference": "N/A"}]

class SynthesisAgent:
    """
    Agent that synthesizes the evaluation results, calculates average scores, and provides a summary.
    """
    def __init__(self):
        self.model = GenerativeModel(EVALUATOR_MODEL_NAME)

    def run(self, evaluation_table: list) -> dict:
        print("Running Synthesis Agent...")
        scores = {}
        total_score = 0
        total_count = 0
        for row in evaluation_table:
            classification = row.get("classification")
            try:
                score_str = str(row.get("score", "0/5.0")).split('/')[0]
                score = float(score_str)
                if classification not in scores:
                    scores[classification] = []
                scores[classification].append(score)
                total_score += score
                total_count += 1
            except (ValueError, IndexError):
                continue

        avg_scores = {cls: sum(s) / len(s) for cls, s in scores.items() if s}
        overall_avg = total_score / total_count if total_count > 0 else 0
        
        summary_prompt = f"""
        あなたは評価結果をインフォグラフィックにまとめるデザイナーです。
        以下の評価結果の平均点と内容を基に、レポート全体の総括コメントを生成してください。

        **総合平均点:** {overall_avg:.2f} / 5.0
        **分類別平均スコア:**
        {json.dumps(avg_scores, indent=2, ensure_ascii=False)}

        **タスク:**
        レポート全体の強みと弱みを、絵文字を使って視覚的に分かりやすく、詳細に分析してください。
        その上で、今後の改善に向けた具体的なアクションプランを3つ提言してください。
        アウトプットは以下の形式に従ってください。

        ---
        ### 総合評価: {overall_avg:.2f} / 5.0

        ### 📈 **総合的な強み (Strength)**
        [ここにレポート全体で優れている点を詳細に記述]

        ### 📉 **今後の課題 (Weakness)**
        [ここにレポート全体で改善が必要な点を詳細に記述]

        ### 🎯 **推奨アクションプラン (Action Plan)**
        1.  **[アクション1のタイトル]**: [アクション1の具体的な内容]
        2.  **[アクション2のタイトル]**: [アクション2の具体的な内容]
        3.  **[アクション3のタイトル]**: [アクション3の具体的な内容]
        ---
        """
        try:
            response = self.model.generate_content(contents=[summary_prompt])
            summary_text = clean_markdown(response.text)
        except Exception as e:
            print(f"Error during summary generation: {e}")
            summary_text = f"総括コメントの生成中にエラーが発生しました: {e}"

        return {
            "average_scores": avg_scores,
            "summary_comment": summary_text
        }

class RadarChartAgent:
    """
    Agent that generates data for a radar chart.
    """
    def run(self, average_scores: dict) -> dict:
        print("Running Radar Chart Agent...")
        return {
            "labels": list(average_scores.keys()),
            "data": list(average_scores.values())
        }

class PdfGeneratorAgent:
    """
    Agent that generates a PDF report from the evaluation results.
    """
    def run(self, final_result: dict) -> str:
        print("Running PDF Generator Agent...")
        try:
            buffer = BytesIO()
            
            # Register Japanese font
            pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
            
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='Japanese', fontName='HeiseiMin-W3', fontSize=10, leading=14))
            styles.add(ParagraphStyle(name='Japanese-h1', parent=styles['h1'], fontName='HeiseiMin-W3'))
            styles.add(ParagraphStyle(name='Japanese-h2', parent=styles['h2'], fontName='HeiseiMin-W3'))

            story = []
            
            story.append(Paragraph("TNFDレポート評価結果", styles['Japanese-h1']))
            story.append(Spacer(1, 12))

            # Summary
            story.append(Paragraph("総合評価", styles['Japanese-h2']))
            summary_text = final_result.get("synthesis", {}).get("summary_comment", "N/A")
            story.append(Paragraph(summary_text.replace("\n", "<br/>"), styles['Japanese']))
            story.append(Spacer(1, 24))

            # Evaluation Table
            story.append(Paragraph("詳細評価", styles['Japanese-h2']))
            table_data = [['項目', '評価', '良い点', '改善点', '参考文献']]
            for row in final_result.get("evaluation_table", []):
                table_data.append([
                    Paragraph(row.get("item", ""), styles['Japanese']),
                    Paragraph(str(row.get("score", "")), styles['Japanese']),
                    Paragraph(row.get("good_point", ""), styles['Japanese']),
                    Paragraph(row.get("improvement_point", ""), styles['Japanese']),
                    Paragraph(row.get("reference", ""), styles['Japanese']),
                ])
            
            table = Table(table_data, colWidths=[60, 40, 120, 120, 120])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), 'HeiseiMin-W3'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0,0), (-1,-1), 1, colors.black)
            ]))
            story.append(table)
            
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            doc.build(story)
            
            pdf_bytes = buffer.getvalue()
            buffer.close()
            return base64.b64encode(pdf_bytes).decode('utf-8')

        except Exception as e:
            print(f"Error generating PDF: {e}")
            return ""
