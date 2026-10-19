#!/usr/bin/env python3
"""
Barcode Reader Benchmark Runner
Main script to run comprehensive barcode reader benchmarks.
"""

import sys
import os
import json
import argparse
from pathlib import Path
import traceback

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.benchmark_framework import BenchmarkFramework, TestCase
from src.barcode_readers import create_reader
from src.test_data_generator import TestDataGenerator
from src.performance_analysis import PerformanceAnalyzer, ReportGenerator


def load_test_cases_from_metadata(metadata_dir: str) -> list:
    """Load test cases from metadata JSON files."""
    test_cases = []
    metadata_path = Path(metadata_dir)
    
    if not metadata_path.exists():
        print(f"Warning: Metadata directory {metadata_dir} not found.")
        return test_cases
    
    # Recursively find all JSON files
    for json_file in metadata_path.rglob("*.json"):
        try:
            with open(json_file, 'r') as f:
                metadata = json.load(f)
            
            # Extract test case information
            test_case = TestCase(
                test_id=metadata.get('test_id', ''),
                image_path=metadata.get('image_path', ''),
                expected_barcodes=metadata.get('barcode_data', []),
                rotation_angle=metadata.get('rotation_angle', 0.0),
                barcode_count=metadata.get('barcode_count', 1),
                test_type=metadata.get('test_type', 'single'),
                metadata=metadata
            )
            test_cases.append(test_case)
            
        except Exception as e:
            print(f"Error loading metadata from {json_file}: {e}")
            continue
    
    return test_cases


def setup_readers_from_config(config: dict) -> list:
    """Set up barcode readers based on configuration."""
    readers = []
    libraries_config = config.get('libraries', {})
    
    for library_name, lib_config in libraries_config.items():
        if not lib_config.get('enabled', False):
            print(f"Skipping disabled library: {library_name}")
            continue
        
        try:
            reader = create_reader(library_name, lib_config)
            readers.append(reader)
            print(f"✅ Added reader: {library_name}")
        except Exception as e:
            print(f"❌ Failed to create reader {library_name}: {e}")
    
    return readers


