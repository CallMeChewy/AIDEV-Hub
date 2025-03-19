# File: run_tests.py
# Path: AIDEV-Hub/Tests/run_tests.py
# Standard: AIDEV-PascalCase-1.6
# Created: 2025-03-19
# Last Modified: 2025-03-19  1:00PM
# Description: Script to run all tests for the AIDEV-Hub project

import os
import sys
import unittest
import argparse
import time
from datetime import datetime

def RunTests(TestPattern=None, Verbose=False):
    """
    Run tests matching the given pattern.
    
    Args:
        TestPattern (str, optional): Pattern to match test files
        Verbose (bool, optional): Whether to show verbose output
    """
    # Find the base directory (parent of Tests)
    BaseDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Add base directory to sys.path
    sys.path.insert(0, BaseDir)
    
    # Set up test loader
    Loader = unittest.TestLoader()
    
    # Set up default pattern if none provided
    if not TestPattern:
        TestPattern = "test_*.py"
    
    # Find test directory
    TestDir = os.path.join(BaseDir, "Tests")
    
    # Discover tests
    print(f"Discovering tests in {TestDir} matching pattern '{TestPattern}'...")
    Suite = Loader.discover(TestDir, pattern=TestPattern)
    
    # Set up test runner
    if Verbose:
        Runner = unittest.TextTestRunner(verbosity=2)
    else:
        Runner = unittest.TextTestRunner(verbosity=1)
    
    # Start time
    StartTime = time.time()
    StartDateTime = datetime.now().strftime("%Y-%m-%d %I:%M:%S%p")
    
    print(f"Starting tests at {StartDateTime}\n")
    print("=" * 70)
    
    # Run tests
    Result = Runner.run(Suite)
    
    # End time
    EndTime = time.time()
    EndDateTime = datetime.now().strftime("%Y-%m-%d %I:%M:%S%p")
    ElapsedTime = EndTime - StartTime
    
    print("\n" + "=" * 70)
    print(f"Finished tests at {EndDateTime}")
    print(f"Elapsed time: {ElapsedTime:.2f} seconds")
    
    # Print summary
    print("\nTest Summary:")
    print(f"  Ran {Result.testsRun} tests")
    print(f"  Errors: {len(Result.errors)}")
    print(f"  Failures: {len(Result.failures)}")
    print(f"  Skipped: {len(Result.skipped)}")
    
    # Print failures and errors if any
    if Result.failures or Result.errors:
        print("\nFailures and errors:")
        
        for TestCase, Trace in Result.failures:
            print(f"\nFAILURE: {TestCase}")
            print("-" * 70)
            print(Trace)
        
        for TestCase, Trace in Result.errors:
            print(f"\nERROR: {TestCase}")
            print("-" * 70)
            print(Trace)
    
    # Return status code based on test results
    return 0 if Result.wasSuccessful() else 1

def GenerateTestReport(OutputFile=None):
    """
    Generate a detailed HTML test report.
    
    Args:
        OutputFile (str, optional): File to write the report to
    """
    try:
        import HtmlTestRunner
    except ImportError:
        print("HtmlTestRunner not installed. Run 'pip install html-testrunner' to enable HTML reports.")
        return 1
    
    # Find the base directory
    BaseDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Add base directory to sys.path
    sys.path.insert(0, BaseDir)
    
    # Find test directory
    TestDir = os.path.join(BaseDir, "Tests")
    
    # Set default output file
    if not OutputFile:
        ReportDir = os.path.join(BaseDir, "TestReports")
        os.makedirs(ReportDir, exist_ok=True)
        Timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        OutputFile = os.path.join(ReportDir, f"test_report_{Timestamp}.html")
    
    # Discover tests
    Loader = unittest.TestLoader()
    Suite = Loader.discover(TestDir, pattern="test_*.py")
    
    # Run tests with HTML reporter
    Runner = HtmlTestRunner.HTMLTestRunner(
        output=os.path.dirname(OutputFile),
        report_name=os.path.basename(OutputFile).rsplit('.', 1)[0],
        combine_reports=True,
        report_title="AIDEV-Hub Test Report"
    )
    
    # Start time
    StartTime = time.time()
    StartDateTime = datetime.now().strftime("%Y-%m-%d %I:%M:%S%p")
    
    print(f"Starting tests with HTML reporter at {StartDateTime}")
    print(f"Report will be written to {OutputFile}")
    
    # Run tests
    Result = Runner.run(Suite)
    
    # End time
    EndTime = time.time()
    ElapsedTime = EndTime - StartTime
    
    print(f"Finished tests. Elapsed time: {ElapsedTime:.2f} seconds")
    print(f"Report generated at {OutputFile}")
    
    # Return status code based on test results
    return 0 if Result.wasSuccessful() else 1

def main():
    """Main entry point for the script."""
    # Set up argument parser
    Parser = argparse.ArgumentParser(description="Run tests for AIDEV-Hub")
    Parser.add_argument("--pattern", "-p", help="Test file pattern to match (default: test_*.py)")
    Parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output")
    Parser.add_argument("--html", action="store_true", help="Generate HTML test report")
    Parser.add_argument("--output", "-o", help="Output file for HTML report")
    
    # Parse arguments
    Args = Parser.parse_args()
    
    # Run with appropriate options
    if Args.html:
        return GenerateTestReport(Args.output)
    else:
        return RunTests(Args.pattern, Args.verbose)

if __name__ == "__main__":
    sys.exit(main())