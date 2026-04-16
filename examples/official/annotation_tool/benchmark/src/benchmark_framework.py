"""
Benchmark Framework Core Classes
This module contains the core classes for the barcode reader benchmark framework.
"""

import json
import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np


@dataclass
class BenchmarkResult:
    """Data class to store benchmark results."""
    library_name: str
    test_case_id: str
    success: bool
    detection_time_ms: float
    barcodes_detected: int
    barcodes_expected: int
    error_message: Optional[str] = None
    additional_metrics: Dict[str, Any] = None


@dataclass
class TestCase:
    """Data class to define a test case."""
    test_id: str
    image_path: str
    expected_barcodes: List[str]
    rotation_angle: float
    barcode_count: int
    test_type: str  # 'single', 'multiple', 'angled'
    metadata: Dict[str, Any] = None


class BarcodeReaderInterface(ABC):
    """Abstract interface for barcode reader implementations."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the barcode reader with its configuration."""
        pass
    
    @abstractmethod
    def decode_barcodes(self, image_path: str) -> Tuple[List[Dict[str, Any]], float]:
        """
        Decode barcodes from an image.
        
        Returns:
            Tuple of (list of detected barcodes, processing time in seconds)
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """Cleanup resources used by the barcode reader."""
        pass


class PerformanceMonitor:
    """Utility class to monitor performance metrics."""
    
    @staticmethod
    def measure_execution_time(func, *args, **kwargs) -> Tuple[Any, float]:
        """Measure execution time of a function."""
        start_time = time.perf_counter()
        
        try:
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            return result, end_time - start_time
        except Exception as e:
            end_time = time.perf_counter()
            raise
    
    # Accuracy scoring removed - framework now focuses on detection time and success rate only
        return 2 * (precision * recall) / (precision + recall)


class BenchmarkFramework:
    """Main benchmark framework class."""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()
        self.readers: List[BarcodeReaderInterface] = []
        self.results: List[BenchmarkResult] = []
        self.test_cases: List[TestCase] = []
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def add_reader(self, reader: BarcodeReaderInterface):
        """Add a barcode reader to the benchmark."""
        self.readers.append(reader)
    
    def add_test_case(self, test_case: TestCase):
        """Add a test case to the benchmark."""
        self.test_cases.append(test_case)
    
    def add_test_cases_from_directory(self, test_data_dir: str, pattern: str = "*.json"):
        """Add test cases from a directory of metadata JSON files."""
        from glob import glob
        import json
        
        # Find all metadata JSON files recursively
        json_paths = glob(f"{test_data_dir}/**/{pattern}", recursive=True)
        
        for json_path in json_paths:
            try:
                with open(json_path, 'r') as f:
                    metadata = json.load(f)
                
                # Create test case from metadata
                test_case = TestCase(
                    test_id=metadata.get('test_id', ''),
                    image_path=metadata.get('image_path', ''),
                    expected_barcodes=metadata.get('barcode_data', []),
                    rotation_angle=metadata.get('rotation_angle', 0.0),
                    barcode_count=metadata.get('barcode_count', 1),
                    test_type=metadata.get('test_type', 'single'),
                    metadata=metadata
                )
                self.add_test_case(test_case)
            except Exception as e:
                print(f"Error loading test case from {json_path}: {e}")
                continue
    
    def run_single_test(self, reader: BarcodeReaderInterface, test_case: TestCase) -> BenchmarkResult:
        """Run a single test case with a specific reader."""
        try:
            # Initialize reader if not already done
            if not hasattr(reader, '_initialized'):
                success = reader.initialize()
                if not success:
                    return BenchmarkResult(
                        library_name=reader.name,
                        test_case_id=test_case.test_id,
                        success=False,
                        detection_time_ms=0.0,
                        barcodes_detected=0,
                        barcodes_expected=len(test_case.expected_barcodes),
                        error_message="Failed to initialize reader"
                    )
                reader._initialized = True
            
            # Monitor performance
            start_time = time.perf_counter()
            
            # Run detection
            detected_barcodes, detection_time = reader.decode_barcodes(test_case.image_path)
            
            end_time = time.perf_counter()
            
            # Calculate metrics - success requires 100% detection (all expected barcodes found)
            # Clean barcode data: strip whitespace
            detected_texts = [barcode.get('data', '').strip() for barcode in detected_barcodes]
            expected_texts = [text.strip() for text in test_case.expected_barcodes]

            # Index-based 1-to-1 matching to correctly handle duplicate barcode values
            # (e.g. two identical ITF barcodes on the same image must match two expected entries)
            matched_detected_indices = set()
            matched_expected_indices = set()
            for i, exp in enumerate(expected_texts):
                for j, det in enumerate(detected_texts):
                    if j in matched_detected_indices:
                        continue
                    # Exact match
                    matched = (det == exp)
                    # UPC-A (12 digits) <-> EAN-13 (13 digits with leading 0)
                    if not matched and len(exp) == 12 and len(det) == 13 and det == '0' + exp:
                        matched = True
                    if not matched and len(det) == 12 and len(exp) == 13 and exp == '0' + det:
                        matched = True
                    # Detected may include appended check digit (up to 2 extra chars)
                    if not matched and det.startswith(exp) and len(det) <= len(exp) + 2:
                        matched = True
                    if matched:
                        matched_expected_indices.add(i)
                        matched_detected_indices.add(j)
                        break

            true_positives = len(matched_expected_indices)
            # Success = all expected barcodes detected (no partial success)
            success_flag = (len(expected_texts) > 0 and true_positives == len(expected_texts))
            
            result = BenchmarkResult(
                library_name=reader.name,
                test_case_id=test_case.test_id,
                success=success_flag,
                detection_time_ms=(end_time - start_time) * 1000,
                barcodes_detected=len(detected_barcodes),
                barcodes_expected=len(test_case.expected_barcodes),
                additional_metrics={
                    'detection_time_api_ms': detection_time * 1000,
                    'barcode_data': detected_barcodes,
                    'test_metadata': test_case.metadata if test_case.metadata else {}
                }
            )
            
            return result
            
        except Exception as e:
            return BenchmarkResult(
                library_name=reader.name,
                test_case_id=test_case.test_id,
                success=False,
                detection_time_ms=0.0,
                barcodes_detected=0,
                barcodes_expected=len(test_case.expected_barcodes),
                error_message=str(e)
            )
    
    def run_all_tests(self) -> List[BenchmarkResult]:
        """Run all test cases with all readers."""
        total_tests = len(self.readers) * len(self.test_cases)
        completed_tests = 0
        
        # Run tests with simple progress updates
        for reader in self.readers:
            for test_case in self.test_cases:
                result = self.run_single_test(reader, test_case)
                self.results.append(result)
                completed_tests += 1
                if completed_tests % 10 == 0 or completed_tests == total_tests:
                    print(f"Progress: {completed_tests}/{total_tests} tests completed")
        
        return self.results
    
    def save_results(self, output_dir: str = "results"):
        """Save benchmark results to files."""
        Path(output_dir).mkdir(exist_ok=True)
        
        # Save detailed results as JSON
        results_dict = [asdict(result) for result in self.results]
        with open(f"{output_dir}/detailed_results.json", 'w') as f:
            json.dump(results_dict, f, indent=2)
        
        # Save summary results as CSV
        import pandas as pd
        df = pd.DataFrame(results_dict)
        df.to_csv(f"{output_dir}/summary_results.csv", index=False)
        
        print(f"Results saved to {output_dir}/")
    
    def generate_report(self, output_path: str = "benchmark_report.html"):
        """Generate an HTML report with benchmark results."""
        # This will be implemented in a separate method
        pass
    
    def cleanup(self):
        """Cleanup all readers and resources."""
        for reader in self.readers:
            try:
                reader.cleanup()
            except Exception as e:
                print(f"Error cleaning up reader {reader.name}: {e}")