#!/usr/bin/env python3
"""
Main Benchmark Execution Script
Simplified workflow for barcode SDK benchmarking.
"""

import sys
import os
from pathlib import Path
import shutil

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.test_data_generator import TestDataGenerator
from src.benchmark_framework import BenchmarkFramework
from src.barcode_readers import create_reader
from src.performance_analysis import PerformanceAnalyzer, ReportGenerator
import json


def step1_generate_test_data(num_samples=20):
    """Step 1: Generate test data with barcodes at various angles and counts."""
    print("\n" + "="*60)
    print("STEP 1: GENERATING TEST DATA")
    print("="*60)
    
    # Clear existing test data to avoid accumulation
    test_data_path = Path("generated_dataset")
    if test_data_path.exists():
        print("\n🗑️  Clearing existing test data...")
        for subdir in ["single_barcode", "angled_barcodes", "multiple_barcodes", "challenging_conditions"]:
            subdir_path = test_data_path / subdir
            if subdir_path.exists():
                shutil.rmtree(subdir_path)
                print(f"   Cleared {subdir}/")
    
    generator = TestDataGenerator("generated_dataset")
    
    # Generate comprehensive test dataset
    print(f"\nGenerating {num_samples} test samples...")
    generator.generate_test_dataset(num_samples)
    
    print("\n✅ Test data generation completed!")
    print(f"📁 Test data saved in: generated_dataset/")
    print("   - single_barcode/     (single barcode tests)")
    print("   - angled_barcodes/    (rotated barcode tests - KEY FOCUS)")
    print("   - multiple_barcodes/  (multiple barcode tests - KEY FOCUS)")
    

def step2_run_benchmark(dataset_choice='generated'):
    """Step 2: Run benchmark with all enabled SDKs."""
    print("\n" + "="*60)
    print("STEP 2: RUNNING BENCHMARK")
    print("="*60)
    
    # Load configuration
    config_path = "config/benchmark_config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Initialize framework
    framework = BenchmarkFramework(config_path)
    
    # Set up readers
    print("\n🔧 Setting up barcode readers...")
    libraries_config = config.get('libraries', {})
    reader_count = 0
    
    for library_name, lib_config in libraries_config.items():
        if lib_config.get('enabled', False):
            try:
                reader = create_reader(library_name, lib_config)
                framework.add_reader(reader)
                print(f"   ✅ {library_name}")
                reader_count += 1
            except Exception as e:
                print(f"   ❌ {library_name}: {e}")
    
    if reader_count == 0:
        print("\n❌ No enabled readers found in configuration!")
        print("Please enable at least one reader in config/benchmark_config.json")
        return None
    
    # Load test cases
    print("\n📋 Loading test cases...")
    if dataset_choice == 'generated':
        framework.add_test_cases_from_directory("generated_dataset", "*.json")
        if len(framework.test_cases) == 0:
            print("\n❌ No test cases found in generated_dataset!")
            print("Please run Step 1 first to generate test data.")
            return None
    elif dataset_choice == 'existing':
        framework.add_test_cases_from_images("existing_dataset", "*.jpg")
        if len(framework.test_cases) == 0:
            print("\n❌ No test cases found in existing_dataset!")
            print("Please download and extract the existing dataset to existing_dataset/ folder.")
            return None
    else:  # both
        framework.add_test_cases_from_directory("generated_dataset", "*.json")
        framework.add_test_cases_from_images("existing_dataset", "*.jpg")
        if len(framework.test_cases) == 0:
            print("\n❌ No test cases found in either dataset!")
            return None
    
    print(f"   Loaded {len(framework.test_cases)} test cases")
    
    # Run benchmark
    print("\n🏃 Running benchmark tests...")
    print("This may take several minutes depending on the number of tests...")
    
    results = framework.run_all_tests()
    
    # Save results
    print("\n💾 Saving results...")
    output_dir = "results"
    framework.save_results(output_dir)
    
    print(f"\n✅ Benchmark completed!")
    print(f"   Total tests run: {len(results)}")
    print(f"   Results saved to: {output_dir}/")
    
    return results


