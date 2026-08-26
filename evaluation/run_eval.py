import json
from app.evaluation.evaluator import SystemEvaluator

def main():
    print("=" * 60)
    print("🚀 RUNNING CROSS-PUBLICATION INSIGHT ASSISTANT BENCHMARK")
    print("=" * 60)
    
    evaluator = SystemEvaluator()
    results = evaluator.run_all()

    print("\n📊 BENCHMARK SUMMARY RESULTS:")
    print("-" * 60)
    for section, data in results.items():
        metric_name = data.get("metric", section)
        accuracy = data.get("accuracy_percentage", 0.0)
        total = data.get("total_samples", 0)
        passed = data.get("correct_predictions", 0)
        time_sec = data.get("execution_time_seconds", 0.0)
        
        print(f"• {metric_name:40} | Accuracy: {accuracy:6.2f}% ({passed}/{total}) | Time: {time_sec}s")

    print("\n" + "=" * 60)
    print("📋 DETAILED REPORT SAVED TO: evaluation_results.json")
    print("=" * 60)

    with open("evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
