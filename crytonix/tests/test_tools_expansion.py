
import unittest
import sys
import os

# Add parent directory to path to import crytonix
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from crytonix.tools import (
    ProductToolbox, DesignToolbox, CodeAnalysisToolbox, 
    TestingToolbox, DatabaseToolbox, DocumentationToolbox,
    SecurityToolbox, MemoryToolbox, ScaffoldToolbox,
    # New toolboxes
    PerformanceToolbox, AIToolbox, EnvironmentToolbox,
    MonitoringToolbox, MigrationToolbox, CollaborationToolbox,
    RefactoringToolbox, FrontendToolbox, TextToolbox,
    NotificationToolbox, TimeTrackingToolbox, DependencyToolbox
)

class TestToolExpansion(unittest.TestCase):
    def test_sentiment_analysis(self):
        print("\nTesting Sentiment Analysis...")
        text = "I love this feature but I hate the bugs."
        result = ProductToolbox.analyze_sentiment(text)
        print(f"Input: {text}")
        print(f"Result: {result}")
        self.assertIn("Polarity", result)
        self.assertIn("Subjectivity", result)

    def test_rice_score(self):
        print("\nTesting RICE Score...")
        # R = 100, I = 3, C = 0.8, E = 5 -> (100 * 3 * 0.8) / 5 = 240 / 5 = 48
        result = ProductToolbox.calculate_rice_score(100, 3, 0.8, 5)
        print(f"RICE(100, 3, 0.8, 5) Result: {result}")
        self.assertIn("48.00", result)

    def test_contrast_ratio(self):
        print("\nTesting Contrast Ratio...")
        # Black and White should be 21:1
        result = DesignToolbox.check_contrast_ratio("#000000", "#FFFFFF")
        print(f"Contrast(#000000, #FFFFFF) Result: {result}")
        self.assertIn("21.00:1", result)
        self.assertIn("PASS", result)

        # Low contrast
        result_bad = DesignToolbox.check_contrast_ratio("#FFFFFF", "#FFFFCC")
        print(f"Contrast(#FFFFFF, #FFFFCC) Result: {result_bad}")
        self.assertIn("FAIL", result_bad)

    def test_find_dependencies(self):
        print("\nTesting Find Dependencies...")
        result = CodeAnalysisToolbox.find_dependencies(".")
        print(f"Dependencies: {result[:200]}...")
        self.assertIsInstance(result, str)

    def test_code_smells(self):
        print("\nTesting Code Smell Detection...")
        # Create a temp file to test
        test_file = os.path.join(os.path.dirname(__file__), "temp_test.py")
        with open(test_file, 'w') as f:
            f.write("def short_func():\n    return 1\n")
        
        result = CodeAnalysisToolbox.detect_code_smells(test_file)
        print(f"Code Smells: {result}")
        self.assertIn("No code smells", result)
        
        os.remove(test_file)

    def test_generate_test_skeleton(self):
        print("\nTesting Test Skeleton Generation...")
        result = TestingToolbox.generate_test_skeleton(__file__)
        print(f"Generated skeleton preview: {result[:200]}...")
        self.assertIn("unittest", result)

    def test_sqlite_query(self):
        print("\nTesting SQLite Query...")
        db_path = ":memory:"  # Using in-memory database
        # Note: query_sqlite expects a file path, so we test error handling
        result = DatabaseToolbox.query_sqlite("nonexistent.db", "SELECT 1")
        print(f"Query Result: {result}")
        self.assertIsInstance(result, str)

    def test_generate_readme(self):
        print("\nTesting README Generation...")
        result = DocumentationToolbox.generate_readme(".")
        print(f"README preview: {result[:200]}...")
        self.assertIn("#", result)
        self.assertIn("Installation", result)

    def test_check_secrets(self):
        print("\nTesting Secret Detection...")
        result = SecurityToolbox.check_secrets(".")
        print(f"Secret scan: {result}")
        self.assertIsInstance(result, str)

    def test_memory_snippet(self):
        print("\nTesting Memory Snippet...")
        # Save a snippet
        save_result = MemoryToolbox.save_snippet("test_snippet", "print('hello')", "test,python")
        print(f"Save result: {save_result}")
        self.assertIn("saved", save_result.lower())
        
        # Recall the snippet
        recall_result = MemoryToolbox.recall_snippet("test_snippet")
        print(f"Recall result: {recall_result}")
        self.assertIn("print('hello')", recall_result)

    def test_generate_gitignore(self):
        print("\nTesting Gitignore Generation...")
        result = ScaffoldToolbox.generate_gitignore("python")
        print(f"Gitignore preview: {result[:200]}...")
        self.assertIn("__pycache__", result)


