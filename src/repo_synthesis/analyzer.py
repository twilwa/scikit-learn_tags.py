"""
Repository analysis tools for code understanding and structure extraction.
"""

import ast
import os
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class FunctionInfo:
    """Information about a function or method."""
    name: str
    args: List[str]
    return_type: Optional[str]
    docstring: Optional[str]
    line_start: int
    line_end: int
    complexity: int = 0
    calls: Set[str] = field(default_factory=set)
    is_method: bool = False
    is_async: bool = False


@dataclass
class ClassInfo:
    """Information about a class."""
    name: str
    bases: List[str]
    methods: List[FunctionInfo]
    docstring: Optional[str]
    line_start: int
    line_end: int
    decorators: List[str] = field(default_factory=list)


@dataclass
class FileInfo:
    """Information about a source file."""
    path: str
    imports: Set[str]
    functions: List[FunctionInfo]
    classes: List[ClassInfo]
    variables: Dict[str, Any]
    docstring: Optional[str]
    lines_of_code: int
    complexity_score: int = 0


@dataclass
class RepositoryStructure:
    """Complete repository structure analysis."""
    root_path: str
    files: Dict[str, FileInfo]
    dependencies: Dict[str, Set[str]]
    entry_points: List[str]
    test_files: List[str]
    config_files: List[str]
    documentation_files: List[str]
    total_loc: int = 0
    languages: Set[str] = field(default_factory=set)