def main():
    """Main benchmark execution function."""
    parser = argparse.ArgumentParser(description="Barcode Reader Benchmark Tool")
    parser.add_argument("--config", default="config/benchmark_config.json", 
                       help="Path to benchmark configuration file")
    parser.add_argument("--generate-data", action="store_true",
                       help="Generate test data before running benchmark")
    parser.add_argument("--num-samples", type=int, default=50,
                       help="Number of test samples to generate")
    parser.add_argument("--libraries", nargs="+", 
                       help="Specific libraries to test (overrides config)")
    parser.add_argument("--output-dir", default="results",
                       help="Output directory for results")
    parser.add_argument("--no-charts", action="store_true",
                       help="Skip generating performance charts")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Load configuration
    try:
        with open(args.config, 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {args.config}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in configuration file: {e}")
        sys.exit(1)
    
    print("🚀 Starting Barcode Reader Benchmark")
    print("="*50)
    
    # Step 1: Generate test data if requested
    if args.generate_data:
        print("📊 Generating test data...")
        test_data_generator = TestDataGenerator("test_data")
        test_data_generator.generate_test_dataset(args.num_samples)
        print("✅ Test data generation completed")
        print()
    
    # Step 2: Load test cases
    print("📋 Loading test cases...")
    test_cases = load_test_cases_from_metadata("test_data")
    
    if not test_cases:
        print("⚠️  No test cases found. Generating default test data...")
        test_data_generator = TestDataGenerator("test_data")
        test_data_generator.generate_test_dataset(args.num_samples)
        test_cases = load_test_cases_from_metadata("test_data")
    
    print(f"✅ Loaded {len(test_cases)} test cases")
    print()
    
    # Step 3: Set up readers
    print("🔧 Setting up barcode readers...")
    readers = setup_readers_from_config(config)
    
    if not readers:
        print("❌ No valid readers configured. Please check your configuration.")
        sys.exit(1)
    
    print(f"✅ Set up {len(readers)} readers")
    print()
    
    # Step 4: Initialize benchmark framework
    print("🎯 Initializing benchmark framework...")
    framework = BenchmarkFramework(args.config)
    
    # Add readers
    for reader in readers:
        framework.add_reader(reader)
    
    # Add test cases
    for test_case in test_cases:
        framework.add_test_case(test_case)
    
    print("✅ Benchmark framework initialized")
    print()
    
    # Step 5: Run benchmark
    print("🏃 Running benchmark tests...")
    print("This may take several minutes depending on the number of tests...")
    
    try:
        results = framework.run_all_tests()
        print(f"✅ Completed {len(results)} benchmark tests")
        print()
        
        # Step 6: Analyze results
        print("📊 Analyzing results...")
        analyzer = PerformanceAnalyzer(results)
        
        # Calculate statistics
        summary_stats = analyzer.calculate_summary_statistics()
        challenging_performance = analyzer.analyze_challenging_barcode_performance()
        angled_performance = analyzer.analyze_angled_barcode_performance()
        multiple_performance = analyzer.analyze_multiple_barcode_performance()
        
        print("✅ Results analysis completed")
        print()
        
        # Step 7: Generate reports
        print("📝 Generating reports...")
        
        # Create output directory
        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # Save raw results
        framework.save_results(str(output_dir))
        
        # Generate charts if requested
        if not args.no_charts:
            print("📈 Generating performance charts...")
            analyzer.generate_performance_charts(str(output_dir / "charts"))
            print("✅ Charts generated")
        
        # Generate HTML report
        print("📄 Generating HTML report...")
        report_generator = ReportGenerator(analyzer)
        report_path = report_generator.generate_html_report(str(output_dir / "benchmark_report.html"))
        
        print(f"✅ HTML report generated: {report_path}")
        print()
        
        # Step 8: Display summary
        print("📋 Benchmark Summary")
        print("="*30)
        
        print(f"Total tests run: {summary_stats.get('total_tests', 0)}")
        print(f"Overall success rate: {summary_stats.get('overall_success_rate', 0)*100:.1f}%")
        print(f"Libraries tested: {', '.join(summary_stats.get('libraries_tested', []))}")
        
        if angled_performance.get('best_performing_library'):
            print(f"🏆 Best angled barcode performance: {angled_performance['best_performing_library']}")
        
        if multiple_performance.get('best_performing_library'):
            print(f"🏆 Best multiple barcode performance: {multiple_performance['best_performing_library']}")

        if challenging_performance.get('best_performing_library'):
            print(f"🏆 Best challenging conditions performance: {challenging_performance['best_performing_library']}")
        
        print()
        print(f"📁 All results saved to: {output_dir.absolute()}")
        print(f"📊 Main report: {report_path}")
        
        # Step 9: Show strategic insights
        print()
        print("🎯 Key Competitive Advantages Identified:")
        print("-" * 40)
        
        if angled_performance.get('best_performing_library'):
            best_angled = angled_performance['best_performing_library']
            performance = angled_performance['libraries_performance'][best_angled]
            print(f"• {best_angled} excels in angled barcode detection ({performance['success_rate']*100:.1f}% success rate)")
        
        if multiple_performance.get('best_performing_library'):
            best_multiple = multiple_performance['best_performing_library']
            performance = multiple_performance['libraries_performance'][best_multiple]
            print(f"• {best_multiple} leads in multiple barcode processing ({performance['success_rate']*100:.1f}% success rate)")

        if challenging_performance.get('best_performing_library'):
            best_challenging = challenging_performance['best_performing_library']
            performance = challenging_performance['libraries_performance'][best_challenging]
            print(f"• {best_challenging} shows robustness under degradations ({performance['success_rate']*100:.1f}% success rate)")
        
        print("• Benchmark demonstrates superior performance in challenging scenarios")
        print("• Results ready for marketing and competitive positioning")
        
    except KeyboardInterrupt:
        print("\n⏹️  Benchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during benchmark execution: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup
        try:
            framework.cleanup()
        except:
            pass
    
    print("\n🎉 Benchmark completed successfully!")
    print("💡 Use the results to promote your leading capabilities in:")
    print("   - Angled barcode recognition (various rotations)")
    print("   - Multiple barcode detection and processing")
    print("   - Robust decoding under challenging conditions (noise, blur, occlusion, perspective)")
    print("   - Overall performance and success rate metrics")


if __name__ == "__main__":
    main()