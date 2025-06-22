from app.agents.sub_agents import (
    ReportParserAgent,
    GuidanceRetrieverAgent,
    ComplianceEvaluatorAgent,
    SynthesisAgent,
    RadarChartAgent,
    PdfGeneratorAgent,
)
import json

class GuidanceAuditorAgent:
    """
    Supervisor agent that orchestrates the entire guidance audit workflow.
    """
    def __init__(self):
        self.parser = ReportParserAgent()
        self.retriever = GuidanceRetrieverAgent()
        self.evaluator = ComplianceEvaluatorAgent()
        self.synthesis = SynthesisAgent()
        self.chart_generator = RadarChartAgent()
        self.pdf_generator = PdfGeneratorAgent()
        print("GuidanceAuditorAgent initialized.")

    def run_audit(self, file_content: bytes, file_name: str, report_text: str) -> dict:
        """
        Executes the full audit process and returns the final result.
        """
        print("--- Starting Guidance Audit Workflow ---")
        logs = []

        # Step 1: Parse Report
        logs.append("ステップ1: レポートの解析を開始...")
        if file_content:
            report_content = self.parser.run(file_content, file_name)
        else:
            report_content = report_text
        logs.append("レポートの解析が完了しました。")
        print("Step 1 Complete.")

        # Step 2: Retrieve Guidance
        query = "TNFDフレームワークの開示推奨項目に関する包括的なガイダンス"
        logs.append(f"ステップ2: 参照ガイダンスの検索を開始...")
        retrieved_data = self.retriever.run(query)
        logs.append("参照ガイダンスの検索が完了しました。")
        print("Step 2 Complete.")

        # Step 3: Evaluate Compliance (14 items)
        logs.append("ステップ3: LLMによる14項目の評価を開始... (時間がかかります)")
        evaluation_table = self.evaluator.run(report_content, retrieved_data)
        logs.append("14項目の評価が完了しました。")
        print("Step 3 Complete.")

        # Step 4: Synthesize Results
        logs.append("ステップ4: 評価結果の集計と総括コメントの生成を開始...")
        synthesis_result = self.synthesis.run(evaluation_table)
        logs.append("集計と総括コメントの生成が完了しました。")
        print("Step 4 Complete.")

        # Step 5: Generate Radar Chart Data
        logs.append("ステップ5: レーダーチャートのデータ生成を開始...")
        radar_chart_data = self.chart_generator.run(synthesis_result["average_scores"])
        logs.append("レーダーチャートのデータ生成が完了しました。")
        print("Step 5 Complete.")

        # Step 6: Compile Final Output (without PDF first)
        final_result = {
            "process_logs": logs,
            "evaluation_table": evaluation_table,
            "synthesis": synthesis_result,
            "radar_chart_data": radar_chart_data,
            "retrieved_guidance": retrieved_data.get("context", "N/A"),
            "retrieved_citations": retrieved_data.get("citations", [])
        }

        # Step 7: Generate PDF
        logs.append("ステップ6: PDFレポートの生成を開始...")
        pdf_b64 = self.pdf_generator.run(final_result)
        final_result["pdf_b64"] = pdf_b64
        logs.append("PDFレポートの生成が完了しました。")
        print("Step 6 Complete.")
        
        print("--- Guidance Audit Workflow Finished ---")
        return final_result