class TestNewToolboxes(unittest.TestCase):
    """Tests for the newly added toolboxes."""
    
    def test_performance_benchmark(self):
        print("\nTesting Performance Benchmark...")
        result = PerformanceToolbox.benchmark_function("x = sum(range(100))", iterations=100)
        print(f"Benchmark result: {result}")
        self.assertIn("Average", result)
        self.assertIn("iterations", result)
    
    def test_ai_token_count(self):
        print("\nTesting AI Token Count...")
        result = AIToolbox.count_tokens("Hello world, this is a test.")
        print(f"Token count result: {result}")
        self.assertIn("token", result.lower())
    
    def test_ai_explain_code(self):
        print("\nTesting AI Explain Code...")
        code = """
def hello():
    print("Hello")

class MyClass:
    def method(self):
        pass
"""
        result = AIToolbox.explain_code(code)
        print(f"Code explanation: {result}")
        self.assertIn("hello", result.lower())
        self.assertIn("MyClass", result)
    
    def test_environment_check_vars(self):
        print("\nTesting Environment Variable Check...")
        # Set a test variable
        os.environ["TEST_VAR"] = "test_value"
        result = EnvironmentToolbox.check_env_vars(["TEST_VAR", "NONEXISTENT_VAR"])
        print(f"Env check result: {result}")
        self.assertIn("TEST_VAR", result)
        self.assertIn("✅", result)
        self.assertIn("❌", result)
    
    def test_text_summarize(self):
        print("\nTesting Text Summarization...")
        text = "This is the first sentence. Here is the second one. And finally the third. Plus a fourth. And a fifth sentence."
        result = TextToolbox.summarize_text(text, sentences=2)
        print(f"Summary: {result}")
        self.assertIsInstance(result, str)
    
    def test_text_keywords(self):
        print("\nTesting Keyword Extraction...")
        text = "Python programming is great. Python makes coding easy. Programming with Python is fun."
        result = TextToolbox.extract_keywords(text, top_n=3)
        print(f"Keywords: {result}")
        self.assertIn("python", result.lower())
    
    def test_text_stats(self):
        print("\nTesting Text Statistics...")
        text = "Hello world. This is a test. Multiple sentences here."
        result = TextToolbox.count_text_stats(text)
        print(f"Text stats: {result}")
        self.assertIn("Words", result)
        self.assertIn("Sentences", result)
    
    def test_grammar_check(self):
        print("\nTesting Grammar Check...")
        text = "This is a good sentence."
        result = TextToolbox.grammar_check(text)
        print(f"Grammar check: {result}")
        self.assertIsInstance(result, str)
    
    def test_time_tracking_todo(self):
        print("\nTesting Time Tracking Todo...")
        # Create a todo
        result = TimeTrackingToolbox.create_todo("Test task", "high")
        print(f"Create todo: {result}")
        self.assertIn("Added todo", result)
        
        # List todos
        list_result = TimeTrackingToolbox.list_todos()
        print(f"List todos: {list_result}")
        self.assertIn("Test task", list_result)
    
    def test_time_tracking_timer(self):
        print("\nTesting Time Tracking Timer...")
        # Start timer
        start_result = TimeTrackingToolbox.start_timer("Test timer task")
        print(f"Start timer: {start_result}")
        self.assertIn("Timer started", start_result)
        
        # Stop timer
        stop_result = TimeTrackingToolbox.stop_timer()
        print(f"Stop timer: {stop_result}")
        self.assertIn("Timer stopped", stop_result)
    
    def test_dependency_generate_requirements(self):
        print("\nTesting Dependency Requirements Generation...")
        result = DependencyToolbox.generate_requirements(".")
        print(f"Requirements: {result[:200]}...")
        self.assertIsInstance(result, str)
    
    def test_refactoring_find_dead_code(self):
        print("\nTesting Find Dead Code...")
        result = RefactoringToolbox.find_dead_code(".")
        print(f"Dead code result: {result[:200]}...")
        self.assertIsInstance(result, str)
    
    def test_ai_suggest_refactoring(self):
        print("\nTesting AI Suggest Refactoring...")
        # Create a temp file
        test_file = os.path.join(os.path.dirname(__file__), "temp_refactor.py")
        with open(test_file, 'w') as f:
            f.write("def short_func():\n    return 1\n")
        
        result = AIToolbox.suggest_refactoring(test_file)
        print(f"Refactoring suggestions: {result}")
        self.assertIsInstance(result, str)
        
        os.remove(test_file)
    
    def test_migration_list(self):
        print("\nTesting Migration List...")
        result = MigrationToolbox.list_migrations()
        print(f"Migrations: {result}")
        self.assertIsInstance(result, str)


if __name__ == '__main__':
    unittest.main()