def step3_analyze_results(results):
    """Step 3: Analyze results and generate reports."""
    print("\n" + "="*60)
    print("STEP 3: ANALYZING RESULTS & GENERATING REPORTS")
    print("="*60)
    
    if results is None or len(results) == 0:
        print("\n❌ No results to analyze!")
        return
    
    # Initialize analyzer
    analyzer = PerformanceAnalyzer(results)
    
    # Calculate statistics
    print("\n📊 Calculating statistics...")
    summary = analyzer.calculate_summary_statistics()
    angled_perf = analyzer.analyze_angled_barcode_performance()
    multiple_perf = analyzer.analyze_multiple_barcode_performance()
    existing_perf = analyzer.analyze_existing_dataset_performance()
    
    # Generate charts
    print("📈 Generating performance charts...")
    try:
        analyzer.generate_performance_charts("results/charts")
        print("   ✅ Charts saved to: results/charts/")
    except Exception as e:
        print(f"   ⚠️  Chart generation failed: {e}")
    
    # Generate HTML report
    print("📄 Generating HTML report...")
    try:
        report_gen = ReportGenerator(analyzer)
        report_path = report_gen.generate_html_report("results/benchmark_report.html")
        print(f"   ✅ Report saved to: {report_path}")
    except Exception as e:
        print(f"   ⚠️  Report generation failed: {e}")
    
    # Display summary
    print("\n" + "="*60)
    print("BENCHMARK SUMMARY")
    print("="*60)
    
    print(f"\n📊 Overall Statistics:")
    print(f"   Total tests: {summary.get('total_tests', 0)}")
    print(f"   Successful: {summary.get('successful_tests', 0)}")
    print(f"   Failed: {summary.get('failed_tests', 0)}")
    print(f"   Success rate: {summary.get('overall_success_rate', 0)*100:.1f}%")
    
    print(f"\n🔬 Libraries tested:")
    for lib in summary.get('libraries_tested', []):
        print(f"   - {lib}")
    
    # Library performance details
    print(f"\n📈 Performance by Library:")
    lib_stats = summary.get('library_statistics', {})
    for lib_name, stats in lib_stats.items():
        print(f"\n   {lib_name}:")
        print(f"      Success rate: {stats.get('success_rate', 0)*100:.1f}%")
        print(f"      Avg detection time: {stats.get('avg_detection_time_ms', 0):.2f} ms")
    
    # Key focus areas
    if angled_perf.get('best_performing_library'):
        print(f"\n🏆 Best Angled Barcode Performance:")
        print(f"   {angled_perf['best_performing_library']}")
        best_lib = angled_perf['best_performing_library']
        perf = angled_perf['libraries_performance'][best_lib]
        print(f"   Success rate: {perf.get('success_rate', 0)*100:.1f}%")
        print(f"   Avg detection time: {perf.get('avg_detection_time_ms', 0):.2f} ms")
    
    if multiple_perf.get('best_performing_library'):
        print(f"\n🏆 Best Multiple Barcode Performance:")
        print(f"   {multiple_perf['best_performing_library']}")
        best_lib = multiple_perf['best_performing_library']
        perf = multiple_perf['libraries_performance'][best_lib]
        print(f"   Success rate: {perf.get('success_rate', 0)*100:.1f}%")
        print(f"   Avg barcodes detected: {perf.get('avg_barcodes_detected', 0):.1f}")
    
    if existing_perf.get('best_performing_library'):
        print(f"\n🏆 Best Existing Dataset Performance (Real-world Images):")
        print(f"   {existing_perf['best_performing_library']}")
        best_lib = existing_perf['best_performing_library']
        perf = existing_perf['libraries_performance'][best_lib]
        print(f"   Success rate: {perf.get('success_rate', 0)*100:.1f}%")
        print(f"   Avg detection time: {perf.get('avg_detection_time_ms', 0):.2f} ms")
        print(f"   Total tested: {existing_perf.get('total_existing_tests', 0)} images")
    
    print("\n✅ Analysis complete!")


