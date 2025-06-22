from google.cloud import discoveryengine_v1alpha as discoveryengine
import os

# --- Configuration ---
PROJECT_ID = "tactile-octagon-372414"
LOCATION = "global"
ENGINE_ID = "tnfd-pdfs-urls_1750581252080" 
SERVING_CONFIG_ID = "default_search"

def search_discovery_engine(query: str) -> dict:
    """
    Searches for documents in Vertex AI Search (Discovery Engine) and returns
    a dictionary containing the summary and citation metadata.
    """
    client = discoveryengine.SearchServiceClient()

    serving_config = (
        f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/"
        f"engines/{ENGINE_ID}/servingConfigs/{SERVING_CONFIG_ID}"
    )

    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=query,
        page_size=5,
        content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
            summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                summary_result_count=3,
                include_citations=True, 
            )
        ),
    )

    try:
        response = client.search(request)
        
        summary_text = response.summary.summary_text if response.summary else "関連する情報の要約は生成されませんでした。"
        
        citations = []
        for result in response.results:
            # derived_struct_data is where extracted metadata for unstructured data (like PDFs) is stored.
            doc_data = result.document.derived_struct_data
            title = doc_data.get('title', 'タイトル不明')
            link = doc_data.get('link', result.document.name) # Fallback to resource name
            
            # Try to get page number from extractive answers if available
            page_number = "N/A"
            if "extractive_answers" in doc_data and doc_data["extractive_answers"]:
                page_number = doc_data["extractive_answers"][0].get("pageNumber", "N/A")

            citations.append({
                "uri": link,
                "title": title,
                "page_number": page_number
            })

        return {
            "context": summary_text,
            "citations": citations
        }

    except Exception as e:
        print(f"An error occurred during Discovery Engine Search: {e}")
        return {
            "context": f"検索中にエラーが発生しました: {e}",
            "citations": []
        }

# Example usage for testing
if __name__ == "__main__":
    test_query = "TNFDのガバナンスに関する開示要求項目を教えて"
    print("--- Running Discovery Engine Search Tool ---")
    results = search_discovery_engine(test_query)
    import json
    print(json.dumps(results, indent=2, ensure_ascii=False))