class CodeAnalyzer:
    """Analyzes Python code structure and dependencies."""
    
    def __init__(self):
        self.supported_extensions = {'.py', '.pyx', '.pyi'}
    
    def analyze_file(self, file_path: str) -> FileInfo:
        """Analyze a single Python file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            # Return minimal info for files with syntax errors
            return FileInfo(
                path=file_path,
                imports=set(),
                functions=[],
                classes=[],
                variables={},
                docstring=None,
                lines_of_code=len(content.splitlines()),
                complexity_score=0
            )
        
        visitor = CodeVisitor()
        visitor.visit(tree)
        
        return FileInfo(
            path=file_path,
            imports=visitor.imports,
            functions=visitor.functions,
            classes=visitor.classes,
            variables=visitor.variables,
            docstring=ast.get_docstring(tree),
            lines_of_code=len([line for line in content.splitlines() if line.strip()]),
            complexity_score=visitor.complexity_score
        )
    
    def analyze_repository(self, repo_path: str) -> RepositoryStructure:
        """Analyze entire repository structure."""
        repo_path = Path(repo_path)
        files = {}
        dependencies = {}
        entry_points = []
        test_files = []
        config_files = []
        documentation_files = []
        total_loc = 0
        languages = set()
        
        # Walk through all files
        for file_path in repo_path.rglob('*'):
            if file_path.is_file():
                relative_path = str(file_path.relative_to(repo_path))
                
                # Categorize files
                if file_path.suffix in self.supported_extensions:
                    languages.add('python')
                    file_info = self.analyze_file(str(file_path))
                    files[relative_path] = file_info
                    total_loc += file_info.lines_of_code
                    
                    # Identify entry points
                    if file_path.name == '__main__.py' or 'main' in file_path.name.lower():
                        entry_points.append(relative_path)
                    
                    # Identify test files
                    if 'test' in relative_path.lower() or file_path.name.startswith('test_'):
                        test_files.append(relative_path)
                
                elif file_path.suffix in {'.json', '.yaml', '.yml', '.toml', '.cfg', '.ini'}:
                    config_files.append(relative_path)
                
                elif file_path.suffix in {'.md', '.rst', '.txt'} or 'readme' in file_path.name.lower():
                    documentation_files.append(relative_path)
                
                elif file_path.suffix in {'.js', '.ts', '.jsx', '.tsx'}:
                    languages.add('javascript')
                elif file_path.suffix in {'.java'}:
                    languages.add('java')
                elif file_path.suffix in {'.cpp', '.c', '.h', '.hpp'}:
                    languages.add('c++')
        
        # Build dependency graph
        for relative_path, file_info in files.items():
            dependencies[relative_path] = set()
            for import_name in file_info.imports:
                # Try to resolve to local files
                for other_path, other_info in files.items():
                    if other_path != relative_path:
                        module_name = other_path.replace('/', '.').replace('.py', '')
                        if import_name.startswith(module_name):
                            dependencies[relative_path].add(other_path)
        
        return RepositoryStructure(
            root_path=str(repo_path),
            files=files,
            dependencies=dependencies,
            entry_points=entry_points,
            test_files=test_files,
            config_files=config_files,
            documentation_files=documentation_files,
            total_loc=total_loc,
            languages=languages
        )
    
    def extract_api_surface(self, repo_structure: RepositoryStructure) -> Dict[str, Any]:
        """Extract the public API surface of the repository."""
        api_surface = {
            'modules': {},
            'classes': {},
            'functions': {},
            'entry_points': repo_structure.entry_points
        }
        
        for file_path, file_info in repo_structure.files.items():
            module_name = file_path.replace('/', '.').replace('.py', '')
            
            # Public functions (not starting with _)
            public_functions = [
                f for f in file_info.functions 
                if not f.name.startswith('_')
            ]
            
            # Public classes
            public_classes = [
                c for c in file_info.classes
                if not c.name.startswith('_')
            ]
            
            if public_functions or public_classes:
                api_surface['modules'][module_name] = {
                    'functions': [f.name for f in public_functions],
                    'classes': [c.name for c in public_classes],
                    'docstring': file_info.docstring
                }
            
            # Add detailed class info
            for class_info in public_classes:
                full_name = f"{module_name}.{class_info.name}"
                api_surface['classes'][full_name] = {
                    'methods': [m.name for m in class_info.methods if not m.name.startswith('_')],
                    'docstring': class_info.docstring,
                    'bases': class_info.bases
                }
            
            # Add detailed function info
            for func_info in public_functions:
                full_name = f"{module_name}.{func_info.name}"
                api_surface['functions'][full_name] = {
                    'args': func_info.args,
                    'docstring': func_info.docstring,
                    'is_async': func_info.is_async
                }
        
        return api_surface


class CodeVisitor(ast.NodeVisitor):
    """AST visitor to extract code structure information."""
    
    def __init__(self):
        self.imports = set()
        self.functions = []
        self.classes = []
        self.variables = {}
        self.complexity_score = 0
        self.current_class = None
    
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        if node.module:
            for alias in node.names:
                full_name = f"{node.module}.{alias.name}"
                self.imports.add(full_name)
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        self._visit_function(node, is_async=False)
    
    def visit_AsyncFunctionDef(self, node):
        self._visit_function(node, is_async=True)
    
    def _visit_function(self, node, is_async=False):
        args = [arg.arg for arg in node.args.args]
        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns) if hasattr(ast, 'unparse') else str(node.returns)
        
        # Calculate function complexity (simplified)
        complexity = 1  # Base complexity
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
                complexity += 1
        
        # Extract function calls
        calls = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                calls.add(child.func.id)
        
        func_info = FunctionInfo(
            name=node.name,
            args=args,
            return_type=return_type,
            docstring=ast.get_docstring(node),
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            complexity=complexity,
            calls=calls,
            is_method=self.current_class is not None,
            is_async=is_async
        )
        
        if self.current_class:
            self.current_class.methods.append(func_info)
        else:
            self.functions.append(func_info)
        
        self.complexity_score += complexity
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            else:
                bases.append(ast.unparse(base) if hasattr(ast, 'unparse') else str(base))
        
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            else:
                decorators.append(ast.unparse(decorator) if hasattr(ast, 'unparse') else str(decorator))
        
        class_info = ClassInfo(
            name=node.name,
            bases=bases,
            methods=[],
            docstring=ast.get_docstring(node),
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            decorators=decorators
        )
        
        self.classes.append(class_info)
        
        # Visit methods within class context
        old_class = self.current_class
        self.current_class = class_info
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_Assign(self, node):
        # Extract module-level variable assignments
        if self.current_class is None:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    try:
                        if isinstance(node.value, (ast.Constant, ast.Str, ast.Num)):
                            value = node.value.value if hasattr(node.value, 'value') else node.value.s
                            self.variables[target.id] = value
                    except:
                        self.variables[target.id] = "complex_expression"
        
        self.generic_visit(node)