def main():
    """Main execution function."""
    print("\n" + "="*60)
    print("BARCODE SDK BENCHMARK")
    print("Comparing: ZXing-Cpp, PyZBar, Dynamsoft*")
    print("(*Commercial SDKs - configure license keys to enable)")
    print("="*60)
    
    print("\nThis benchmark will:")
    print("1. Select dataset (generated/existing/both)")
    print("2. Generate test data if needed (for generated dataset)")
    print("3. Run benchmark tests with enabled SDKs")
    print("4. Analyze results and generate reports")
    
    # Check available datasets
    generated_path = Path("generated_dataset")
    existing_path = Path("existing_dataset")
    
    has_generated = False
    has_existing = False
    
    if generated_path.exists():
        json_files = list(generated_path.rglob("*.json"))
        has_generated = len(json_files) > 0
    
    if existing_path.exists():
        jpg_files = list(existing_path.glob("*.jpg")) + list(existing_path.glob("*.png"))
        has_existing = len(jpg_files) > 0
    
    print("\n📁 Available datasets:")
    print(f"   Generated dataset: {'✅ Found' if has_generated else '❌ Not found'}")
    if has_generated:
        print(f"      ({len(list(generated_path.rglob('*.json')))} test cases)")
    print(f"   Existing dataset:  {'✅ Found' if has_existing else '❌ Not found'}")
    if has_existing:
        print(f"      ({len(list(existing_path.glob('*.jpg')) + list(existing_path.glob('*.png')))} images)")
    
    # Dataset selection
    print("\n🔍 Select dataset to benchmark:")
    print("   1. Generated dataset (auto-generated test cases)")
    print("   2. Existing dataset (real-world barcode images)")
    print("   3. Both datasets")
    
    dataset_choice = input("\nYour choice (1/2/3, default 1): ").strip()
    if dataset_choice == '2':
        dataset_type = 'existing'
    elif dataset_choice == '3':
        dataset_type = 'both'
    else:
        dataset_type = 'generated'
    
    # Check if test data exists
    test_data_path = Path("generated_dataset")
    has_test_data = False
    if test_data_path.exists():
        # Check for JSON metadata files
        json_files = list(test_data_path.rglob("*.json"))
        has_test_data = len(json_files) > 0
    
    # Handle generated dataset generation if needed
    if dataset_type in ['generated', 'both']:
        if not has_test_data:
            print("\n⚠️  No generated test data found. Will generate test data first.")
            choice = input("\nPress Enter to continue or 'q' to quit: ").strip().lower()
            if choice == 'q':
                print("Exiting...")
                return
        else:
            regenerate = input("\nRegenerate test data? (y/N): ").strip().lower()
            if regenerate == 'y':
                has_test_data = False
    
    try:
        # Step 1: Generate test data (if needed)
        if not has_test_data:
            num_samples = input("\nNumber of test samples to generate (default 20): ").strip()
            num_samples = int(num_samples) if num_samples.isdigit() else 20
            step1_generate_test_data(num_samples)
        
        # Step 2: Run benchmark
        print("\n" + "-"*60)
        input("Press Enter to run benchmark (or Ctrl+C to exit)...")
        results = step2_run_benchmark(dataset_type)
        
        if results is None:
            print("\n❌ Benchmark failed. Please check the errors above.")
            return
        
        # Step 3: Analyze results
        print("\n" + "-"*60)
        input("Press Enter to analyze results (or Ctrl+C to exit)...")
        step3_analyze_results(results)
        
        print("\n" + "="*60)
        print("🎉 BENCHMARK COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\n📁 Results are available in:")
        print("   - results/detailed_results.json  (raw data)")
        print("   - results/summary_results.csv    (summary table)")
        print("   - results/benchmark_report.html  (full report)")
        print("   - results/charts/                (performance charts)")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Benchmark interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
